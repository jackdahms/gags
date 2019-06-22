# blockoff
Turn off writer's block by taking inspiration from original, unreleased songs in the style of any artist.

# TODO
- progress bar on song loading
- support for n-grams

## Low priority:
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
