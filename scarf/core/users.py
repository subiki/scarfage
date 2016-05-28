import datetime
import base64
import bcrypt
import hashlib
import logging
#import hmac
import json
import random
from string import ascii_letters, digits

from flask import render_template

from .. import config

from sql import read, doquery, upsert, doupsert, doquery, Tree, MySQLdb
from mail import send_mail
from memoize import memoize_with_expiry, cache_persist, long_cache_persist
import items
import messages 

logger = logging.getLogger(__name__)

accesslevels = {-1: 'anonymous', 0:'banned', 1:'user', 10:'moderator', 255:'admin'}

def get_users():
    sql = """select users.username 
             from users
             join userstat_lastseen on userstat_lastseen.uid=users.uid 
             order by userstat_lastseen.date desc"""

    result = doquery(sql)

    users = []

    for user in result:
        users.append(SiteUser.create(user[0]))

    return users

stats_cache = dict()
@memoize_with_expiry(stats_cache, long_cache_persist)
def user_by_uid(uid):
    sql = "select username from users where uid = %(uid)s;"
    result = doquery(sql, { 'uid': uid })
    try:
        return result[0][0]
    except IndexError:
        return None

@memoize_with_expiry(stats_cache, long_cache_persist)
def uid_by_user(username):
    sql = "select uid from users where username = %(username)s;"
    result = doquery(sql, { 'username': unicode(username)[:200] })

    try:
        return result[0][0]
    except IndexError:
        return None

class NoUser(Exception):
    def __init__(self, username):
        Exception.__init__(self, username)

class AuthFail(Exception):
    def __init__(self, username):
        Exception.__init__(self, username)

class OwnWant(object):
    def __init__(self, itemid, userid):
        sql = """select ownwant.uid, ownwant.own, ownwant.willtrade, ownwant.want, ownwant.hidden
                 from items
                 join ownwant on ownwant.itemid=items.uid
                 where items.uid = %(itemid)s and ownwant.userid = %(uid)s"""
        result = doquery(sql, { 'itemid': itemid, 'uid': userid })
        self.itemid = itemid
        self.userid = userid

        try:
            self.uid = result[0][0]
            self.have = result[0][1]
            self.willtrade = result[0][2]
            self.want = result[0][3]
            self.hidden = result[0][4]
        except IndexError:
            self.uid = 0
            self.have = 0
            self.willtrade = 0
            self.want = 0
            self.hidden = 0

    def update(self, values):
        update = dict(uid=self.uid, userid=self.userid, itemid=self.itemid)
        update.update(values)
 
        sql = upsert("ownwant", safe=True, **update)
        data = doupsert(sql, safe=True)
        sql = "delete from ownwant where own = '0' and want = '0' and willtrade = '0';"
        result = doquery(sql)

    def values(self):
        return dict(have=self.have, want=self.want, willtrade=self.willtrade, hidden=self.hidden)

class SiteUserProfile(object):
    def __init__(self, username=None, uid=None):
        try:
            if username:
                uid = uid_by_user(username)

            if not uid:
                raise NoUser(None)

            sql = """select json 
                     from user_profiles
                     where uid = %(uid)s; """
            result = doquery(sql, { 'uid': uid })

            self.uid = uid
            self.profile = json.loads(result[0][0])
        except (Warning, IndexError):
            self.profile = dict()
            self.profile['timezone'] = "America/Los_Angeles"

            sql = "insert into user_profiles (uid, json) values (%(uid)s, %(json)s);"
            result = doquery(sql, { 'uid': uid, 'json': json.dumps(self.profile)})
 
    def update(self):
        profile_cache = dict()
        sql = "update user_profiles set json = %(json)s where uid = %(uid)s;"
        doquery(sql, {"uid": self.uid, "json": json.dumps(self.profile)})

