# -*- coding: utf8 -*-

import logging
import base64

from sql import upsert, doupsert, doquery, MySQLdb
from memoize import memoize_with_expiry, cache_persist, long_cache_persist
import utility

logger = logging.getLogger(__name__)

sitestring_cache = dict()
class SiteString(object):
    """
    SiteString - used for storage and translation of arbitrary strings

    >>> scarf.core.new_string('welcomebanner', 'Welcome to the site')
    1110L
    >>> scarf.core.SiteString('welcomebanner').string
    'Welcome to the site'
    >>> scarf.core.SiteString('welcomebanner', 'fr').string
    'Welcome to the site'
    >>> scarf.core.new_string('welcomebanner', 'Bienvenue sur le site', 'fr')
    1112L
    >>> scarf.core.SiteString('welcomebanner', 'fr').string
    'Bienvenue sur le site'
    >>> scarf.core.SiteString('welcomebanner').string
    'Welcome to the site'
    >>> scarf.core.SiteString('welcomebanner', 'es').string
    'Welcome to the site'

    If the string does not currently exist it will be created and the string will be set to the name, this allows you to use SiteString blindly and not worry if a string has actually been translated.

    >>> scarf.core.SiteString('Add to collection').string
    'Add to collection'
    >>> scarf.core.SiteString('Add to collection', 'fr').string
    'Add to collection'
    >>> scarf.core.new_string('Add to collection', 'Ajouter à la collection', 'fr')
    1114L
    >>> scarf.core.SiteString('Add to collection', 'fr').string
    'Ajouter à la collection'

    """
    DEFAULTLANG = 'en'

    @classmethod
    @memoize_with_expiry(sitestring_cache, long_cache_persist)
    def create(cls, name, lang=None):
        return cls(name, lang)

    def __init__(self, name, lang=DEFAULTLANG):
        if not name:
            raise NoString(name, lang)

        sql = 'select id, string from strings where name = %(name)s and lang = %(lang)s;'
        result = doquery(sql, { 'name': name, 'lang': lang })

        try: 
            self.uid = result[0][0]
            self.name = name
            self.string = base64.b64decode(result[0][1])
            self.lang = lang
        except IndexError:
            sql = 'select id, string from strings where name = %(name)s and lang = %(lang)s;'
            result = doquery(sql, { 'name': name, 'lang': SiteString.DEFAULTLANG })

            try: 
                self.uid = result[0][0]
                self.name = name
                self.string = base64.b64decode(result[0][1])
                self.lang = SiteString.DEFAULTLANG
            except IndexError:
                uid = new_string(name, name)
                if not uid:
                    raise NoString(name)

                self.uid = uid
                self.name = name
                self.string = name
                self.lang = lang

    def update(self):
        """
        Writes the current object state back to the database

        :return: UID of the object that was updated
        """

        logger.info('string updated {}: {} '.format(self.uid, self.name))
        sql = "update strings set string = %(string)s where id = %(uid)s;"
        sitestring_cache = dict()
        return doquery(sql, {"uid": self.uid, "string": base64.b64encode(self.string)})

    def delete(self, all_langs=False):
        """
        Removes the current object from the database.

        :param all_langs: Set to True if all versions of the string should be removed
        :return: None
        """

        if all_langs:
            sql = 'delete from strings where name = %(name)s;'
        else:
            sql = 'delete from strings where name = %(name)s and lang = %(lang)s;'

        result = doquery(sql, { 'name': self.name, 'lang': self.lang })

        sitestring_cache = dict()
        logger.info('deleted string id {}'.format(self.uid))

def new_string(name, string, lang=SiteString.DEFAULTLANG):
    """
    Create a new string in the database.

    :param name: Name of the string. Strings configurable by the user should have all-lowercase descriptive names so as not to conflict with translations. When used for translation the name should be the DEFAULTLANG version of the string itself.
    :param string: The string to be stored. 
    :param lang: Optional parameter, defaults to DEFAULTLANG
    :return: UID of the new string, or UID of the existing string if it already exists
    """

    if not name or not string:
        return NoString(name, string)

    try:
        sql = 'select id from strings where name = %(name)s and lang = %(lang)s;'
        result = doquery(sql, { 'name': name, 'lang': lang })
        return result[0][0]
    except IndexError:
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

class NoString(Exception):
    def __init__(self, name, lang=SiteString.DEFAULTLANG):
        Exception.__init__(self, name, lang)
