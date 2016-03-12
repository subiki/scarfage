import imghdr
import logging
import base64

from sql import upsert, doupsert, doquery, Tree
from mail import send_mail
from memoize import memoize_with_expiry, cache_persist, long_cache_persist
import users
import utility

logger = logging.getLogger(__name__)

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

def new_img(f, title, parent, userid, ip):
    raw = f.read()

    if not imghdr.what(None, raw):
        logger.info('failed to add image to {} by {} / {} '.format(parent, userid, ip))
        return

    image = base64.b64encode(raw)
    title = title.strip()[:64]

    sql = "insert into images (tag, parent, userid, image, ip) values (%(tag)s, %(parent)s, %(userid)s, %(image)s, %(ip)s);"
    doquery(sql, { 'tag': title, 'userid': userid, 'ip': utility.ip_uid(ip), 'parent': parent, 'image': image})

    # there is a potential race condition with last_insert_id()
    sql = "select last_insert_id();"
    imgid = doquery(sql)[0][0]

    sql = "insert into imgmods (userid, imgid) values (%(userid)s, %(imgid)s);"
    doquery(sql, { 'userid': userid, 'imgid': imgid })

    logger.info('new image added to {} by {} / {} '.format(parent, userid, ip))
    return imgid 

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
        logger.info('deleted image id {}: {}'.format(self.uid, self.tag))
        siteimage_cache = dict()
        #TODO image purgatory
        sql = 'delete from imgmods where imgid = %(uid)s;'
        result = doquery(sql, { 'uid': self.uid })

        sql = 'delete from images where uid = %(uid)s;'
        result = doquery(sql, { 'uid': self.uid })

    def approve(self):
        logger.info('moderation approved image id {}: {}'.format(self.uid, self.tag))
        sql = 'delete from imgmods where imgid = %(uid)s;'
        result = doquery(sql, { 'uid': self.uid })

    def flag(self, userid=None):
        logger.info('moderation flag added for image id {} by userid {}'.format(self.uid, userid))
        if userid:
            sql = upsert('imgmods', **{"imgid": self.uid, "userid": userid, "flag": 1})
        else:
            sql = upsert('imgmods', **{"imgid": self.uid, "flag": 1})
