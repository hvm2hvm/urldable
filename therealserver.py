import cherrypy
import random
import psycopg2

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

class URLShortener(object):
    def __init__(self):
        pass
        
    @cherrypy.expose
    def index(self, **kargs):
        pass
        
    @cherrypy.expose
    def shorten(self, url):
        pass
        
