# G.A.G.S
#### Good At Generating Songs
Turn off writer's block by taking inspiration from original, unreleased songs in the style of any artist.

# TODO
- n-grams
- advanced options
    - force search for new songs
    - line ending method
        - mean centered normal
        - median centered
        - end-of-song character
        - random sample

## Mongo Collections
- artists
    - genius_id: Genius' artist ID
    - name: hyphenated lower case name
    - songs: array of dictionaries
        - title: title of song
        - id: Genius' song ID
        - url: url to Genius page with lyrics
- jobs
- songs
    - id: Genius' song ID
    - raw_text: as scraped from HTML

## Low priority:
- https://stackoverflow.com/questions/118241/calculate-text-width-with-javascript
- mongo automatically delete jobs
- add api exception for status()
- if artist is past TTL, refresh
- what to do about punctuation?
    - ignore when building chain?
- advanced options dropdown
- song title generation
- put os.path.joins everywhere
- web interface
    - filter songs/albums used to generate
    - view table of artists with statistics
    - option to include featured work
    - button to update for artist? Not good if publicly facing.
- get lyrics for multiple songs in one request? big bottleneck...
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
- replace BeautifulSoup with built-in parser: https://docs.python.org/3/library/html.parser.html
- carbon ads
