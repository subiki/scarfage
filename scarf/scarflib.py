import os
import datetime
import time
import uuid
import imghdr
import base64
import bcrypt
import hashlib
#import hmac
import random

from config import *
from string import ascii_letters, digits

from scarf import app
from flask import request, redirect, session, flash, url_for, render_template
from urlparse import urlparse, urljoin
from sql import upsert, doupsert, doquery, Tree
from mail import send_mail

from memoize import memoize_with_expiry, cache_persist, long_cache_persist

########## Utility stuff

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

def xor_strings(s,t):
    return "".join(chr(ord(a)^ord(b)) for a,b in zip(s,t))

def obfuscate(string):
    try:
        return base64.b16encode(xor_strings('\xaa\x99\x95\x167\xd3\xe1A\xec\x92\xff\x9eR\xb8\xd9\xa85\xc8\xe2\x92$\xaf\xd7\x16', str(string))).lower()
    except TypeError:
        return None

def deobfuscate(string):
    try:
        return xor_strings('\xaa\x99\x95\x167\xd3\xe1A\xec\x92\xff\x9eR\xb8\xd9\xa85\xc8\xe2\x92$\xaf\xd7\x16', base64.b16decode(str(string.upper())))
    except TypeError:
        return None

def ip_uid(ip, r=False):
    try:
        sql = "select uid from ip where ip = %(ip)s;"
        result = doquery(sql, { 'ip': ip })
        return result[0][0]
    except IndexError:
        if r:
            return None
        sql = "insert into ip (ip) values ( %(ip)s );"
        result = doquery(sql, { 'ip': ip })
        app.logger.info(result)
        return ip_uid(ip, True)

class pagedata(object):
    accesslevels = {-1: 'anonymous', 0:'banned', 1:'user', 10:'moderator', 255:'admin'}
    pass

    def __init__(self):
        try:
            self.prefix = prefix
        except NameError:
            self.prefix = ''

        if 'username' in session:
            self.authuser = siteuser.create(session['username'])
            try:
                self.authuser = siteuser.create(session['username'])
            except:
                pass

######### User stuff
stats_cache = dict()
@memoize_with_expiry(stats_cache, long_cache_persist)
def get_whores_table():
    sql = """select count(*), users.username
             from users 
             join ownwant on ownwant.userid=users.uid 
             where ownwant.own = 1 
             group by users.uid, ownwant.own 
             order by count(*) desc limit 10;"""
    result = doquery(sql)

    return result;

willtrade_cache = dict()
@memoize_with_expiry(willtrade_cache, long_cache_persist)
def get_willtrade_table():
    sql = """select count(*), users.username
             from users 
             join ownwant on ownwant.userid=users.uid 
             where ownwant.willtrade = 1 
             group by users.uid, ownwant.willtrade
             order by count(*) desc limit 10;"""
    result = doquery(sql)

    return result;

needy_cache = dict()
@memoize_with_expiry(needy_cache, long_cache_persist)
def get_needy_table():
    sql = """select count(*), users.username
             from users 
             join ownwant on ownwant.userid=users.uid 
             where ownwant.want = 1 
             group by users.uid, ownwant.want
             order by count(*) desc limit 10;"""
    result = doquery(sql)

    return result;

contribs_cache = dict()
@memoize_with_expiry(contribs_cache, long_cache_persist)
def get_contribs_table():
    sql = """select count(*), users.username
             from users 
             join itemedits on itemedits.userid=users.uid 
             group by users.uid, itemedits.userid
             order by count(*) desc limit 10;"""
    result = doquery(sql)

    return result;

@memoize_with_expiry(stats_cache, long_cache_persist)
def user_by_uid(uid):
    sql = "select username from users where uid = %(uid)s;"
    result = doquery(sql, { 'uid': uid })
    try:
        return result[0][0]
    except IndexError:
        return

@memoize_with_expiry(stats_cache, long_cache_persist)
def uid_by_user(username):
    sql = "select uid from users where username = %(username)s;"
    result = doquery(sql, { 'username': username })

    try:
        return result[0][0]
    except IndexError:
        return

class NoUser(Exception):
    def __init__(self, username):
        Exception.__init__(self, username)