siteuser_cache = dict()
collection_cache = dict()
profile_cache = dict()
message_cache = dict()
class SiteUser(object):
    @classmethod
    @memoize_with_expiry(siteuser_cache, cache_persist)
    def create(cls, username):
        return cls(username)

    def __init__(self, username):
        self.auth = False
        self.username = unicode(username).strip()[:200]

        sql = """select users.uid, users.email, users.joined, userstat_lastseen.date, users.accesslevel 
                 from users
                 join userstat_lastseen on userstat_lastseen.uid=users.uid 
                 where users.username = %(username)s; """

        try:
            result = doquery(sql, { 'username': self.username })
            self.uid = result[0][0]
            self.email = result[0][1]
            self.joined = result[0][2]
            self.lastseen = result[0][3]
            self.accesslevel = result[0][4]
        except IndexError:
            raise NoUser(username)
        except (Warning, TypeError):
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
            sitem = items.SiteItem.create(item[4])
            sitem.have = item[0]
            sitem.willtrade = item[1]
            sitem.want = item[2]
            sitem.hidden = item[3]

            ret.append(sitem)

        return ret


    @memoize_with_expiry(profile_cache, cache_persist)
    def profile(self):
        return SiteUserProfile(self.username)

    #@memoize_with_expiry(collection_cache, cache_persist)
    # ^^^ causes a bug with ownwant updates
    def query_collection(self, item):
        return OwnWant(item, self.uid)

    @memoize_with_expiry(message_cache, cache_persist)
    def messages(self):
        ret = list()
        sql = """select uid,status from messages
                 where fromuserid = %(fromuid)s or touserid = %(touid)s
                 order by sent desc;"""

        result = doquery(sql, { 'fromuid': self.uid, 'touid': self.uid })

        for item in result:
            if item[1] >= messages.messagestatus['unread_pm']:
                message = messages.PrivateMessage.create(item[0])
            else:
                message = messages.TradeMessage.create(item[0])

            ret.append(message)

        return ret

    def seen(self):
        now = datetime.datetime.utcnow().replace(microsecond=0)

        if now - self.lastseen > datetime.timedelta(minutes=10):
            sql = "INSERT INTO userstat_lastseen (date, uid) VALUES (%(lastseen)s, %(uid)s) ON DUPLICATE KEY UPDATE date = %(lastseen)s, uid = %(uid)s;"
            result = doquery(sql, { 'uid': self.uid, 'lastseen': now.strftime("%Y-%m-%d %H:%M:%S") })

    def authenticate(self, password):
        sql = """select users.pwhash
                 from users
                 where users.uid = %(uid)s;"""
        result = doquery(sql, { 'uid': self.uid })

        try:
            pwhash = result[0][0]
        except IndexError:
            logger.info('AuthFail for user {}: unable to find user'.format(self.username))
            raise AuthFail(self.username)
 
        if self.accesslevel == 0:
            logger.info('AuthFail for user {}: account has been banned'.format(self.username))
            raise AuthFail(self.username)

        if not verify_pw(password, pwhash):
            logger.info('AuthFail for user {}: invalid password'.format(self.username))
            raise AuthFail(self.username)

        logger.info('Successful authentication for user {}'.format(self.username))

    def newaccesslevel(self, accesslevel):
        logger.info('Accesslevel change for user {}, was {} is now {}'.format(self.username, self.accesslevel, accesslevel))
        self.accesslevel = int(accesslevel)

        sql = "update users set accesslevel = %(level)s where uid = %(uid)s;"
        doquery(sql, {"uid": self.uid, "level": self.accesslevel})

    def newpassword(self, password):
        logger.info('Password reset for user {}'.format(self.username))
        pwhash = gen_pwhash(password)
        del password

        sql = "update users set pwhash = %(pwhash)s where uid = %(uid)s;"
        return doquery(sql, {"uid": self.uid, "pwhash": pwhash})

    def newemail(self, email):
        logger.info('Email reset for user {}'.format(self.username))
        self.email = email

        sql = "update users set email = %(email)s where uid = %(uid)s;"
        return doquery(sql, {"uid": self.uid, "email": email})

    def forgot_pw_reset(self, ip, admin=False):
        logger.info('Forgotten password reset for user {} by {}'.format(self.username, ip))
        newpw = ''.join([random.choice(ascii_letters + digits) for _ in range(12)])
        self.newpassword(newpw)

        message = render_template('email/pwreset.html', username=self.username, email=self.email, newpw=newpw, admin=admin, ip=ip)
        send_mail(recipient=self.email, subject='Password Reset', message=message)

    def delete(self):
        logger.info('Account deletion for user {}'.format(self.username))

        #TODO: clean up the other tables
        sql = "delete from userstat_lastseen where uid = %(uid)s;"
        doquery(sql, {"uid": self.uid})

        sql = "delete from user_profiles where uid = %(uid)s;"
        doquery(sql, {"uid": self.uid})

        sql = "delete from users where uid = %(uid)s;"
        doquery(sql, {"uid": self.uid})


def hashize(string):
    return base64.b64encode(hashlib.sha384(string).digest())

def gen_pwhash(password):
    return bcrypt.hashpw(hashize(password), bcrypt.gensalt(config.BCRYPT_ROUNDS))

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
    username = unicode(username).strip()[:200]
    email = email.strip()[:200]
    pwhash = gen_pwhash(password)

    if len(username) == 0:
        raise NoUser(0)

    if len(email) < 3:
        raise NoUser(0)

    joined = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    try:
        sql = "select uid from users where username = %(username)s;"
        uid = doquery(sql, { 'username': username })[0][0]
        # user exists
        return False
    except (Warning, IndexError):
        # user doesn't exist
        pass

    try:
        sql = "insert into users (username, pwhash, email, joined, accesslevel) values (%(username)s, %(pwhash)s, %(email)s, %(joined)s, '1');"
        result = doquery(sql, { 'username': username, 'pwhash': pwhash, 'email': email, 'joined': joined })

        uid = doquery("select last_insert_id();")[0][0]
        if not uid:
            raise NoUser(username)

        sql = "insert into userstat_lastseen (date, uid) values (%(lastseen)s, %(uid)s);"
        result = doquery(sql, { 'uid': uid, 'lastseen': joined })
    except MySQLdb.Error, e:
        try:
            logger.info('MySQL error adding new user {} - {}: {})'.format(username, e.args[0], e.args[1]))
            raise NoUser(username)
        except IndexError:
            logger.info('MySQL error adding new user {} - {})'.format(username, e))
            raise NoUser(username)

    if '0.0.0.0' not in ip:
        message = render_template('email/new_user.html', username=username, email=email, joined=joined, ip=ip)
        send_mail(recipient=email, subject='Welcome to Scarfage', message=message)

    logger.info('Added new user {} ({})'.format(username, uid))
    return uid
