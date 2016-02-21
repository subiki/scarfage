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
from sql import upsert, doupsert, read, doquery, delete, sql_escape 
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

def ip_uid(ip):
    try:
        sql = "select uid from ip where ip = %(ip)s;"
        result = doquery(sql, { 'ip': ip })
        return result[0][0]
    except IndexError:
        sql = upsert("ip", ip=sql_escape(ip))
        result = doupsert(sql)
        return result

class pagedata:
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
        sql = """select ownwant.own, ownwant.willtrade, ownwant.want, ownwant.hidden, items.name
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

    @memoize_with_expiry(collection_cache, cache_persist)
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
        self.lastseen=datetime.datetime.now()

        sql = upsert("userstat_lastseen", \
                     uid=self.uid, \
                     date=self.lastseen)
        result = doupsert(sql)

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

        sql = upsert("users", 
                     uid=self.uid, 
                     accesslevel=self.accesslevel)
        data = doupsert(sql)

    def newpassword(self, password):
        pwhash = gen_pwhash(password)
        del password

        sql = upsert("users", 
                     uid=self.uid, 
                     pwhash=pwhash)
        data = doupsert(sql)

    def newemail(self, email):
        self.email = sql_escape(email)

        sql = upsert("users", 
                     uid=self.uid, 
                     email=self.email)
        data = doupsert(sql)

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
        joined = datetime.datetime.now()
        sql = upsert("users", \
                     username=sql_escape(username), \
                     pwhash=gen_pwhash(password), \
                     email=sql_escape(email), \
                     joined=joined, \
                     accesslevel=1)
        uid = doupsert(sql)

        sql = upsert("userstat_lastseen", \
                     uid=uid, \
                     date=joined)
        result = doupsert(sql)
 
    except Exception as e:
        return False

    # todo: add ip
    message = render_template('email/new_user.html', username=username, email=email, joined=joined)
    send_mail(recipient=email, subject='Welcome to Scarfage', message=message)

    return True



######### Image stuff

class NoImage(Exception):
    def __init__(self, item):
        Exception.__init__(self, item)

siteimage_cache = dict()
class siteimage:

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

class itemhist():
    def __init__(self, uid):
        self.uid = uid

class NoItem(Exception):
    def __init__(self, item):
        Exception.__init__(self, item)

class siteitem():
    def __init__(self, name):
        self.name = name[:64]

        sql = 'select * from items where name = %(name)s;'
        result = doquery(sql, { 'name': name })

        try:
            self.uid = result[0][0]
            self.description = result[0][2]
            self.added = result[0][3]
            self.modified = result[0][4]
        except IndexError:
            raise NoItem(name)

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
        sql = upsert("items", \
                     uid=self.uid, \
                     name=sql_escape(self.name), \
                     description=sql_escape(self.description), \
                     modified=datetime.datetime.now())

        data = doupsert(sql)

        return data

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
        sql = "SELECT body FROM itemedits WHERE uid = '%(uid)s';"
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
    if userid > 0:
        sql = upsert("itemedits", \
                     date=datetime.datetime.now(), \
                     itemid=sql_escape(itemid), \
                     userid=sql_escape(userid), \
                     ip=ip_uid(request.remote_addr), \
                     body=sql_escape(description))
    else:
        sql = upsert("itemedits", \
                     date=datetime.datetime.now(), \
                     itemid=sql_escape(itemid), \
                     ip=ip_uid(request.remote_addr), \
                     body=sql_escape(description))

    edit = doupsert(sql)
    app.logger.debug(edit)

    sql = upsert("items", \
                 uid=sql_escape(itemid), \
                 description=edit, \
                 modified=datetime.datetime.now())
    doupsert(sql)

    return edit 

def new_item(name, description, userid):
    sql = upsert("items", \
                 name=sql_escape(name), \
                 description=0, \
                 added=datetime.datetime.now(), \
                 modified=datetime.datetime.now())

    itemid = doupsert(sql)

    new_edit(itemid, description, userid)

    return itemid 

def new_img(f, title, parent):
    image = base64.b64encode(f.read())

    userid = 0
    if 'username' in session:
        userid = uid_by_user(session['username'])

    if userid > 0:
        sql = upsert("images", \
                         tag=title, \
                         userid=userid, \
                         ip=ip_uid(request.remote_addr), \
                         parent=parent, \
                         image=image)

        imgid = doupsert(sql)

        sql = upsert("imgmods", \
                     userid=userid, \
                     imgid=imgid)
        data = doupsert(sql)

    else:
        sql = upsert("images", \
                         tag=title, \
                         ip=ip_uid(request.remote_addr), \
                         parent=parent, \
                         image=image)

        imgid = doupsert(sql)

        sql = upsert("imgmods", \
                     imgid=imgid)
        data = doupsert(sql)

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
        app.logger.debug(result)
        for item in result:
            items.append(siteitem(item_by_uid(item[0])))
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

#FIXME
messagestatus = {'unread_trade': 0, 'active_trade': 1, 'complete_trade': 2, 'settled_trade': 3, 'rejected_trade': 4, 'unread_pm': 10, 'read_pm': 11}
tradestatus = {'unmarked': 0, 'rejected': 1, 'accepted': 2}

pmessage_cache = dict()
class pmessage:
    @classmethod
    @memoize_with_expiry(pmessage_cache, cache_persist)
    def create(cls, messageid):
        return cls(messageid)

    def __init__(self, messageid):
        self.messagestatus = messagestatus

        sql = 'select * from messages where uid = %(uid)s;'
        result = doquery(sql, {'uid': messageid})

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

    def parent(self):
        if self.parentid > 0:
            return pmessage.create(self.parentid)

    def read(self):
        if self.uid > 0 and self.status == messagestatus['unread_pm'] and uid_by_user(session['username']) == self.to_uid:
            sql = upsert("messages", \
                         uid=self.uid, \
                         status=messagestatus['read_pm'])
            data = doupsert(sql)
        else:
            return

    def unread(self):
        if self.uid > 0 and self.status == messagestatus['read_pm'] and uid_by_user(session['username']) == self.to_uid:
            sql = upsert("messages", \
                         uid=self.uid, \
                         status=messagestatus['unread_pm'])
            data = doupsert(sql)
        else:
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

class tradeitem:
    def __init__(self, itemid):
        self.uid = itemid 
        self.itemid = 0
        self.messageid = 0
        self.userid = 0
        self.acceptstatus = 0

    def accept(self):
        if self.uid > 0:
            sql = upsert("tradelist", \
                         uid=self.uid, \
                         acceptstatus=tradestatus['accepted'])
            data = doupsert(sql)
        else:
            return

    def reject(self):
        if self.uid > 0:
            sql = upsert("tradelist", \
                         uid=self.uid, \
                         acceptstatus=tradestatus['rejected'])
            data = doupsert(sql)
        else:
            return

#FIXME inheritance
class trademessage(pmessage):
    cache = []

    @classmethod
    def create(cls, messageid):
        for o in trademessage.cache:
            if o.uid == messageid:
                return o

        o = cls(messageid)
        cls.cache.append(o)
        return o

    def __init__(self, messageid):
        self.messagestatus = messagestatus
        self.tradestatus = tradestatus

        sql = 'select * from messages where uid = %(uid)s;'
        result = doquery(sql, {"uid": messageid})

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

        self.items = []

        sql = 'select * from tradelist where uid = %(uid)s;'
        result = doquery(sql, {"uid": messageid})

        complete = True
        for item in result:
            ti = tradeitem(item[0])
            ti.itemid = item[1]
            ti.messageid = item[2]
            ti.userid = item[3]
            ti.acceptstatus = item[4]
            ti.item = siteitem(item_by_uid(ti.itemid))
            ti.user = siteuser.create(user_by_uid(ti.userid))

            self.items.append(ti)

            if (ti.acceptstatus != tradestatus['accepted']):
                complete = False

        if complete == True and self.status < messagestatus['settled_trade']:
            self.status = messagestatus['complete_trade']

    def settle(self):
        if self.uid > 0:
            sql = upsert("messages", \
                         uid=self.uid, \
                         status=messagestatus['settled_trade'])
            data = doupsert(sql)
        else:
            return

    def reject(self):
        if self.uid > 0:
            sql = upsert("messages", \
                         uid=self.uid, \
                         status=messagestatus['rejected_trade'])
            data = doupsert(sql)
        else:
            return

def send_pm(fromuserid, touserid, subject, message, status, parent):
    if 'username' not in session:
        flash('You must be logged in to send a message or trade request!')
        return

    try:
        # todo: fix parent id validation
        if parent:
            sql = upsert("messages", \
                         fromuserid=sql_escape(fromuserid), \
                         touserid=sql_escape(touserid), \
                         subject=sql_escape(subject), \
                         message=sql_escape(message), \
                         parent=sql_escape(parent), \
                         sent=datetime.datetime.now(), \
                         status=sql_escape(status))
        else:
            sql = upsert("messages", \
                         fromuserid=sql_escape(fromuserid), \
                         touserid=sql_escape(touserid), \
                         subject=sql_escape(subject), \
                         message=sql_escape(message), \
                         sent=datetime.datetime.now(), \
                         status=sql_escape(status))
        data = doupsert(sql)
    except Exception as e:
        app.logger.error(e)
        raise

    return data

def add_tradeitem(itemid, messageid, userid, acceptstatus):
    try:
        sql = upsert("tradelist", \
                     itemid=sql_escape(itemid), \
                     messageid=sql_escape(messageid), \
                     userid=sql_escape(userid), \
                     acceptstatus=sql_escape(acceptstatus))
        data = doupsert(sql)
    except Exception as e:
        app.logger.error(e)
