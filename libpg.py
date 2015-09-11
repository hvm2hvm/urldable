import threading
import psycopg2
import psycopg2.extras

def log(*args):
    for a in args:
        print a,
    print

class PG(object):

    def __init__(self, uselocks=True, **kargs):
        """
            available parameters:
                user, host, password, database/dbname
                uselocks: lock requests s.t. only 1 operation is allowed per connection
        """
        
        self.params = {
            'host': 'localhost',
            'port': 5432,
            'dbname': 'postgres',
            'user': 'postgres',
            'password': 'postgres',
        }
        self.params.update(kargs)
        
        if 'database' in self.params:
            self.params['dbname'] = self.params['database']
            del self.params['database']
        
        self.uselocks = uselocks
        if uselocks:
            self.lock = threading.Lock()
        
        self.connect()
        
    def connect(self):
        # try:
            # self.cur.close()
        # except:
            # pass
        try:
            self.conn.close()
        except:
            pass
            
        try:
            self.conn = psycopg2.connect(**self.params)
            self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        except Exception as e:
            self.conn = None
            log("failed to connect %s:%s to %s:%s: %s" % (self.params['user'], self.params['password'], 
                self.params['host'], self.params['port'], e))
        
    def execute(self, query, params, commit=1):
        if self.uselocks:
            self.lock.acquire()
            
        try:
            retries = 3
            while True:
                try:
                    self.cur.execute(query, params)
                    if commit:
                        self.conn.commit()
                    return True
                except Exception as e:
                    retries -= 1
                    if retries <= 0:
                        break
                    log("query failed: [%s] with params %s" % (query, params))
                    log("   exception: %s" % (e))
                    log("retrying, %d attempts left" % (retries))
                    self.connect()
                    
            log("failed after 3 retries")
            return False
        finally:
            if self.uselocks:
                self.lock.release()
        
    def get(self, query, params=[], commit=1):
        row = self.execute(query, params, commit) and self.cur.fetchone()
        if row:
            return row[0]
        return None
        
    def getOne(self, query, params=[], commit=1):
        return self.execute(query, params, commit) and self.cur.fetchone()
        
    def getMany(self, query, count, params=[], commit=1):
        rows = self.execute(query, params, commit) and self.cur.fetchall()
        if rows:
            return rows[:count]
        else:
            return None
            
    def getList(self, query, params=[], commit=1):
        rows = self.execute(query, params, commit) and self.cur.fetchall()
        if rows:
            return [x[0] for x in rows]
        else:
            return None
        
    def getAll(self, query, params=[], commit=1):
        rows = self.execute(query, params, commit) and self.cur.fetchall()
        if rows:
            return rows
        else:
            return None