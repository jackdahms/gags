import datetime
import math
import os.path
import random
import re
import requests

from bs4 import BeautifulSoup

LIBRARY = 'static/artists/'
MANIFEST = 'static/manifest.csv'
INDEX = 'songs.tsv' # use .tsv so we can allow songs with commas
DELIMITER = '\t' # delimiter for index
V = lambda *args: None # Verbose printing function. Does nothing by default

class Song():

    def __init__(self, title, song_id, url):
        self.title = title
        self.id = song_id
        self.url = url

    def __len__(self):
        '''
        Returns number of lines in song.
        '''
        return len(self.text.split('\n'))

    def load(self, location):
        with open(location + str(self.id)) as f:
            self.set_text(''.join(f.readlines()))

    def save(self, location):
        with open(location + str(self.id), 'w') as f:
            f.write(self.raw_text)

    def set_text(self, raw_text):
        self.raw_text = raw_text

        # get rid of section labels
        text = re.sub(r'\[.+\]', '', self.raw_text)
        # get rid of some of the empty lines and leading/trailing whitespace
        text = re.sub(r'\n\n\n', '\n\n', text).strip()
        self.text = text
        
    def scrape(self):
        page = requests.get(self.url)
        html = BeautifulSoup(page.text, 'html.parser')
        self.set_text(html.find('div', class_='lyrics').get_text())

def build_chain(songs, n=2):
    # Build markov chain
    chain = {}
    V('Building lyric model...')

    for i, song in enumerate(songs):
        # V('Calculating %d/%d' % (i, len(self.songs)))

        lyrics = song.text

        # split song into words
        words = []
        word = ''
        for c in lyrics:
            if c == '\n':
                words.append(word)
                words.append('\n')
                word = ''
            elif c == ' ':
                words.append(word)
                word = ''
            else:
                word += c

        #build markov chains
        for i in range(1, len(words) - 2):
            key = (words[i - 1], words[i])
            if key in chain:
                chain[key].append(words[i + 1])
            else:
                chain[key] = [words[i + 1]]
    return chain

def song_count(artist_id, token):
    '''
    Returns number of songs
    '''   
    headers = 'title%sid%surl\n' % (2 * (DELIMITER,))

    # Make sure our paths are valid
    if not os.path.exists(LIBRARY):
        os.mkdir(LIBRARY)
    if not os.path.exists(LIBRARY + artist_id):
        os.mkdir(LIBRARY + artist_id)
    if not os.path.exists(LIBRARY + artist_id + '/' + INDEX):
        # use .tsv not .csv so songs with commas in the name don't mess up
        with open(LIBRARY + artist_id + '/' + INDEX, 'w') as f:
            f.write(headers)

    # Load existing song names
    count = 0
    with open(LIBRARY + artist_id + '/' + INDEX) as f:
        rows = [r.strip().split(DELIMITER) for r in f.readlines()[1:]]
        counnt = len(rows)

    if count == 0:
        # We probably just created the list. Let's check Genius.
        per_page = 50 # songs per request
        next_page = 1 # page of results indexed from 1
        url = 'http://api.genius.com/artists/%s/songs' % artist_id
        headers = {'Authorization': 'Bearer ' + token}
        while next_page != None:
            params = {'per_page': per_page, 'page': next_page}
            json = requests.get(url, params=params, headers=headers).json()
            for song in json['response']['songs']:
                count += 1
            next_page = json['response']['next_page']

    return count

def generate_song(chain, line_count=21):
    # Generate a new song
    # start with a capital letter
    pair = ('a')
    while not pair[0][0].isupper():
        pair = random.choice(list(chain.keys()))
    # generate song
    count = 0
    song = pair[0] + ' '
    while count < line_count:
        song += pair[1] + ' '
        if pair[1] == '\n':
            count += 1
            if count != line_count:
                song += '' # '\b'
        try:
            next_word = random.choice(chain[pair])
        except:
            count += 1
        pair = (pair[1], next_word)

    # Removes any blank lines from the beginning/end
    song = song.strip()

    return song