class AuthFail(Exception):
    def __init__(self, username):
        Exception.__init__(self, username)

class ownwant(object):
    def __init__(self):
        self.have = 0
        self.want = 0
        self.willtrade = 0
        self.hidden = 0

siteuser_cache = dict()
collection_cache = dict()
message_cache = dict()
class siteuser(object):
    @classmethod
    @memoize_with_expiry(siteuser_cache, cache_persist)
    def create(cls, username):
        return cls(username)

    def __init__(self, username):
        self.auth = False
        self.username = username

        sql = """select users.uid, users.email, users.joined, userstat_lastseen.date, users.accesslevel 
                 from users
                 join userstat_lastseen on userstat_lastseen.uid=users.uid 
                 where users.username = %(username)s; """

        result = doquery(sql, { 'username': username })

        try:
            self.uid = result[0][0]
            self.email = result[0][1]
            self.joined = result[0][2]
            self.lastseen = result[0][3]
            self.accesslevel = result[0][4]
        except IndexError:
            raise NoUser(username)
        except TypeError:
            pass

        if 'username' in session:
            if session['username'] is username:
                self.seen()
                self.auth = True
            else:
                self.auth = False

    @memoize_with_expiry(collection_cache, cache_persist)
    def collection(self):
        ret = list()
        sql = """select ownwant.own, ownwant.willtrade, ownwant.want, ownwant.hidden, items.uid
                 from ownwant
                 join items on items.uid=ownwant.itemid
                 where ownwant.userid = %(uid)s"""

        result = doquery(sql, { 'uid': self.uid })

        for item in result:
            sitem = siteitem(item[4])
            sitem.have = item[0]
            sitem.willtrade = item[1]
            sitem.want = item[2]
            sitem.hidden = item[3]

            ret.append(sitem)

        return ret

    #@memoize_with_expiry(collection_cache, cache_persist)
    # ^^^ causes a bug with ownwant updates
    def query_collection(self, item):
        ret = ownwant()

        try:
            sql = """select ownwant.uid, ownwant.own, ownwant.willtrade, ownwant.want, ownwant.hidden
                     from items
                     join ownwant on ownwant.itemid=items.uid
                     where items.name = %(name)s and ownwant.userid = %(uid)s"""
            result = doquery(sql, { 'name': item, 'uid': self.uid })

            ret.uid = result[0][0]
            ret.have = result[0][1]
            ret.willtrade = result[0][2]
            ret.want = result[0][3]
            ret.hidden = result[0][4]
        except IndexError:
            pass

        return ret

    @memoize_with_expiry(message_cache, cache_persist)
    def messages(self):
        ret = list()
        sql = """select uid,status from messages
                 where fromuserid = %(fromuid)s or touserid = %(touid)s"""

        result = doquery(sql, { 'fromuid': self.uid, 'touid': self.uid })

        for item in result:
            if item[1] >= messagestatus['unread_pm']:
                pm = pmessage.create(item[0])
            else:
                pm = trademessage.create(item[0])

            ret.append(pm)

        return ret

    def seen(self):
        self.lastseen=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # FIXME: update, not insert
        sql = "INSERT INTO userstat_lastseen (date, uid) VALUES (%(lastseen)s, %(uid)s) ON DUPLICATE KEY UPDATE date = %(lastseen)s, uid = %(uid)s;"
        result = doquery(sql, { 'uid': self.uid, 'lastseen': self.lastseen })

    def authenticate(self, password):
        sql = """select users.pwhash
                 from users
                 where users.uid = %(uid)s;"""
        result = doquery(sql, { 'uid': self.uid })

        try:
            pwhash = result[0][0]
        except IndexError:
            raise AuthFail(self.username)
 
        if self.accesslevel == 0:
            flash('Your account has been banned')
        else:
            if verify_pw(password, pwhash):
                session['username'] = self.username
            else:
                raise AuthFail(self.username)

    def newaccesslevel(self, accesslevel):
        self.accesslevel = int(accesslevel)

        sql = "update users set accesslevel = %(level)s where uid = %(uid)s;"
        return doquery(sql, {"uid": self.uid, "level": self.accesslevel})

    def newpassword(self, password):
        pwhash = gen_pwhash(password)
        del password

        sql = "update users set pwhash = %(pwhash)s where uid = %(uid)s;"
        return doquery(sql, {"uid": self.uid, "pwhash": pwhash})

    def newemail(self, email):
        self.email = email

        sql = "update users set email = %(email)s where uid = %(uid)s;"
        return doquery(sql, {"uid": self.uid, "email": email})

    def forgot_pw_reset(self, admin=False):
        newpw = ''.join([random.choice(ascii_letters + digits) for _ in range(12)])
        self.newpassword(newpw)

        message = render_template('email/pwreset.html', username=self.username, email=self.email, newpw=newpw, admin=admin, ip=request.environ['REMOTE_ADDR'])
        send_mail(recipient=self.email, subject='Password Reset', message=message)

