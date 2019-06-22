'''
TODO
- progress bar on song loading
- support for n-grams

Low priority:
- put os.path.joins everywhere
- figure out better design for load_songs
    - build_index() returns songs?
    - load_songs() yeilds progress?
- global token variable in blockoff.py?
- better song display
- extra space at the beginning of each line in generate_song
- if artist has any songs in songs.tsv, we don't look for more songs. 
    - what if more were added?
    - what if we were interrupted when adding songs last time?
    - search for songs by default, add advanced option to disable search
- what happens when using an end of song character instead of sampled line lengths?
    - probably really long songs...
- handle outliers in song lengths?
    - center on median instead?
- keep manifest loaded?
    - race conditions... blech
    - use an actual database lol
- should all that logic even be in the constructor?
- split artist class methods into logical components
    - e.g. updating manifest shouldn't be in fetch_id
- web interface
    - filter songs/albums used to generate
    - view table of artists with statistics
    - option to include featured work
    - button to update for artist? Not good if publicly facing.
- get lyrics for multiple songs in one request? big bottleneck...
- get true capitalization from genius
    - randomly select song length from existing lengths?
- automatically filter live/different versions of songs
    - if duplicates allowed, lyrics will be weighted heavier
- generate from multiple artists
- build chains more efficiently? 
    - rather than have a list of all words that come after each tuple, 
      keep list of pairs of following words with frequency
- regex to split song into words?
- song list has some weird random songs
    - writing credit
    - when displaying songs, show relationship? (i.e. primary artist, feature, writer)
- better way of getting artist name
    - e.g. One, The One, and O-N-E all go to the same page
    - 'fingerprint conflict'?
- option to separate by verses/choruses/structural elements
    - reuse 1 chorus throughout song
    - randomly include bridge?
- skulpt for client-side python?
- keep manifest alphabetized and search for artist with binarysearch
- replace BeautifulSoup with built-in parser: https://docs.python.org/3/library/html.parser.html
- carbon ads
'''
import time
from random import normalvariate

from flask import Flask
from flask import redirect, render_template, request
from flask import send_from_directory, session, stream_with_context, url_for

from blockoff import * 

TOKEN = load_token()

app = Flask(__name__)

def stdev(A, mean):
    '''
    Returns standard deviation of values in A.
    Treats values in A as samples from a population.
    '''
    residuals = [(mean - x)**2 for x in A]
    var = sum(residuals) / (len(A) - 1)
    stdev = math.sqrt(var)
    return stdev

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/find')
def find():
    if 'artist' not in request.args.keys():
        return redirect(url_for('index'))

    artist = request.args.get('artist').strip().lower().replace(' ', '-')
    if artist == '':
        return redirect(url_for('index'))

    try:
        artist_id = load_artist_id(artist)
        add_to_manifest(artist, artist_id)
        return render_template('index.html', found=True, artist_data=(artist, artist_id))
    except:
        return render_template('index.html', found=False, artist_data=(artist, None))

@app.route('/generate')
def generate():
    if 'artist' not in request.args.keys():
        return redirect(url_for('index'))
    artist = request.args.get('artist')

    if 'artist_id' not in request.args.keys():
        return redirect(url_for('find', artist=request.args.get('artist')))
    artist_id = request.args.get('artist_id')

    if 'ngrams' not in request.args.keys():
        return render_template('index', found=True, artist_data=(artist, artist_id))

    i = 0
    count = song_count(artist_id, TOKEN)
    songs = []
    for song in load_songs(artist_id, TOKEN):
        songs.append(song)
        i += 1

    # new song length sampled from normal distribution based on other songs
    song_lengths = [len(s) for s in songs]
    mean_line_count = sum(song_lengths) / len(songs)
    sd = stdev(song_lengths, mean_line_count)
    sample_length = normalvariate(mean_line_count, sd)

    chain = build_chain(songs)
    lines = generate_song(chain, sample_length).split('\n')
    return render_template('song.html', 
                           found=True, 
                           artist_data=(artist, artist_id), 
                           lines=lines)

if __name__ == "__main__":
    app.secret_key = '123'
    app.run(debug=True)
