import os
import sys
import random
import re
import requests

from bs4 import BeautifulSoup
from json import dumps

LIBRARY = 'static/artists/'
MANIFEST = 'static/manifest.csv'
TOKEN = ''
V = lambda *args: None # Verbose printing function. Does nothing by default

class Artist():

    def __init__(self, name):
        self.name = name.replace(' ', '-').lower()

        # Check manifest for artist
        found = False
        if os.path.exists(MANIFEST):
            # Check manifest for artist
            V('Checking manifest for %s...' % self.name)
            with open(MANIFEST) as f:
                manifest = [row.split(',') for row in f.readlines()]
                for row in manifest:
                    if self.name == row[0]:
                        found = True
                        # Read ID
                        self.id = row[1]
                        V('id=' + self.id)
            V('found=%s' % found)
        else:
            with open(MANIFEST, 'w') as f:
                f.write('artist,id,last_updated\n')
            V('No manifest found.')
        
        if found:
            self.load_songs()
        else:
            self.fetch_id()
            self.fetch_songs()
            self.scrape_songs()

        self.build_chain()

    def build_chain(self, n=2):
        # Build markov chain
        chain = {}
        headers = {'Authorization': 'Bearer ' + TOKEN}
        V('Building lyric model...')

        for i, song in enumerate(self.songs):
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
        self.chain = chain

    def fetch_id(self):
        '''
        Fetch artist ID from Genius.
        Throws exception if artist isn't found. Sets self.id. Updates manifest.
        '''
        self.id = None
        V('Getting %s id from Genius...' % self.name)

        url = 'https://www.genius.com/artists/' + self.name
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            self.id = re.search(r'(?<=content="\/artists\/)\d+(?=")', response.text).group(0)
        else:
            raise Exception('Artist not found! (HTTP Error %d)' % response.status_code)
        V('Found %s. (id=%s)' % (self.name, self.id))

        # Update manifest
        with open(MANIFEST) as f:
            manifest = f.readlines()
        manifest.append('%s,%s,%s\n' % (self.name, self.id, 'today'))
        with open(MANIFEST, 'w') as f:
            for row in manifest:
                f.write(row)

    def fetch_songs(self):
        '''
        Fetch song list from Genius.
        Saves list in library.
        '''
        V('Fetching songs...')
        songs = []
        per_page = 50 # songs per request
        next_page = 1 # page of results indexed from 1
        url = 'http://api.genius.com/artists/%s/songs' % self.id
        headers = {'Authorization': 'Bearer ' + TOKEN}
        while next_page != None:
            params = {'per_page': per_page, 'page': next_page}
            json = requests.get(url, params=params, headers=headers).json()
            for song in json['response']['songs']:
                s = Song(
                    self, 
                    song['title'], 
                    id=song['id'],
                    url=song['url'])
                songs.append(s)
            next_page = json['response']['next_page']
            V('Found ' + str(len(songs)) + ' songs so far...')
        V(str(len(songs)) + ' songs found.')
        self.songs = songs

        # If the artist folder doesn't exist, create it
        if not os.path.exists(LIBRARY):
            os.mkdir(LIBRARY)
        if not os.path.exists(LIBRARY + self.id):
            os.mkdir(LIBRARY + self.id)

        # Save song list
        with open(LIBRARY + self.id + '/songs.csv', 'w') as f:
            f.write('title,id,url')
            for song in songs:
                f.write('%s,%s,%s\n' % (song.title, song.id, song.url))

        return songs

    def load_songs(self):
        try:
            V('Loading song manifest...')
            self.songs = []
            with open(LIBRARY + self.id + '/songs.csv') as f:
                rows = [row.strip().split(',') for row in f.readlines()[1:]]
                self.songs = [Song(self, row[0], id=row[1], url=row[2]) for row in rows]

            V('Loading songs from disk...')
            for i, song in enumerate(self.songs):
                V('%d/%d' % (i, len(self.songs)))
                song.load()
        except Exception as e:
            V('Failed! ' + str(e))
            self.fetch_songs()
            self.scrape_songs()

    def new_song(self, lines=21):
        # Generate a new song
        # start with a capital letter
        chain = self.chain
        pair = ('a')
        while not pair[0][0].isupper():
            pair = random.choice(list(chain.keys()))
        # generate song
        count = 0
        song = '1)\t' + pair[0] + ' '
        while count < lines:
            song += pair[1] + ' '
            if pair[1] == '\n':
                count += 1
                if count != lines:
                    song += '\b' + str(count+1) + ')\t'
            try:
                nextWord = random.choice(chain[pair])
            except:
                count += 1
            pair = (pair[1], nextWord)
        song += '\b'
        return song

    def scrape_songs(self):
        V('Scraping songs from Genius...')
        for i, song in enumerate(self.songs):
            V('%d/%d' % (i, len(self.songs)))
            song.scrape()
            song.save()

class Song():

    def __init__(self, artist, title, **kwargs):
        self.artist = artist
        self.title = title

        # credit
        # id
        # url
        self.__dict__.update(kwargs)

        self.raw_text = ''
        self.text = ''

    def load(self):
        with open(LIBRARY + str(self.artist.id) + '/songs/' + str(self.id)) as f:
            self.raw_text = ''.join(f.readlines())

            text = self.raw_text
            # get rid of section labels
            text = re.sub(r'\[.+\]', '', text)
            # get rid of some of the empty lines and leading/trailing whitespace
            text = re.sub(r'\n\n\n', '\n\n', text).strip()
            self.text = text

    def save(self):
        path = LIBRARY + self.artist.id + '/songs/'

        # If the artist's songs folder doesn't exist, create it
        if not os.path.exists(path):
            os.mkdir(path)

        with open(path + str(self.id), 'w') as f:
            f.write(self.raw_text)

    def scrape(self, url=None):
        if url == None:
            url = self.url
        page = requests.get(url)
        html = BeautifulSoup(page.text, 'html.parser')
        self.raw_text = html.find('div', class_='lyrics').get_text()

        text = self.raw_text
        # get rid of section labels
        text = re.sub(r'\[.+\]', '', text)
        # get rid of some of the empty lines and leading/trailing whitespace
        text = re.sub(r'\n\n\n', '\n\n', text).strip()
        self.text = text

def get_api_token(filename='token'):
    V('Reading authorization token...')
    try:
        return open(filename).read()
    except:
        raise Exception('Error reading token from file!')

def get_song(id):
    # No lyrics in API song endpoint
    url = 'http://api.genius.com/song/' + id
    headers = {'Authorization': 'Bearer ' + TOKEN}
    params = {'text_format': 'dom,plain,html'}
    json = requests.get(url, params=params, headers=headers).json()
    V(dumps(json, indent=4))

def set_verbose(verbose):
    if verbose:
        global V
        def verbose_print(*args):
            print(*args)
        V = verbose_print

if __name__ == '__main__':
    name = input('Artist name? ')
    set_verbose(True)
    TOKEN = get_api_token()
    artist = Artist(name)
    print(artist.new_song())