def hashize(string):
    return base64.b64encode(hashlib.sha384(string).digest())

def gen_pwhash(password):
    return bcrypt.hashpw(hashize(password), bcrypt.gensalt(13))

def verify_pw(password, pwhash):
    if (bcrypt.hashpw(hashize(password), pwhash) == pwhash):
        return True

    return False

"""
python 2.7.7+ only

def verify_pw(password, pwhash):
    if (hmac.compare_digest(bcrypt.hashpw(hashize(password), pwhash), pwhash)):
        return True

    return False

"""

def check_email(email):
    sql = "select username from users where email = %(email)s;"
    result = doquery(sql, { 'email': email })

    try: 
        return siteuser.create(result[0][0])
    except IndexError:
        return None

def new_user(username, password, email):
    try:
        joined = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sql = "insert into users (username, pwhash, email, joined, accesslevel) values (%(username)s, %(pwhash)s, %(email)s, %(joined)s, '1');"
        result = doquery(sql, { 'username': username, 'pwhash': gen_pwhash(password), 'email': email, 'joined': joined })

        sql = "insert into userstat_lastseen (date, uid) values (%(lastseen)s, %(uid)s);"
        result = doquery(sql, { 'uid': uid_by_user(username), 'lastseen': joined })
    except Exception as e:
        return False

    message = render_template('email/new_user.html', username=username, email=email, joined=joined, ip=request.environ['REMOTE_ADDR'])
    send_mail(recipient=email, subject='Welcome to Scarfage', message=message)

    return True

######### Image stuff

class NoImage(Exception):
    def __init__(self, item):
        Exception.__init__(self, item)

siteimage_cache = dict()
class siteimage(object):
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

    def flag(self):
        try:
            userid = uid_by_user(session['username'])
            sql = upsert('imgmods', **{"imgid": self.uid, "userid": userid, "flag": 1})
        except KeyError:
            sql = upsert('imgmods', **{"imgid": self.uid, "flag": 1})

        result = doquery(sql)

######### Item stuff

class Tag(Tree):
    def __init__(self):
        super(self.__class__, self).__init__('tags')

item_cache = dict()
@memoize_with_expiry(item_cache, long_cache_persist)
def item_by_uid(uid):
    sql = 'select name from items where uid = %(uid)s;'
    result = doquery(sql, { 'uid': uid })

    try:
        return result[0][0]
    except IndexError:
        return

@memoize_with_expiry(item_cache, long_cache_persist)
def uid_by_item(item):
    sql = 'select uid from items where name = %(name)s;'
    result = doquery(sql, { 'name': item })

    try:
        return result[0][0]
    except IndexError:
        return

class itemhist(object):
    def __init__(self, uid):
        self.uid = uid

class NoItem(Exception):
    def __init__(self, item):
        Exception.__init__(self, item)

