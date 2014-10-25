import cherrypy
import random
import psycopg2
import libpg
import re
import threading

from liburldable import compose_url, decompose_url, create_word, format_url

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
            return compose_url(existing['short'], existing['index'])
            
        # if not, create a new short url
        short = create_word() # create a random readable word
        # check if word was already created
        index = self.pg.get("SELECT max(index) FROM urls WHERE short=%s", [short])
        if not index:
            index = 0
            
        if self.pg.execute('''INSERT INTO urls(short, "index", url, last_accessed)
                            VALUES (%s, %s, %s, extract(epoch from now()))
                        ''', [short, index+1, url]):
            return compose_url(short, index+1)
        else:
            return None
    
    @cherrypy.expose
    def index(self, **kargs):
        return """
        <html>
        <head>
            <script src="/static/js/jquery-min.js"></script>
            <script src="/static/js/shortener.js"></script>
            <link rel="stylesheet" type="text/css" href="/static/css/main.css">
        </head>
        <body>
            <div id="central">
                <div id="query">
                    <input type="text" name="url" id="urlbox" />
                    <button name="shorten" id="button" onclick="do_shorten()">shorten</button>
                </div> <br />
                <div id="results">
                </div>
            </div>
        </body>
        </html>
        """
       
    @cherrypy.expose
    def shorten(self, url):
        print "url = [%s]" % (url)
        short = self._shorten(url)
        print "short url = [%s]" % (short)
        
        if short is None:
            return """
                The service couldn't create a short url for some reason, sorry.
            """
        
        if len(url) > 30:
            url = url[:17] + "..." + url[-10:]
        
        return """
            <span id="result">Shortened to [
                    <span id=\"short\" title="you can copy now">http://%s/%s</span> 
                ] <br />
                from url [ %s ].<br/>
                (hover over url to select it)
            </span>
            <script>
                $("#short").hover(function(){
                    SelectText("short");
                });
            </script>
        """ % (self.config['server']['hostname'], short, url)
        
    @cherrypy.expose
    def default(self, *args):
        if len(args) > 1:
            return "invalid url: [%s]" % ('/'.join(args))
            
        short, index = decompose_url(args[0])
        if short is None:
            return "invalid url: [%s]" % (args[0])
            
        url = self.pg.get("SELECT url FROM urls WHERE short = %s AND index = %s", [short, index])
        # return "redirect url: [%s]" % (url)
        raise cherrypy.HTTPRedirect(url)
        
config = eval(open('config.py', 'rb').read())

cherrypy.quickstart(URLShortener(config), config="cherrypy.conf")
