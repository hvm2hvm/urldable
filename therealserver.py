import cherrypy
import random
import psycopg2
import libpg
import re
import threading

vowels = "aeiou"
consonants = "bcdfgjklmnprstvz"
joinable_consonants = "bcdfgkpt" # can be followed by 'l' or 'r'
# joinable_syllables = "" # can be joined but in different syllables (kloNDike)

def create_word():
    two_start_cons = random.random() > 0.5
    ends_in_vowel = random.random() > 0.5
    
    w = ""
    
    # first syllable
    if two_start_cons:
        w += random.choice(joinable_consonants) + random.choice("lr")
    else:
        w += random.choice(consonants)
    w += random.choice(vowels) + random.choice(consonants) * two_start_cons * (random.random() > 0.5)
    
    # second syllable
    w += random.choice(consonants)
    w += random.choice(vowels)
    w += random.choice(consonants)
    if ends_in_vowel:
        w += random.choice(vowels)
        
    return w
    
def format_url(url):
    """
        converts the domain name part of the url to lowercase 
    """
    start_index = 0
    if url.lower().startswith('http://'):
        start_index = 7
    end_index = url.find("/", start_index)
    return url[:end_index].lower() + url[end_index:]
    
def compose_url(short, index):
    return "%s%d" % (short, index)

class URLShortener(object):
    def __init__(self, config):
        self.config = config
        self.pg = libpg.PG(**config['pg'])
        # self.lock = threading.Lock()

    def _shorten(self, url):
        url = format_url(url)
        # if url exists use existing shortened url
        existing = self.pg.getOne("SELECT short, index FROM urls WHERE url=%s", [url])
        if existing:
            return "%s%d" % (existing['short'], existing['index'])
            
        # if not, create a new short url
        short = create_word() # create a random readable word
        # check if word was already created
        index = self.pg.get("SELECT max(index) FROM urls WHERE short=%s", [short])
        if not index:
            index = 0
        self.pg.execute('''INSERT INTO urls(short, "index", url, last_accessed)
                            VALUES (%s, %s, %s, extract(epoch from now()))
                        ''', [short, index+1, url])
                        
    @cherrypy.expose
    def index(self, **kargs):
        return """
        <html>
        <body>
            
        </body>
        </html>
        """
        
    @cherrypy.expose
    def shorten(self, url):
        self._shorten(url)
        
config = eval(open('config.py', 'rb').read())
shortener_server = URLShortener(config)
shortener_server._shorten("http://google.com/asdfuKJHASDKcasd/")
