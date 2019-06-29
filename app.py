import time
from json import dumps
from random import normalvariate

from flask import Flask
from flask import jsonify, redirect, render_template, request, url_for

from gags import * 

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', data=dumps({}))

@app.route('/find')
def find():
    if 'artist' not in request.args:
        return redirect(url_for('index'))
    
    artist_input = request.args['artist']
    artist = artist_input.strip().lower().replace(' ', '-')
    if artist == '':
        artist_input = 'Radiohead'
        artist = 'radiohead'

    data = {
        'artist': artist,
        'artist_input': artist_input,
    }
    try:
        artist_id = load_artist_id(artist)
        data['found'] = True
        data['artist_id'] = artist_id
    except:
        data['found'] = False

    return render_template('index.html', data=data)

@app.route('/generate')
def generate():
    if 'artist' not in request.args:
        return redirect(url_for('index'))
    data = {'artist': request.args['artist']}

    if 'artist_input' not in request.args:
        data['artist_input'] = data['artist']
    else:
        data['artist_input'] = request.args['artist_input']

    if 'artist_id' not in request.args:
        return redirect(url_for('find', data=data))
    data['artist_id'] = request.args['artist_id']
    data['found'] = True

    if 'ngrams' not in request.args:
        return render_template('index.html', data=data)
    try:
        data['ngrams'] = int(request.args['ngrams'])
    except:
        return render_template('index.html', data=data)

    data['job_id'] = new_job(data['artist_id'], data['ngrams'])
    return render_template('song.html', data=data)

@app.route('/status')
def status():
    '''
    Check status of a job.
    '''
    if 'job_id' not in request.args.keys():
        return redirect(url_for('index'))
    job_id = request.args.get('job_id')

    job = get_job(job_id)
    return dumps(job)

if __name__ == "__main__":
    app.secret_key = '123'
    app.run(debug=True)
