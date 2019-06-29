import datetime
import math
import os.path
import random
import re
import requests
from random import normalvariate
from threading import Thread

import pymongo
from bson.objectid import ObjectId
from bs4 import BeautifulSoup

DB = pymongo.MongoClient()['library']
TOKEN = open('token').read()
V = lambda *args: None # Verbose printing function. Does nothing by default

def stdev(A, mean):
    '''
    Returns standard deviation of values in A.
    Treats values in A as samples from a population.
    '''
    residuals = [(mean - x)**2 for x in A]
    var = sum(residuals) / (len(A) - 1)
    stdev = math.sqrt(var)
    return stdev

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

    def to_dict(self):
        return {
            'title': self.title,
            'id': self.id,
            'url': self.url
        }

    def load(self):
        song = DB.songs.find_one({'id': self.id})
        self.set_text(song['raw_text'])

    def save(self):
        song = {
            'id': self.id,
            'raw_text': self.raw_text
        }
        DB.songs.insert_one(song)

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

def build_chain(songs, n=2, job_id=None):
    # Build markov chain
    chain = {}
    V('Building lyric model...')

    for i, song in enumerate(songs):
        # Try and load all the lyrics from files. If they don't exist, scrape 'em
        try:
            song.load()
        except:
            song.scrape()
            song.save()

        V('Calculating %d/%d' % (i+1, len(songs)))
        if job_id is not None:
            DB.jobs.update_one({'_id': ObjectId(job_id)}, {'$inc': {'current': 1}})


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

def get_job(job_id):
    '''
    Returns serializable job document.
    '''
    job = DB.jobs.find_one({'_id': ObjectId(job_id)})
    job['_id'] = str(job['_id'])
    return job

def load_songs(artist_id, job_id=None, token=TOKEN):
    '''
    Returns list of Song objects with id, title, and url.
    '''   
    songs = []

    # Load existing song names
    artist = DB.artists.find_one({'_id': artist_id})
    if artist is None:
        raise Exception('No artist with id ' + str(artist_id) + ' found!')
    for s in artist['songs']:
        song = Song(s['title'], s['id'], s['url'])
        songs.append(song)

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
            V('%d songs found...' % len(songs))
            if job_id is not None:
                DB.jobs.update_one({'_id': ObjectId(job_id)}, {'$set': {'total': len(songs)}})
        DB.artists.update_one({'_id': artist_id}, {'$set': {'songs': [s.to_dict() for s in songs]}})

    # needs to happen again outside the if in case we never went in the if
    if job_id is not None:
        DB.jobs.update_one({'_id': ObjectId(job_id)}, {'$set': {'total': len(songs)}})

    return songs

def load_artist_id(name):
    '''
    Checks database and Genius for an ID that corresponds to name.
    Raises an exception if one can't be found.
    '''
    name = name.replace(' ', '-').lower()
    artist_id = None

    # Check database
    V('Checking databse for id...')
    artists = DB['artists']
    result = artists.find_one({'name': name})

    # if we didn't find it, get it from Genius and add it to the databse
    if result is None:
        V('Not found. Checking Genius...')
        url = 'https://www.genius.com/artists/' + name
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            artist_id = re.search(r'(?<=content="\/artists\/)\d+(?=")', response.text).group(0)
            artist = {
                '_id': artist_id,
                'name': name,
                'songs': []
            }
            artists.insert_one(artist)
        else:
            raise Exception('Artist not found! (HTTP Code %d)' % response.status_code)
    else:
        V('Found!')
        V(result['_id'])
        artist_id = result['_id']

    return artist_id

def new_job(artist_id, ngrams, token=TOKEN):
    '''
    Creates a document to represent a job to generate a song.
    Jobs track song counting, loading, and generation
    Returns unique id of job.
    '''
    job = {
        'artist_id': artist_id,
        'ngrams': ngrams,
        'loaded': False,
        'total': -1,
        'current': 0,
        'lines': []
    }
    job_id = str(DB.jobs.insert_one(job).inserted_id)

    def new(artist_id, job_id, token):
        songs = load_songs(artist_id, job_id)
        DB.artists.update_one({'_id': artist_id}, {'$set': {'loaded': True}})

        chain = build_chain(songs, job_id=job_id)

        # new song length sampled from normal distribution based on other songs
        song_lengths = [len(s) for s in songs]
        mean_line_count = sum(song_lengths) / len(songs)
        sd = stdev(song_lengths, mean_line_count)
        sample_length = normalvariate(mean_line_count, sd)

        for song in load_songs(artist_id, token):
            songs.append(song)
    
        lines = generate_song(chain, sample_length).split('\n')
        DB.jobs.update_one({'_id': ObjectId(job_id)}, {'$set': {'lines': lines}})

    t = Thread(target=new, args=(artist_id, job_id, token))
    t.start()

    return job_id

def set_verbose(verbose):
    if verbose:
        global V
        def verbose_print(*args):
            print(*args)
        V = verbose_print

if __name__ == '__main__':
    set_verbose(True)
    artist_name = input('Artist name? ').replace(' ', '-').lower()
    artist_id = load_artist_id(artist_name)
    songs = load_songs(artist_id)
    chain = build_chain(songs)
    print(generate_song(chain))