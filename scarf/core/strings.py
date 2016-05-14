import logging
import base64

from sql import upsert, doupsert, doquery, MySQLdb
from memoize import memoize_with_expiry, cache_persist, long_cache_persist
import utility

logger = logging.getLogger(__name__)

class NoString(Exception):
    def __init__(self, name, lang):
        Exception.__init__(self, name, lang)

sitestring_cache = dict()
class SiteString(object):
    DEFAULTLANG = 'en'

    @classmethod
    @memoize_with_expiry(sitestring_cache, long_cache_persist)
    def create(cls, name):
        return cls(name)

    def __init__(self, name, lang=None):
        if not lang:
            lang = SiteString.DEFAULTLANG

        sql = 'select id, string from strings where name = %(name)s and lang = %(lang)s;'
        result = doquery(sql, { 'name': name, 'lang': lang })

        try: 
            self.uid = result[0][0]
            self.name = name
            self.string = base64.b64decode(result[0][1])
            self.lang = lang
        except IndexError:
            raise NoString(name, lang)

    def update(self):
        logger.info('string updated {}: {} '.format(self.uid, self.name))
        sql = "update strings set string = %(string)s where id = %(uid)s;"
        sitestring_cache = dict()
        return doquery(sql, {"uid": self.uid, "string": base64.b64encode(self.string)})

    def delete(self):
        logger.info('deleted string id {}'.format(self.uid))
        sitestring_cache = dict()
        sql = 'delete from strings where id = %(uid)s;'
        result = doquery(sql, { 'uid': self.uid })

def new_string(name, string, lang=SiteString.DEFAULTLANG):
    if not name or not string:
        return NoString(name, string)

    try:
        SiteString(name, lang)
        return None
    except:
        pass

    try:
        sql = "insert into strings (name, string, lang) values (%(name)s, %(string)s, %(lang)s);"
        doquery(sql, {'name': name, 'string': base64.b64encode(string), 'lang': lang})

        sql = "select last_insert_id();"
        uid = doquery(sql)[0][0]
        if uid is None:
            raise NoString(name, lang)
    except (MySQLdb.OperationalError, MySQLdb.DataError, Warning):
        raise NoString(name, lang)

    return uid
