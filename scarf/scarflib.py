import hashlib
import os
import datetime
import time
import uuid
import imghdr
import base64

from scarf import app
from flask import request, redirect, session, flash, url_for
from urlparse import urlparse, urljoin
from sql import upsert, doupsert, read, doquery, delete, sql_escape 

from memoize import memoize_with_expiry, cache_persist, long_cache_persist

########## Utility stuff

# Workaround for the issue identified here:
# https://bugs.python.org/issue16512
# Credit to:
# https://coderwall.com/p/btbwlq/fix-imghdr-what-being-unable-to-detect-jpegs-with-icc_profile
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
        sql = read('ip', **{"ip": sql_escape(ip)})
        result = doquery(sql)
        app.logger.debug(result)
        return result[0][0]
    except:
        sql = upsert("ip", \
                     ip=sql_escape(ip))
        result = doupsert(sql)

        app.logger.debug(result)
        return result

class pagedata:
    accesslevels = {-1: 'anonymous', 0:'banned', 1:'user', 10:'moderator', 255:'admin'}
    pass

    def __init__(self):
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
    sql = read('users', **{"uid": sql_escape(uid)})
    result = doquery(sql)

    try:
        return result[0][1]
    except IndexError:
        return

@memoize_with_expiry(stats_cache, long_cache_persist)
def uid_by_user(username):
    sql = read('users', **{"username": sql_escape(username)})
    result = doquery(sql)

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
                 where users.username = "%s"; """ % sql_escape(username)
        result = doquery(sql)

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
                 where ownwant.userid=%s""" % self.uid

        result = doquery(sql)

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
                     where items.name='%s' and ownwant.userid='%s'""" % (sql_escape(item), self.uid)
            result = doquery(sql)

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
        sql = """select * from messages
                 where fromuserid = '%s' or touserid = '%s'""" % (self.uid, self.uid)

        result = doquery(sql)

        for item in result:
            if item[4] >= messagestatus['unread_pm']:
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
        sql = """select users.pwhash, users.pwsalt
                 from users
                 where users.uid = "%s"; """ % self.uid
        result = doquery(sql)

        try:
            pwhash = result[0][0]
            pwsalt = result[0][1]
        except IndexError:
            raise AuthFail(self.username)
 
        if self.accesslevel == 0:
            flash('Your account has been banned')
        else:
            checkhash = gen_pwhash(password, pwsalt)
            del password # meh
        
            if checkhash == pwhash:
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
        pwsalt = str(uuid.uuid4().get_hex().upper()[0:6])
        pwhash = gen_pwhash(password, pwsalt)
        del password

        sql = upsert("users", 
                     uid=self.uid, 
                     pwsalt=pwsalt,
                     pwhash=pwhash)
        data = doupsert(sql)

    def newemail(self, email):
        self.email = sql_escape(email)

        sql = upsert("users", 
                     uid=self.uid, 
                     email=self.email)
        data = doupsert(sql)

def gen_pwhash(password, salt):
    return hashlib.sha224(password + salt).hexdigest()

def new_user(username, password, email):
    try:
        salt=str(uuid.uuid4().get_hex().upper()[0:6])
        sql = upsert("users", \
                     username=sql_escape(username), \
                     pwhash=gen_pwhash(password, salt), \
                     pwsalt=salt, \
                     email=sql_escape(email), \
                     joined=datetime.datetime.now(), \
                     accesslevel=1)
        uid = doupsert(sql)

        sql = upsert("userstat_lastseen", \
                     uid=uid, \
                     date=datetime.datetime.now())
        result = doupsert(sql)
 
    except Exception as e:
        return False

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
        sql = read('images', **{"uid": sql_escape(uid)})
        result = doquery(sql)

        try: 
            self.uid = result[0][0]
            self.tag = result[0][1]
            self.userid = result[0][2]
            self.ip = result[0][3] #FIXME: needs join on ip, nothing uses this yet tho
            self.image = result[0][4]
        except IndexError:
            raise NoImage(uid)

    def delete(self):
        siteimage_cache = dict()
        #TODO image purgatory
        sql = delete('images', **{"uid": self.uid})
        result = doquery(sql)

        sql = delete('imgmods', **{"imgid": self.uid})
        result = doquery(sql)

    def approve(self):
        sql = delete('imgmods', **{"imgid": self.uid})
        result = doquery(sql)

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
    sql = read('items', **{"uid": sql_escape(uid)})
    result = doquery(sql)

    try:
        return result[0][1]
    except IndexError:
        return

@memoize_with_expiry(item_cache, long_cache_persist)
def uid_by_item(item):
    sql = read('items', **{"name": sql_escape(item)})
    result = doquery(sql)

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
        self.name = name

        sql = read('items', **{"name": sql_escape(name)})
        result = doquery(sql)

        try:
            self.uid = result[0][0]
            self.description = result[0][2]
            self.added = result[0][3]
            self.modified = result[0][4]
        except IndexError:
            raise NoItem(name)

    def delete(self):
        item_cache = dict()

        # TODO: + item edits
        sql = delete('items', **{"uid": self.uid}) 
        result = doquery(sql) 
     
        sql = delete('ownwant', **{"itemid": self.uid}) 
        result = doquery(sql) 

        sql = delete('tradelist', **{"itemid": self.uid}) 
        result = doquery(sql) 

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
                 where itemid = '%s'
                 order by uid desc;""" % self.uid
        edits = doquery(sql)

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

    have_cache = dict()
    @memoize_with_expiry(have_cache, cache_persist)
    def haveusers(self):
        haveusers = list()
        have = 0

        sql = read('ownwant', **{"itemid": self.uid})
        res = doquery(sql)
        
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

        sql = read('ownwant', **{"itemid": self.uid})
        res = doquery(sql)
        
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

        sql = read('ownwant', **{"itemid": self.uid})
        res = doquery(sql)
        
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

def new_img(f, title):
    image = base64.b64encode(f.read())

    userid = 0
    if 'username' in session:
        userid = uid_by_user(session['username'])

    if userid > 0:
        sql = upsert("images", \
                         tag=title, \
                         userid=userid, \
                         ip=ip_uid(request.remote_addr), \
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
            sql = "SELECT uid FROM items order by added desc limit " + sql_escape(limit) + ";"
        else:
            sql = "SELECT uid FROM items;"
        result = doquery(sql)
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

        sql = read('messages', **{"uid": sql_escape(messageid)})
        result = doquery(sql)

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

        sql = read('messages', **{"parent": self.uid})
        result = doquery(sql)

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

        sql = read('messages', **{"uid": sql_escape(messageid)})
        result = doquery(sql)

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

        sql = read('tradelist', **{"messageid": sql_escape(messageid)})
        result = doquery(sql)

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

        sql = upsert("messages", \
                     fromuserid=sql_escape(fromuserid), \
                     touserid=sql_escape(touserid), \
                     subject=sql_escape(subject), \
                     message=sql_escape(message), \
                     parent=sql_escape(parent), \
                     sent=datetime.datetime.now(), \
                     status=sql_escape(status))
        data = doupsert(sql)
    except Exception as e:
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
        return False

    return True

