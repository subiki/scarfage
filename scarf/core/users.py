import datetime
import base64
import bcrypt
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
import utility

logger = logging.getLogger(__name__)

accesslevels = {-1: 'anonymous', 0:'banned', 1:'user', 10:'moderator', 255:'admin'}

def get_users():
    """
    Get a list of all users sorted by last seen.
  
    .. todo:: Add range and sort parameters
    :return: List of SiteUsers
    """
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
    """
    Lookup username by uid

    :param uid: UID of a user
    :return: None or the username
    """
    sql = "select username from users where uid = %(uid)s;"
    result = doquery(sql, { 'uid': uid })
    try:
        return result[0][0]
    except IndexError:
        return None

@memoize_with_expiry(stats_cache, long_cache_persist)
def uid_by_user(username):
    """
    Lookup user's UID by username

    :param username: User's username
    :return: UID of the user
    """

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
    """
    Object containing a user's status for an item
    """

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
        """
        Update the current object and the database from a dict

        :Example:

        >>> OwnWant(item_id, user_id).update(dict(own=1, hidden=0, willtrade=1, want=0))

        :param values: dict to update the object with. Any not being updated can be omitted
        :return: None
        """

        update = dict(uid=self.uid, userid=self.userid, itemid=self.itemid)
        update.update(values)
 
        sql = upsert("ownwant", safe=True, **update)
        data = doupsert(sql, safe=True)
        sql = "delete from ownwant where own = '0' and want = '0' and willtrade = '0';"
        result = doquery(sql)

    def values(self):
        """
        Return the object as a dict
 
        :return: dict(have=self.have, want=self.want, willtrade=self.willtrade, hidden=self.hidden)
        """
        return dict(have=self.have, want=self.want, willtrade=self.willtrade, hidden=self.hidden)

class SiteUserProfile(object):
    """
    Object for a user's profile. Not much here yet.

    The object can be initialized with either a username or UID.

    :raises NoUser: If no user is found NoUser will be raised
    """

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

            # Delete this at some point once all data has been moved, shouldn't take long
            if 'avatar' in self.profile:
                logger.info('avatar fixup applied for user id {}'.format(uid))
                self.new_avatar(self.profile['avatar'])
                del self.profile['avatar']
                self.update()
        except (Warning, IndexError):
            # return defaults
            self.profile = dict()
            self.profile['timezone'] = "America/Los_Angeles"

            #sql = "insert into user_profiles (uid, json) values (%(uid)s, %(json)s);"
            #result = doquery(sql, { 'uid': uid, 'json': json.dumps(self.profile)})
 
    def update(self):
        profile_cache = dict()
        sql = "update user_profiles set json = %(json)s where uid = %(uid)s;"
        doquery(sql, {"uid": self.uid, "json": json.dumps(self.profile)})

    def avatar(self):
        sql = """select avatar
                 from user_profiles
                 where uid = %(uid)s; """
        result = doquery(sql, { 'uid': self.uid })
        try:
            return result[0][0]
        except IndexError:
            return None

    def new_avatar(self, image):
        profile_cache = dict()
        sql = "update user_profiles set avatar = %(image)s where uid = %(uid)s;"
        doquery(sql, {"uid": self.uid, "image": image})

