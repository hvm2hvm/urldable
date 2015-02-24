import os, sys

here = os.path.dirname(__file__)
sys.path.append(here)

import json
import cherrypy
import random
import psycopg2
import libpg
import re
import threading
import time
import urlparse

from liburldable import compose_url, decompose_url, create_word, format_url
from libutils import is_mobile_ua

class URLShortener(object):
    def __init__(self, config):
        self.config = config
        self.pg = libpg.PG(**config['pg'])
        self.limit_data = {
            '_shorten_existing': {},
            '_shorten_new': {},
            '_access': {},
        }
        # per minute
        self.limit_values = {
            '_shorten_existing': 20,
            '_shorten_new': 10,
            '_access': 30,
        }
        
        # self.lock = threading.Lock()

    def _limit_requests(self, location):
        ip = self._get_ip()
        ts = int(time.time())
        
        limit = self.limit_values[location]

        data = self.limit_data[location]
        
        if ip in data:
            new_data = filter(lambda x: x >= ts - 60, data[ip])
            new_data.append(ts)
            data[ip] = new_data
            if len(new_data) >= limit:
                raise cherrypy.HTTPError(400, message="Too many requests, try again later...")
        else:
            data[ip] = [ts]
            
    def _get_ip(self):
        if 'X-Forwarded-For' in cherrypy.request.headers:
            return cherrypy.request.headers['X-Forwarded-For']
        else:
            return cherrypy.request.remote.ip

    def _shorten(self, url):
        self._limit_requests('_shorten_existing')
    
        url = format_url(url)
        
        # if url exists use existing shortened url
        existing = self.pg.getOne("SELECT short, index FROM urls WHERE url=%s", [url])
        if existing:
            return compose_url(existing['short'], existing['index'])
            
        self._limit_requests('_shorten_new')
            
        # if not, create a new short url
        short = create_word() # create a random readable word
        # check if word was already created
        index = self.pg.get("SELECT max(index) FROM urls WHERE short=%s", [short])
        if not index:
            index = 0
            
        if self.pg.execute('''INSERT INTO urls(short, "index", url, last_accessed, creation_ts)
                            VALUES (%s, %s, %s, extract(epoch from now()), extract(epoch from now()))
                        ''', [short, index+1, url]):
            return compose_url(short, index+1)
        else:
            return None
    
    @cherrypy.expose
    def index(self, **kargs):
        ua = cherrypy.request.headers['User-Agent']
        return """
            <html>
            <head>
                <script src="/static/js/jquery-min.js"></script>
                <script src="/static/js/shortener.js"></script>
                <link rel="stylesheet" type="text/css" href="/static/css/main.css">
            </head>
            <body>
                <div id="central">
                    <div id="title">
                        <span>Press CTRL+V to shorten your URL</span><br />
                    </div> <br />
                    <div id="query">
                        <input type="text" name="url" id="urlbox" />
                    </div> <br />
                    <div id="results">
                    </div>
                </div>
            </body>
            </html>
            """
        
    
    @cherrypy.expose
    def _stats(self):
        url_count = self.pg.get("SELECT count(url) FROM urls")
        access_count = self.pg.get("SELECT count(*) FROM accesses")
        unique_ip_count = self.pg.get("SELECT count(distinct ip) FROM accesses")
        
        url_count_24h = self.pg.get("""
            SELECT count(url) FROM urls WHERE creation_ts > extract(epoch from now()) - 86400
            """)
        access_count_24h = self.pg.get("""
            SELECT count(*) FROM accesses WHERE ts > extract(epoch from now()) - 86400
            """)
        unique_ip_count_24h = self.pg.get("""
            SELECT count(distinct ip) FROM accesses WHERE ts > extract(epoch from now()) - 86400
            """)
        return """
            <html>
                <head>
                </head>
                <body>
                    <span>Number of URLs shortened: %d (%d in the last 24h)</span><br />
                    <span>Number of accesses: %d (%d in the last 24h)</span><br />
                    <span>Number of unique IPs: %d (%d in the last 24h)</span><br />
                </body>
            </html>
        """ % (url_count, url_count_24h, 
               access_count, access_count_24h, 
               unique_ip_count, unique_ip_count_24h)
        
    @cherrypy.expose
    def shorten(self, url, format):
        short = self._shorten(url)
        
        if short is None:
            return """
                The service couldn't create a short url for some reason, sorry.
            """
        
        if len(url) > 30:
            url = url[:17] + "..." + url[-10:]
        if format == "html":
            return """
                <span id="result">Shortened to [
                        <span id=\"short\" title="you can copy now">http://%s/%s</span> 
                    ] <br />
                    from url [ %s ].<br/>
                </span>
                <script>
                    short_url_ready();
                </script>
            """ % (self.config['server']['hostname'], short, url)
        elif format == "json":
            return json.dumps({
                "short": short,
            })
            
    @cherrypy.expose
    def favicon_ico(self):
        raise cherrypy.HTTPRedirect("/static/img/small-icon.png")
        
    @cherrypy.expose
    def default(self, *args):
        ip = self._get_ip()
        self._limit_requests('_access')
    
        if len(args) > 1:
            return "invalid url: [%s]" % ('/'.join(args))
            
        short, index = decompose_url(args[0])
        if short is None:
            return "invalid url: [%s]" % (args[0])
            
        res = self.pg.getOne("SELECT id, url FROM urls WHERE short = %s AND index = %s", [short, index])
        if res is None:
            return "invalid url: [%s]" % (args[0])
        url_id, url = res
        if not url.startswith('http') and not url.startswith('data:image'):
            url = 'http://' + url
        
        self.pg.execute("INSERT INTO accesses(ip, url_id, ts) VALUES(%s, %s, extract(epoch from now()))", 
                        [ip, url_id])
                        
        self.pg.execute("UPDATE urls SET last_accessed = extract(epoch from now()) WHERE id = %s", [url_id])
        
        raise cherrypy.HTTPRedirect(url)
        
def application(environ, start_response):
    config_fp = os.path.join(here, 'config.py')
    config = eval(open(config_fp, 'rb').read())

    cp_conf = {
        'global': {
            'server.socket_port': config.get('socket_port', 8000),
            'server.max_request_body_size': config.get('max_request_body_size', 1048576),
            'environment': config.get('environment', 'development'),
        },
    }
    
    cherrypy.tree.mount(URLShortener(config), "/", cp_conf)
    
    return cherrypy.tree(environ, start_response)
    