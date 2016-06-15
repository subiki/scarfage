import logging
import base64

from sql import upsert, doupsert, doquery, MySQLdb
from memoize import memoize_with_expiry, cache_persist, long_cache_persist
import utility

logger = logging.getLogger(__name__)

sitekey_cache = dict()
class SiteKey(object):
    """
    Object for key/value pairs
    """

    @classmethod
    @memoize_with_expiry(sitekey_cache, long_cache_persist)
    def create(cls, key):
        return cls(key)

    def __init__(self, key):
        if not key:
            raise NoKey(key)

        sql = 'select value from keyvalue where keyhash = %(key)s;'
        result = doquery(sql, { 'key': utility.digest(key) })

        try: 
            self.key = key
            self.value = base64.b64decode(result[0][0])
        except IndexError:
            raise NoKey(key)

    def update(self):
        """
        Writes the current object state back to the database
        """

        logger.info('key updated: {} '.format(self.key))
        sql = "update keyvalue set value = %(value)s where keyhash = %(key)s;"
        sitekey_cache = dict()
        return doquery(sql, {"value": base64.b64encode(self.value), "key": utility.digest(self.key)})

    def delete(self):
        """
        Removes the current object from the database.
        """

        sql = 'delete from keyvalue where keyhash = %(key)s;'
        result = doquery(sql, { 'key': utility.digest(self.key) })

        sitekey_cache = dict()
        logger.info('deleted key id {}'.format(self.key))

        self.key = None
        self.value = None

def check_key_exists(key):
    sql = 'select count(1) from keyvalue where keyhash = %(key)s;'
    return bool(doquery(sql, {'key': utility.digest(key)})[0][0])

def new_key(key, value):
    """
    Create a new key/value pair in the database.

    :param key: Name of the key. Will be hashed
    :param value: The value to be stored. 
    """

    if not key:
        return NoKey(key)

    key = utility.digest(key)

    try:
        sql = 'select value from keyvalue where keyhash = %(key)s;'
        result = doquery(sql, {'key': key})[0][0]
        return
    except IndexError:
        pass

    try:
        sql = "insert into keyvalue (keyhash, value) values (%(key)s, %(value)s);"
        doquery(sql, {'key': key, 'value': base64.b64encode(value)})

        sql = "select last_insert_id();"
        uid = doquery(sql)[0][0]
        if uid is None:
            raise NoKey(key)
    except (MySQLdb.OperationalError, MySQLdb.DataError, Warning):
        raise NoKey(key)

class NoKey(Exception):
    def __init__(self, key):
        Exception.__init__(self, key)