siteuser_cache = dict()
collection_cache = dict()
profile_cache = dict()
message_cache = dict()
class SiteUser(object):
    """
    SiteUser - user object

    :Attributes:
        * uid           - User ID
        * email         - User's email address
        * joined        - Datetime object of when they joined 
        * lastseen      - Datetime object of when they were last seen online
        * accesslevel   - Users accesslevel as an integer
    """

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
        """
        List a user's collection

        :return: list of SiteItem objects
        """
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
        """
        Get the profile for a user

        :return: SiteUserProfile object
        """
        return SiteUserProfile(self.username)

    #@memoize_with_expiry(collection_cache, cache_persist)
    # ^^^ causes a bug with ownwant updates
    def query_collection(self, itemid):
        """
        Get the collection status for an item id

        :param itemid: The id of the item you want to query
        :return: OwnWant object for the item
        """
        return OwnWant(itemid, self.uid)

    mwi_cache = dict()
    @memoize_with_expiry(mwi_cache, long_cache_persist)
    def mwi(self):
        """
        Get a count of unread messages and trades for a user

        :return: (unread messages, unread trades)
        """

        num_messages = 0
        num_trades = 0

        sql = """select uid,status from messages
                 where touserid = %(touid)s
                 order by sent desc limit 100;"""

        result = doquery(sql, { 'touid': self.uid })

        for item in result:
            message = messages.TradeMessage.create(item[0])

            if message.delete_status(self.username):
                continue

            read = message.read_status(self.username)

            if not read:
                if item[1]:
                    num_trades = num_trades + 1
                else:
                    num_messages = num_messages + 1

        return (num_messages, num_trades)

    @memoize_with_expiry(message_cache, cache_persist)
    def messages(self, trash=False):
        """
        Get all trades and private messages for a user

        :param trash: Only show deleted messages. Permanent deletion is not currently implemented.
        :return: list of PrivateMessage and TradeMessage objects
        """

        mwi_cache = dict()
        ret = list()
        sql = """select uid,status from messages
                 where fromuserid = %(fromuid)s or touserid = %(touid)s
                 order by sent desc;"""

        result = doquery(sql, { 'fromuid': self.uid, 'touid': self.uid })

        for item in result:
            if item[1]:
                message = messages.TradeMessage.create(item[0])
            else:
                message = messages.PrivateMessage.create(item[0])

            deleted = message.delete_status(self.username)

            if trash:
                deleted = not deleted
            if not deleted:
                ret.append(message)

        return ret

    def seen(self):
        """
        Method to update the last seen time for a user
        """

        now = datetime.datetime.utcnow().replace(microsecond=0)

        if now - self.lastseen > datetime.timedelta(minutes=10):
            sql = "INSERT INTO userstat_lastseen (date, uid) VALUES (%(lastseen)s, %(uid)s) ON DUPLICATE KEY UPDATE date = %(lastseen)s, uid = %(uid)s;"
            result = doquery(sql, { 'uid': self.uid, 'lastseen': now.strftime("%Y-%m-%d %H:%M:%S") })

    def authenticate(self, password):
        """
        Verify a user's password

        :param password: The plaintext password to verify.
        :return: None
        :raises AuthFail: This exception will be raised if the user cannot be logged in for any reason.
        """

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
        return None

    def newaccesslevel(self, accesslevel):
        """
        Method to change a user's access level

        :param accesslevel: The new accesslevel
        """

        logger.info('Accesslevel change for user {}, was {} is now {}'.format(self.username, self.accesslevel, accesslevel))
        self.accesslevel = int(accesslevel)

        sql = "update users set accesslevel = %(level)s where uid = %(uid)s;"
        doquery(sql, {"uid": self.uid, "level": self.accesslevel})

    def newpassword(self, password):
        """
        Method to reset a user's password

        :param password: The new plaintext password
        """

        logger.info('Password reset for user {}'.format(self.username))
        pwhash = gen_pwhash(password)
        del password

        sql = "update users set pwhash = %(pwhash)s where uid = %(uid)s;"
        return doquery(sql, {"uid": self.uid, "pwhash": pwhash})

    def newemail(self, email):
        """
        Method to reset a user's email

        :param email: The new plaintext email
        """

        logger.info('Email reset for user {}'.format(self.username))
        self.email = email

        sql = "update users set email = %(email)s where uid = %(uid)s;"
        return doquery(sql, {"uid": self.uid, "email": email})

    def forgot_pw_reset(self, ip, admin=False):
        """
        Randomize a user's password and send it to the email we have for them.

        :param ip: The IP address of the requester as a string
        :param admin: Set to True if this was requested by an admin
        """

        logger.info('Forgotten password reset for user {} by {}'.format(self.username, ip))
        newpw = ''.join([random.choice(ascii_letters + digits) for _ in range(12)])
        self.newpassword(newpw)

        message = render_template('email/pwreset.html', username=self.username, email=self.email, newpw=newpw, admin=admin, ip=ip)
        send_mail(recipient=self.email, subject='Password Reset', message=message)

    def delete(self):
        """
        Delete a user account. Possibly dangerous.
        """
        logger.info('Account deletion for user {}'.format(self.username))

        #TODO: clean up the other tables
        sql = "delete from userstat_lastseen where uid = %(uid)s;"
        doquery(sql, {"uid": self.uid})

        sql = "delete from user_profiles where uid = %(uid)s;"
        doquery(sql, {"uid": self.uid})

        sql = "delete from users where uid = %(uid)s;"
        doquery(sql, {"uid": self.uid})


def gen_pwhash(password):
    """
    Generate a password hash for the given cleartext

    :param password: Cleartext password to hash
    :return: bcrypt.hashpw(utility.hashize(password), bcrypt.gensalt(config.BCRYPT_ROUNDS))
    """

    return bcrypt.hashpw(utility.hashize(password), bcrypt.gensalt(config.BCRYPT_ROUNDS))

def verify_pw(password, pwhash):
    """
    Verify a cleartext password

    :param password: Cleartext password
    :param pwhash: Password hash to verify against
    :return: True or False
    """

    if (bcrypt.hashpw(utility.hashize(password), pwhash) == pwhash):
        return True

    return False

"""
python 2.7.7+ only

def verify_pw(password, pwhash):
    if (hmac.compare_digest(bcrypt.hashpw(utility.hashize(password), pwhash), pwhash)):
        return True

    return False

"""

def check_email(email):
    """
    Check if an email address belongs to a user

    :param email: The email address to check
    :return: SiteUser object or None
    """

    sql = "select username from users where email = %(email)s;"
    result = doquery(sql, { 'email': email })

    try: 
        return SiteUser.create(result[0][0])
    except IndexError:
        return None

def new_user(username, password, email, ip):
    """
    Register a new user

    :param username: Username. Truncated to 200 characters
    :param password: Cleartext password
    :param email: email address. Truncated to 200 characters
    :param ip: IP address of the requester

    :raises NoUser: if an invalid email or username is given, or on general failure in creating the user
    :return: UID of the new user or False if the username is taken
    """

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