class siteitem(object):
    def __init__(self, uid):
        sql = 'select * from items where uid = %(uid)s;'
        result = doquery(sql, { 'uid': uid })

        try:
            self.uid = result[0][0]
            self.name = result[0][1]
            self.description = result[0][2]
            self.added = result[0][3]
            self.modified = result[0][4]
        except IndexError:
            raise NoItem(uid)

        """
        sql = 'select tag from itemtags where uid = %(uid)s;'
        result = doquery(sql, { 'uid': uid })

        try:
            self.tags = result[0]
        except IndexError:
            self.tags = None
        """

    def delete(self):
        item_cache = dict()

        sql = 'delete from itemedits where itemid = %(uid)s;'
        result = doquery(sql, {"uid": self.uid}) 
     
        sql = 'delete from ownwant where itemid = %(itemid)s;'
        result = doquery(sql, {"itemid": self.uid}) 

        sql = 'delete from tradelist where itemid = %(itemid)s;'
        result = doquery(sql, {"itemid": self.uid}) 

        sql = 'delete from items where uid = %(uid)s;'
        result = doquery(sql, {"uid": self.uid}) 

    def update(self):
        sql = "update items set name = %(name)s, description = %(desc)s, modified = %(modified)s where uid = %(uid)s;"
        return doquery(sql, {"uid": self.uid, "desc": self.description, "name": self.name, "modified": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") })

    def history(self):
        sql = """select itemedits.uid, itemedits.itemid, itemedits.date, itemedits.userid, ip.ip
                 from itemedits
                 join ip on itemedits.ip=ip.uid
                 where itemid = %(uid)s
                 order by uid desc;"""
        edits = doquery(sql, { 'uid': self.uid })

        ret = list()
        for edit in edits:
            editobject = itemhist(edit[0])
            editobject.uid = str(editobject.uid).zfill(8)
            editobject.itemid = edit[1]
            editobject.date = edit[2]
            editobject.userid = edit[3]
            editobject.ip = edit[4]

            editobject.user = user_by_uid(editobject.userid)

            ret.append(editobject)

        return ret

    imglist_cache = dict()
    @memoize_with_expiry(imglist_cache, cache_persist)
    def images(self):
        ret = list()
        sql = """select uid
                 from images
                 where parent = %(uid)s"""
        for row in doquery(sql, { 'uid': self.uid }):
            ret.append(siteimage(row[0]))

        return ret

    body_cache = dict()
    @memoize_with_expiry(body_cache, cache_persist)
    def body(self):
        sql = "select body from itemedits where uid = '%(uid)s';"
        return doquery(sql, {'uid': self.description })[0][0]

    have_cache = dict()
    @memoize_with_expiry(have_cache, cache_persist)
    def haveusers(self):
        haveusers = list()
        have = 0

        sql = "select * from ownwant where itemid = %(uid)s"
        res = doquery(sql, {"uid": self.uid})
        
        for user in res:
            if (user[3] == 1):
                have = have + 1
                if(user[6] == 0):
                    userinfo = siteuser.create(user_by_uid(user[1]))
                    haveusers.append(userinfo)

        return (have, haveusers)

    willtrade_cache = dict()
    @memoize_with_expiry(willtrade_cache, cache_persist)
    def willtradeusers(self):
        willtradeusers = list()
        willtrade = 0

        sql = "select * from ownwant where itemid = %(uid)s"
        res = doquery(sql, {"uid": self.uid})
 
        
        for user in res:
            if (user[4] == 1):
                willtrade = willtrade + 1
                if(user[6] == 0):
                    userinfo = siteuser.create(user_by_uid(user[1]))
                    willtradeusers.append(userinfo)

        return (willtrade, willtradeusers)

    want_cache = dict()
    @memoize_with_expiry(want_cache, cache_persist)
    def wantusers(self):
        wantusers = list()
        want = 0

        sql = "select * from ownwant where itemid = %(uid)s"
        res = doquery(sql, {"uid": self.uid})
        
        for user in res:
            if (user[5] == 1):
                want = want + 1
                if(user[6] == 0):
                    userinfo = siteuser.create(user_by_uid(user[1]))
                    wantusers.append(userinfo)

        return (want, wantusers)

def new_edit(itemid, description, userid):
    if userid == 0:
        userid = None

    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = "insert into itemedits (date, itemid, userid, ip, body) values (%(date)s, %(itemid)s, %(userid)s, %(ip)s, %(body)s);"
    doquery(sql, { 'date': date, 'itemid': itemid, 'userid': userid, 'ip': ip_uid(request.remote_addr), 'body': description })

    sql = "select uid from itemedits where date=%(date)s and itemid=%(itemid)s and ip=%(ip)s;"
    edit = doquery(sql, { 'date': date, 'itemid': itemid, 'ip': ip_uid(request.remote_addr) })[0][0]

    sql = "update items set description = %(edit)s, modified = %(modified)s where uid = %(uid)s;"
    doquery(sql, {"uid": itemid, "edit": edit, "modified": date })

    return edit 

def new_item(name, description, userid):
    sql = "insert into items (name, description, added, modified) values (%(name)s, 0, %(now)s, %(now)s);"
    doquery(sql, { 'now': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'name': name })

    sql = "select uid from items where name=%(name)s and description=0;"
    itemid = doquery(sql, { 'name': name })[0][0]

    new_edit(itemid, description, userid)

    return itemid 

def new_img(f, title, parent):
    image = base64.b64encode(f.read())

    userid = None
    if 'username' in session:
        userid = uid_by_user(session['username'])

    sql = "insert into images (tag, parent, userid, image, ip) values (%(tag)s, %(parent)s, %(userid)s, %(image)s, %(ip)s);"
    doquery(sql, { 'tag': title, 'userid': userid, 'ip': ip_uid(request.remote_addr), 'parent': parent, 'image': image})

    sql = "select uid from images where tag=%(tag)s and parent=%(parent)s and ip=%(ip)s;"
    imgid = doquery(sql, { 'tag': title, 'ip': ip_uid(request.remote_addr), 'parent': parent })[0][0]

    sql = "insert into imgmods (userid, imgid) values (%(userid)s, %(imgid)s);"
    doquery(sql, { 'userid': userid, 'imgid': imgid })

    flash('Uploaded ' + f.filename)
    return imgid 

@memoize_with_expiry(item_cache, long_cache_persist)
def latest_items(limit=0):
    items = list()

    try:
        if limit > 0:
            sql = "SELECT uid FROM items order by added desc limit %(limit)s;"
        else:
            sql = "SELECT uid FROM items;"
        result = doquery(sql, { 'limit': limit })
        for item in result:
            items.append(siteitem(item[0]))
    except TypeError:
        pass

    return items

######### Redirect stuff

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

def redirect_back(endpoint, **values):
    target = request.referrer
    if not target or not is_safe_url(target):
        target = url_for(endpoint, **values)
    return redirect(target)


# Trade and message stuff

messagestatus = {'unread_trade': 0, 'active_trade': 1, 'complete_trade': 2, 'settled_trade': 3, 'rejected_trade': 4, 'cancelled_trade': 5, 'unread_pm': 10, 'read_pm': 11}
tradeitemstatus = {'unmarked': 0, 'rejected': 1, 'accepted': 2}

pmessage_cache = dict()
class pmessage(object):
    @classmethod
    @memoize_with_expiry(pmessage_cache, cache_persist)
    def create(cls, messageid):
        return cls(messageid)

    def __init__(self, messageid):
        self.messagestatus = messagestatus

        sql = 'select * from messages where uid = %(uid)s;'
        result = doquery(sql, {'uid': messageid})

        try:
            self.uid = result[0][0]
            self.uid_obfuscated = obfuscate(result[0][0])
            self.from_uid = result[0][1]
            self.to_uid = result[0][2]
            self.subject = result[0][3]
            self.message = result[0][4]
            self.status = result[0][5]
            self.parentid = result[0][6]
            self.parentid_obfuscated = obfuscate(result[0][6])
            self.sent = result[0][7]

            self.from_user = siteuser.create(user_by_uid(self.from_uid)).username
            self.to_user = siteuser.create(user_by_uid(self.to_uid)).username
        except IndexError:
            raise NoItem(messageid)

    def parent(self):
        if self.parentid > 0:
            return pmessage.create(self.parentid)

    def setstatus(self, status):
        if self.uid > 0:
            self.status = status
            sql = "update messages set status = %(status)s where uid = %(uid)s;"
            result = doquery(sql, {"uid": self.uid, "status": status})
        else:
            return None

    def read(self):
        if self.uid > 0 and uid_by_user(session['username']) == self.to_uid:
            status = None
            if self.status == messagestatus['unread_pm']:
                status = messagestatus['read_pm']
            elif self.status == messagestatus['unread_trade']:
                status = messagestatus['active_trade']

            if status:
                return self.setstatus(status)

        return

    def unread(self):
        if self.status == messagestatus['read_pm']:
            return self.setstatus(messagestatus['unread_pm'])
        elif self.status >= messagestatus['unread_trade']:
            return self.setstatus(messagestatus['unread_trade'])
        return

    @memoize_with_expiry(pmessage_cache, cache_persist)
    def replies(self):
        ret = list()

        sql = 'select * from messages where parent = %(uid)s;'
        result = doquery(sql, {"uid": self.uid})

        for reply in result:
            pm = pmessage.create(reply[0])
            ret.append(pm)

        return ret

class tradeitem(object):
    def __init__(self, itemid):
        self.uid = itemid 
        self.itemid = 0
        self.messageid = 0
        self.userid = 0
        self.acceptstatus = 0

    def setstatus(self, status):
        if self.uid > 0:
            self.acceptstatus = status

            sql = "update tradelist set acceptstatus = %(status)s where uid = %(uid)s;"
            return doquery(sql, { "uid": self.uid, "status": status })

    def accept(self):
        return self.setstatus(tradeitemstatus['accepted'])

    def reject(self):
        return self.setstatus(tradeitemstatus['rejected'])

trademessage_cache = dict()
class trademessage(pmessage):
    @classmethod
    @memoize_with_expiry(trademessage_cache, cache_persist)
    def create(cls, messageid):
        return cls(messageid)

    def __init__(self, messageid):
        super(self.__class__, self).__init__(messageid)
        self.tradeitemstatus = tradeitemstatus

        self.items = []

        sql = 'select * from tradelist where messageid = %(uid)s;'
        result = doquery(sql, {"uid": messageid})

        complete = True
        for item in result:
            ti = tradeitem(item[0])
            ti.itemid = item[1]
            ti.messageid = item[2]
            ti.userid = item[3]
            ti.acceptstatus = item[4]
            ti.item = siteitem(ti.itemid)
            ti.user = siteuser.create(user_by_uid(ti.userid))

            self.items.append(ti)

            if (ti.acceptstatus != tradeitemstatus['accepted']):
                complete = False

        if complete == True and self.status < messagestatus['settled_trade']:
            self.status = messagestatus['complete_trade']

    def settle(self):
        return self.setstatus(messagestatus['settled_trade'])

    def reject(self):
        return self.setstatus(messagestatus['rejected_trade'])

    def cancel(self):
        return self.setstatus(messagestatus['cancelled_trade'])

def send_pm(fromuserid, touserid, subject, message, status, parent):
    if 'username' not in session:
        flash('You must be logged in to send a message or trade request!')
        return

    # FIXME: parent id validation
    sent = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = "insert into messages (fromuserid, touserid, subject, message, parent, sent, status) values (%(fromuserid)s, %(touserid)s, %(subject)s, %(message)s, %(parent)s, %(sent)s, %(status)s);"
    doquery(sql, { 'fromuserid': fromuserid, 'touserid': touserid, 'subject': subject, 'message': message, 'parent': parent, 'sent': sent, 'status': status })

    sql = "select uid from messages where fromuserid=%(fromuserid)s and touserid=%(touserid)s and sent=%(sent)s;"
    messageid = doquery(sql, { 'fromuserid': fromuserid, 'touserid': touserid, 'sent': sent })[0][0]

    email_user = siteuser.create(user_by_uid(touserid))
    from_user = siteuser.create(user_by_uid(fromuserid))

    message = render_template('email/pm_notify.html', to_user=email_user, email=email_user.email, from_user=from_user, message=message, status=status, parent=parent, messageid=obfuscate(messageid))

    if status >= 10:
        subject = '[Scarfage] (PM) '
    else:
        subject = '[Scarfage] (Trade) '

    send_mail(recipient=email_user.email, subject=subject + subject, message=message)

    return messageid 

def add_tradeitem(itemid, messageid, userid, acceptstatus):
    sql = "insert into tradelist (itemid, messageid, userid, acceptstatus) values (%(itemid)s, %(messageid)s, %(userid)s, %(acceptstatus)s);"
    doquery(sql, { 'itemid': itemid, 'messageid': messageid, 'userid': userid, 'acceptstatus': acceptstatus })
