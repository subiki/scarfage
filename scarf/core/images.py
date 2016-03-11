import imghdr

from sql import upsert, doupsert, doquery, Tree
from mail import send_mail
from memoize import memoize_with_expiry, cache_persist, long_cache_persist
import users

"""
Workaround for the issue identified here:
https://bugs.python.org/issue16512
Credit to:
https://coderwall.com/p/btbwlq/fix-imghdr-what-being-unable-to-detect-jpegs-with-icc_profile
"""
def test_icc_profile_images(h, f):
    if h.startswith('\xff\xd8') and h[6:17] == b'ICC_PROFILE':
        return "jpeg"
imghdr.tests.append(test_icc_profile_images)

class NoImage(Exception):
    def __init__(self, item):
        Exception.__init__(self, item)

siteimage_cache = dict()
class SiteImage(object):
    @classmethod
    @memoize_with_expiry(siteimage_cache, long_cache_persist)
    def create(cls, username):
        return cls(username)

    def __init__(self, uid):
        sql = 'select * from images where uid = %(uid)s;'
        result = doquery(sql, { 'uid': uid })

        try: 
            self.uid = result[0][0]
            self.tag = result[0][1]
            self.userid = result[0][2]
            self.ip = result[0][3] #FIXME: needs join on ip, nothing uses this yet tho
            self.image = result[0][4]
            self.parent = result[0][5]
        except IndexError:
            raise NoImage(uid)

    def delete(self):
        siteimage_cache = dict()
        #TODO image purgatory
        sql = 'delete from imgmods where imgid = %(uid)s;'
        result = doquery(sql, { 'uid': self.uid })

        sql = 'delete from images where uid = %(uid)s;'
        result = doquery(sql, { 'uid': self.uid })

    def approve(self):
        sql = 'delete from imgmods where imgid = %(uid)s;'
        result = doquery(sql, { 'uid': self.uid })

    def flag(self, userid=None):
        if userid:
            sql = upsert('imgmods', **{"imgid": self.uid, "userid": userid, "flag": 1})
        else:
            sql = upsert('imgmods', **{"imgid": self.uid, "flag": 1})

