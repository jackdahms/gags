from blockoff import Song

LIBRARY = 'static/artists/'
MANIFEST = 'static/manifest.csv'

SONG_FILENAME = 'songs.tsv'
DELIMITER = '\t'

def in_song(query, artist):
    '''
    Searches artist's downloaded songs for the query string.
    Returns first song the query is found in
    Raises an exception if artist isn't in the manifest.
    '''
    filename = SONG_FILENAME
    delimiter = DELIMITER

    artist_id = None

    # Check manifest
    with open(MANIFEST) as f:
        rows = [row.strip().split(',') for row in f.readlines()[1:]]
        for row in rows:
            if artist == row[0]:
                artist_id = row[1]
    if artist_id is None:
        raise Exception('Arist must be in manifest!')

    # Load existing song names
    songs = []
    with open(LIBRARY + artist_id + '/' + filename) as f:
        rows = [r.strip().split(delimiter) for r in f.readlines()[1:]]
        for row in rows:
            songs.append(Song(row[0], row[1], row[2]))

    # Try and load all the lyrics from files. If they don't exist, scrape 'em.
    location = LIBRARY + artist_id + '/songs/'
    for song in songs:
        try:
            song.load(location)
        except:
            song.scrape()
        if query in song.text:
            return song

    raise Exception('Query not found in any song by artist!')

if __name__ == '__main__':
    print(in_song('U2', 'radiohead').title)
    print(in_song('10.', 'radiohead').title)