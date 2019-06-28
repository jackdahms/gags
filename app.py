import json
import time
from random import normalvariate

from flask import Flask
from flask import flash, redirect, render_template, request, url_for

from gags import * 

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/find')
def find():
    if 'artist' not in request.args.keys():
        return redirect(url_for('index'))

    artist = request.args.get('artist').strip().lower().replace(' ', '-')
    if artist == '':
        return redirect(url_for('index'))

    try:
        artist_id = load_artist_id(artist)
        return render_template('index.html', found=True, artist_data=(artist, artist_id))
    except:
        return render_template('index.html', found=False, artist_data=(artist, None))

@app.route('/generate')
def generate():
    '''
    TODO
    1. create a job in database
        - client displays spinner
    2. client checks job
        - if songs counted, client displays progress bar
        - if songs loaded, client updates progress bar
    3. remove job
    '''
    if 'artist' not in request.args.keys():
        return redirect(url_for('index'))
    artist = request.args.get('artist')

    if 'artist_id' not in request.args.keys():
        return redirect(url_for('find', artist=request.args.get('artist')))
    artist_id = request.args.get('artist_id')

    if 'ngrams' not in request.args.keys():
        return render_template('index', found=True, artist_data=(artist, artist_id))
    ngrams = request.args.get('ngrams')
    try:
        ngrams = int(ngrams)
    except:
        return render_template('index', found=True, artist_data=(artist, artist_id))

    job_id = new_job(artist, artist_id, ngrams)
    return render_template('song.html', 
                           found=True, 
                           artist_data=(artist, artist_id), 
                           job_id=job_id)

@app.route('/status')
def status():
    '''
    Check status of a job.
    '''
    if 'job_id' not in request.args.keys():
        return redirect(url_for('index'))
    job_id = request.args.get('job_id')

    current, total, lines = job_status(job_id);

    payload = {
        'song_count': total,
        'current_song': current,
        'lyrics': lines
    }
    return json.dumps(payload)

if __name__ == "__main__":
    app.secret_key = '123'
    app.run(debug=True)