def load_songs(artist_id, token):
    '''
    Returns generator of loaded songs.
    '''   
    header_row = 'title%sid%surl\n' % (2 * (DELIMITER,))
    location = LIBRARY + artist_id + '/songs/'

    # Make sure our paths are valid
    if not os.path.exists(LIBRARY):
        os.mkdir(LIBRARY)
    if not os.path.exists(LIBRARY + artist_id):
        os.mkdir(LIBRARY + artist_id)
    if not os.path.exists(location):
        os.mkdir(location)
    if not os.path.exists(LIBRARY + artist_id + '/' + INDEX):
        # use .tsv not .csv so songs with commas in the name don't mess up
        with open(LIBRARY + artist_id + '/' + INDEX, 'w') as f:
            f.write(header_row)

    # Load existing song names
    songs = []
    with open(LIBRARY + artist_id + '/' + INDEX) as f:
        rows = [r.strip().split(DELIMITER) for r in f.readlines()[1:]]
        for row in rows:
            songs.append(Song(row[0], row[1], row[2]))

    if len(songs) == 0:
        # We probably just created the list. Let's check Genius.
        per_page = 50 # songs per request
        next_page = 1 # page of results indexed from 1
        url = 'http://api.genius.com/artists/%s/songs' % artist_id
        headers = {'Authorization': 'Bearer ' + token}
        while next_page != None:
            params = {'per_page': per_page, 'page': next_page}
            json = requests.get(url, params=params, headers=headers).json()
            for song in json['response']['songs']:
                s = Song(song['title'], song['id'], song['url'])
                songs.append(s)
            next_page = json['response']['next_page']

    # Hopefully we have more songs now. Let's save them back to the list.
    with open(LIBRARY + artist_id + '/' + INDEX, 'w') as f:
        f.write(header_row)
        for song in songs:
            f.write('%s\t%s\t%s\n' % (song.title, song.id, song.url))

    # Try and load all the lyrics from files. If they don't exist, scrape 'em.
    for song in songs:
        try:
            song.load(location)
        except:
            song.scrape()
            song.save(location)
        yield song

def load_artist_id(name):
    '''
    Checks manifest and Genius for an ID that corresponds to name.
    Raises an exception if one can't be found.
    '''
    name = name.replace(' ', '-').lower()
    artist_id = None

    # Check manifest
    V('Checking manifest for id...')
    if os.path.exists(MANIFEST):
        with open(MANIFEST) as f:
            rows = [row.strip().split(',') for row in f.readlines()[1:]]
            for row in rows:
                if name == row[0]:
                    V('Found!')
                    artist_id = row[1]

    # if we didn't find it, get it from Genius
    if artist_id is None:
        V('Not found. Checking Genius...')
        url = 'https://www.genius.com/artists/' + name
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            artist_id = re.search(r'(?<=content="\/artists\/)\d+(?=")', response.text).group(0)
        else:
            raise Exception('Artist not found! (HTTP Code %d)' % response.status_code)

    return artist_id

def load_token(filename='token'):
    return open(filename).read()

def set_verbose(verbose):
    if verbose:
        global V
        def verbose_print(*args):
            print(*args)
        V = verbose_print

def add_to_manifest(name, artist_id):
    if not os.path.exists(MANIFEST):
        with open(MANIFEST, 'w') as f:
            f.write('name,id,updated\n')

    with open(MANIFEST) as f:
        manifest = [r.strip().split(',') for r in f.readlines()]

    # Does this artist already exist?
    found = artist_id in [r[1] for r in manifest[1:]]
    # If not, add him
    if not found:
        now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        manifest.append([name, artist_id, now])

    with open(MANIFEST, 'w') as f:
        for row in manifest:
            f.write('%s,%s,%s\n' % (row[0], row[1], row[2]))

if __name__ == '__main__':
    set_verbose(True)
    token = load_token()
    artist_name = input('Artist name? ').replace(' ', '-').lower()
    artist_id = load_artist_id(artist_name)
    add_to_manifest(artist_name, artist_id)
    songs = load_songs(artist_id, token)
    chain = build_chain(songs)
    print(generate_song(chain))