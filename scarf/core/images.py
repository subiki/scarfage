from bisect import bisect
from PIL import Image
import cStringIO
import imghdr
import logging
import base64
import random

from sql import upsert, doupsert, doquery, Tree
from mail import send_mail
from memoize import memoize_with_expiry, cache_persist, long_cache_persist
import users
import utility

zonebounds=[36,72,108,144,180,216,252]
greyscale = [
            " ",
            " ",
            ".,-",
            "_ivc=!/|\\~",
            "gjez2]/(YL)t[+T7Vf",
            "mdKbNDXY5P*Q",
            "W8KMA",
            "#%$"
            ]

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

        sql = "insert into imgmods (imgid, userid, flag) values (%(imgid)s, %(userid)s, %(flag)s) on duplicate key update flag = %(flag)s;"
        doquery(sql, { 'imgid': self.uid, 'userid': userid, 'flag': 1})

    def ascii(self, scale=1):
        image_string = cStringIO.StringIO(base64.b64decode(self.image))
        im = Image.open(image_string)
        basewidth = int(100 * scale)
        wpercent = (basewidth/float(im.size[0]))
        hsize = int((float(im.size[1])*float(wpercent))) / 2
        im=im.resize((basewidth,hsize), Image.ANTIALIAS)
        im=im.convert("L") # convert to mono

        ascii=""
        for y in range(0,im.size[1]):
            for x in range(0,im.size[0]):
                lum=255-im.getpixel((x,y))
                row=bisect(zonebounds,lum)
                possibles=greyscale[row]
                ascii=ascii+possibles[random.randint(0,len(possibles)-1)]
            ascii=ascii+"\n"

        return ascii
