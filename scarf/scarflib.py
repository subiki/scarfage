import hashlib
import os
import datetime
import imghdr
import uuid
from scarf import app
from flask import request, redirect, session, escape, flash, url_for
from urlparse import urlparse, urljoin
from sql import upsert, doupsert, read, doquery, delete

# DEBUG
import socket 
if socket.gethostname() == "grenadine":
    upload_dir = '/home/pq/sf/site/scarf/static/uploads/'
else: 
    upload_dir = '/srv/data/web/vhosts/default/static/uploads/'

class pagedata:
    accesslevels = {-1: 'anonymous', 0:'banned', 1:'user', 10:'moderator', 255:'admin'}
    pass

    def __init__(self):
        self.accesslevel = -1
        if 'username' in session:
            self.authuser = siteuser(escape(session['username']))
            try:
                self.authuser = siteuser(escape(session['username']))
            except:
                pass

######### User stuff

class NoUser(Exception):
    def __init__(self, username):
        Exception.__init__(self, username)

class AuthFail(Exception):
    def __init__(self, username):
        Exception.__init__(self, username)

class siteuser:
    def __init__(self, username):
        self.auth = False
        self.username = username

        sql = read('users', **{"username": username})
        result = doquery(sql)

        try:
            self.uid = result[0][0]
            # self.username = result[0][1]
            self.pwhash = result[0][2]
            self.pwsalt = result[0][3]
            self.email = result[0][4]
            self.joined = result[0][5]
            self.lastseen = result[0][6]
            self.numadds = result[0][7]
            self.accesslevel = result[0][8]
        except IndexError:
            raise NoUser(username)
        except TypeError:
            pass

        # Update lastseen if we're looking up the currently logged in user
        if 'username' in session:
            if session['username'] is username:
                self.seen()
                self.auth = True

    def __writedb__(self):
        sql = upsert("users", \
                     uid=self.uid, \
                     pwhash=self.pwhash,
                     pwsalt=self.pwsalt,
                     email=self.email,
                     joined=self.joined,
                     lastseen=self.lastseen,
                     numadds=self.numadds,
                     accesslevel=self.accesslevel)
        data = doupsert(sql)

    def get_collection(self):
        collection = []

        sql = read('ownwant', **{"userid": self.uid})
        result = doquery(sql)

        for item in result:
            sql = read('items', **{"uid": item[2]})
            sresult = doquery(sql)

            sitem = siteitem(sresult[0][1])
            sitem.have = item[3]
            sitem.willtrade = item[4]
            sitem.want = item[5]
            sitem.hidden = item[6]

            collection.append(sitem)

        return collection

    def query_collection(self, item):
        class __ownwant__:
            def __init__(self):
                self.have = 0
                self.want = 0
                self.willtrade = 0
                self.hidden = 0
                pass

        ret = __ownwant__()

        try:
            sql = read('items', **{"name": item})
            sresult = doquery(sql)
     
            sql = read('ownwant', **{"userid": self.uid, "itemid": sresult[0][0]})
            result = doquery(sql)

            ret.uid = result[0][0]
            ret.have = result[0][3]
            ret.willtrade = result[0][4]
            ret.want = result[0][5]
            ret.hidden = result[0][6]
        except IndexError:
            pass

        return ret

    def seen(self):
        self.lastseen=datetime.datetime.now()
        self.__writedb__()

    def incadd(self):
        self.numadds = self.numadds + 1
        self.__writedb__()

    def authenticate(self, password):
        if self.accesslevel == 0:
            flash('Your account has been banned')
        else:
            checkhash = gen_pwhash(password, self.pwsalt)
        
            if checkhash == self.pwhash:
                session['username'] = self.username
            else:
                raise AuthFail(self.username)

    def newaccesslevel(self, accesslevel):
        self.accesslevel = int(accesslevel)
        self.__writedb__()

    def newpassword(self, password):
        self.pwsalt = str(uuid.uuid4().get_hex().upper()[0:6])
        self.pwhash = gen_pwhash(password, self.pwsalt)
        self.__writedb__()

    def newemail(self, email):
        self.email = email
        self.__writedb__()

    def delete(self):
        sql = delete('users', **{"uid": self.uid}) 
        result = doquery(sql) 
 
        sql = delete('ownwant', **{"userid": self.uid}) 
        result = doquery(sql)

def gen_pwhash(password, salt):
    return hashlib.sha224(password + salt).hexdigest()

def new_user(username, password, email):
    try:
        salt=str(uuid.uuid4().get_hex().upper()[0:6])
        sql = upsert("users", \
                     uid=0, \
                     username=username, \
                     pwhash=gen_pwhash(password, salt), \
                     pwsalt=salt, \
                     email=email, \
                     joined=datetime.datetime.now(), \
                     lastseen=datetime.datetime.now(), \
                     numadds=0, \
                     accesslevel=1)
        data = doupsert(sql)
    except Exception as e:
        app.logger.error("Error creating new user: " + e)
        return False

    return True

######### Image stuff

class NoImage(Exception):
    def __init__(self, item):
        Exception.__init__(self, item)

