import datetime
import base64
import bcrypt
import hashlib
#import hmac
import random
from string import ascii_letters, digits

from flask import render_template

from sql import upsert, doupsert, doquery, Tree
from mail import send_mail
from memoize import memoize_with_expiry, cache_persist, long_cache_persist
import items
import messages 

accesslevels = {-1: 'anonymous', 0:'banned', 1:'user', 10:'moderator', 255:'admin'}

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

class OwnWant(object):
    def __init__(self):
        self.have = 0
        self.want = 0
        self.willtrade = 0
        self.hidden = 0

siteuser_cache = dict()
collection_cache = dict()
message_cache = dict()
class SiteUser(object):
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

    @memoize_with_expiry(collection_cache, cache_persist)
    def collection(self):
        ret = list()
        sql = """select ownwant.own, ownwant.willtrade, ownwant.want, ownwant.hidden, items.uid
                 from ownwant
                 join items on items.uid=ownwant.itemid
                 where ownwant.userid = %(uid)s"""

        result = doquery(sql, { 'uid': self.uid })

        for item in result:
            sitem = items.SiteItem(item[4])
            sitem.have = item[0]
            sitem.willtrade = item[1]
            sitem.want = item[2]
            sitem.hidden = item[3]

            ret.append(sitem)

        return ret

    #@memoize_with_expiry(collection_cache, cache_persist)
    # ^^^ causes a bug with ownwant updates
    def query_collection(self, item):
        ret = OwnWant()

        try:
            sql = """select ownwant.uid, ownwant.own, ownwant.willtrade, ownwant.want, ownwant.hidden
                     from items
                     join ownwant on ownwant.itemid=items.uid
                     where items.uid = %(itemid)s and ownwant.userid = %(uid)s"""
            result = doquery(sql, { 'itemid': item, 'uid': self.uid })

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
            if item[1] >= messages.messagestatus['unread_pm']:
                message = messages.PrivateMessage.create(item[0])
            else:
                message = messages.TradeMessage.create(item[0])

            ret.append(message)

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
            raise AuthFail(self.username)

        if not verify_pw(password, pwhash):
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

    def forgot_pw_reset(self, ip, admin=False):
        newpw = ''.join([random.choice(ascii_letters + digits) for _ in range(12)])
        self.newpassword(newpw)

        message = render_template('email/pwreset.html', username=self.username, email=self.email, newpw=newpw, admin=admin, ip=ip)
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
        return SiteUser.create(result[0][0])
    except IndexError:
        return None

def new_user(username, password, email, ip):
    username = username.strip()
    email = email.strip()
    try:
        joined = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sql = "insert into users (username, pwhash, email, joined, accesslevel) values (%(username)s, %(pwhash)s, %(email)s, %(joined)s, '1');"
        result = doquery(sql, { 'username': username, 'pwhash': gen_pwhash(password), 'email': email, 'joined': joined })

        sql = "insert into userstat_lastseen (date, uid) values (%(lastseen)s, %(uid)s);"
        result = doquery(sql, { 'uid': uid_by_user(username), 'lastseen': joined })

        message = render_template('email/new_user.html', username=username, email=email, joined=joined, ip=ip)
        send_mail(recipient=email, subject='Welcome to Scarfage', message=message)
    except Exception as e:
        return False

    return True

