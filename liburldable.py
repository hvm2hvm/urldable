import random
import re

vowels = "aeiou"
consonants = "bcdfgjklmnprstvz"
joinable_consonants = "bfgkp" # can be followed by 'l' or 'r'
# joinable_syllables = "" # can be joined but in different syllables (kloNDike)

def create_word():
    random.seed()

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
    elif url.lower().startswith('https://'):
        start_index = 8
        
    end_index = url.find("/", start_index)
    return url[:end_index].lower() + url[end_index:]
    
short_re = re.compile(r"(?P<short>[a-z]+)(?P<index>[0-9]+)?")
def decompose_url(short_and_index):
    m = short_re.match(short_and_index)
    if m is None:
        return None, None
    m = m.groupdict()
    index = 1
    if m['index']:
        index = int(m['index'])
    short = m['short']
    return short, index
    
def compose_url(short, index):
    if index > 1:
        return "%s%d" % (short, index)
    else:
        return short

if __name__ == "__main__":
    # putting some very basic tests here
    print "testing decompose_url"
    assert ("tatziki", 2000) == decompose_url("tatziki2000")
    assert ("mister", 1) == decompose_url("mister")
    print "tests passed"