class siteimage:
    def __init__(self, uid):
        sql = read('images', **{"uid": uid})
        result = doquery(sql)

        try: 
            self.uid = result[0][0]
            self.filename = result[0][1]
            self.tag = result[0][1]
        except IndexError:
            raise NoImage(uid)

    def delete(self):
        sql = delete('itemimg', **{"imgid": self.uid})
        result = doquery(sql)

        sql = delete('images', **{"uid": self.uid})
        result = doquery(sql)

        sql = delete('imgmods', **{"imgid": self.uid})
        result = doquery(sql)

        try:
            os.remove(upload_dir + self.filename)
        except Exception as e:
            app.logger.error("Error removing image: " + e)
            raise

    def approve(self):
        sql = delete('imgmods', **{"imgid": self.uid})
        result = doquery(sql)

    def flag(self):
        if 'username' in session:
            username = session['username']
        else:
            username = "anon"

        sql = upsert('imgmods', **{"imgid": self.uid, "username": username, "flag": 1})
        result = doquery(sql)

######### Item stuff

class NoItem(Exception):
    def __init__(self, item):
        Exception.__init__(self, item)

class __siteitem__:
    def __init__(self):
        self.name = ""
        self.have = 0
        self.want = 0
        self.willtrade = 0
        self.hidden = 0

class siteitem(__siteitem__):
    def __init__(self, name):
        self.name = name
        self.images = []
        self.haveusers = []
        self.wantusers = []
        self.willtradeusers = []

        sql = read('items', **{"name": name})
        result = doquery(sql)

        try:
            self.uid = result[0][0]
            #self.name = result[0][1]
            self.description = result[0][2]
            self.added = result[0][3]
            self.modified = result[0][4]
        except IndexError:
            raise NoItem(name)

        sql = read('itemimg', **{"itemid": self.uid})
        result = doquery(sql)

        try:
            for itemimg in result:
                image = siteimage(itemimg[1])
                self.images.append(image)
        except IndexError:
            pass

        sql = read('ownwant', **{"itemid": self.uid, "own": "1"})
        res = doquery(sql)
        self.have = len(res)
        for user in res:
            sql = read('users', **{"uid": user[1]})
            result = doquery(sql)
            userinfo = siteuser(result[0][1])
            self.haveusers.append(userinfo)

        sql = read('ownwant', **{"itemid": self.uid, "want": "1"})
        res = doquery(sql)
        self.want = len(res)
        for user in res:
            sql = read('users', **{"uid": user[1]})
            result = doquery(sql)
            userinfo = siteuser(result[0][1])
            self.wantusers.append(userinfo)

        sql = read('ownwant', **{"itemid": self.uid, "willtrade": "1"})
        res = doquery(sql)
        self.willtrade = len(res)
        for user in res:
            sql = read('users', **{"uid": user[1]})
            result = doquery(sql)
            userinfo = siteuser(result[0][1])
            self.willtradeusers.append(userinfo)

    def delete(self):
        for i in self.images: 
            try: 
                os.remove(upload_dir + i.filename) 
     
                sql = delete('images', **{"uid": i.uid}) 
                result = doquery(sql) 
            except: 
                flash("Error removing image: " + i.filename) 
                app.logger.error("Error removing image: " + i.filename) 
     
        sql = delete('items', **{"uid": self.uid}) 
        result = doquery(sql) 
     
        sql = delete('itemimg', **{"itemid": self.uid}) 
        result = doquery(sql) 
     
        sql = delete('ownwant', **{"itemid": self.uid}) 
        result = doquery(sql) 
     

    def newimg(self, f, tag):
        if not f.filename == '':
            fuuid = uuid.uuid4().get_hex()
            try:
                newname = fuuid + os.path.splitext(f.filename)[1]
                f.save(upload_dir + newname)
            except Exception as e:
                raise

            if imghdr.what(upload_dir + newname):
                sql = upsert("images", \
                             uid=0, \
                             filename=newname, \
                             tag=escape(tag))
                imgid = doupsert(sql)

                sql = upsert("itemimg", \
                             imgid=imgid, \
                             itemid=self.uid)
                data = doupsert(sql)

                try:
                    username = session['username']
                except KeyError:
                    username = "anon"

                sql = upsert("imgmods", \
                             username=username, \
                             imgid=imgid)
                data = doupsert(sql)

                flash('Uploaded ' + f.filename)
            else:
                try:
                    os.remove(upload_dir + newname)
                except:
                    app.logger.error("Error removing failed image upload: " + upload_dir + newname)

                flash(f.filename + " is not an image.")

def new_item(name, description, username):
    sql = upsert("items", \
                 uid=0, \
                 name=name, \
                 description=description, \
                 added=datetime.datetime.now(), \
                 modified=datetime.datetime.now())

    data = doupsert(sql)

def all_items():
    items = []

    try:
        sql = read('items')
        result = doquery(sql)

        for item in result:
            newitem = __siteitem__()
            newitem.uid = item[0]
            newitem.name = item[1]
            newitem.description = item[2]
            newitem.added = item[3]
            newitem.modified = item[4]

            items.append(newitem)
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


