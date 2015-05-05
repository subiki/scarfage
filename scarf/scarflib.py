import hashlib

import os
import datetime
import imghdr
import uuid
from scarf import app
# TODO no flask stuff here besides escape and session
from flask import request, session, redirect, url_for, escape, flash
from urlparse import urlparse, urljoin
from sql import upsert, doupsert, read, doselect

# DEBUG
import socket 
if socket.gethostname() == "grenadine":
    upload_dir = '/home/pq/sf/site/scarf/static/uploads/'
else: 
    upload_dir = '/srv/data/web/vhosts/default/static/uploads/'

class pagedata:
    #FIXME put this somewhere else and inherit/copy it
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
        self.collection = []

        sql = read('users', **{"username": username})
        result = doselect(sql)

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
        except:
            raise NoUser(username)

        # Update lastseen if we're looking up the currently logged in user
        if 'username' in session:
            if session['username'] is username:
        #        self.seen()
                self.auth = True

    def __writedb__(self):
        try:
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
        except:
            pass
            #TODO check for sql exceptions

    def seen(self):
        self.lastseen=datetime.datetime.now()
        self.__writedb__()
        # Update last seen column in user table

    def authenticate(self, password):
        if self.accesslevel == 0:
            flash('Your account has been banned')
        else:
            checkhash = gen_pwhash(password, self.pwsalt)
        
            if checkhash == self.pwhash:
                session['username'] = self.username
            else:
                raise AuthFail

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
        result = doselect(sql) 
 
        sql = delete('ownwant', **{"userid": self.uid}) 
        result = doselect(sql)

def gen_pwhash(password, salt):
    return hashlib.sha224(password + salt).hexdigest()

def new_user(username, password, email):
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

    #TODO error checking
    return True

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

def check_scarf(name):
    sql = read('scarves', **{"name": escape(name)})
    result = doselect(sql)

    try:
        return result[0]
    except IndexError:
        return False

def scarf_imgs(scarf_uid):
    sql = read('scarfimg', **{"scarfid": scarf_uid})
    result = doselect(sql)
    scarfimgs = []

    try:
        for scarfimg in result:
            sql = read('images', **{"uuid": scarfimg[1]})
            result = doselect(sql)
            scarfimgs.append(result)
    except IndexError:
        return scarfimgs

    return scarfimgs

def get_imgupload(f, scarfuid, tag):
    if not f.filename == '':
        fuuid = uuid.uuid4().get_hex()
        try:
            newname = fuuid + os.path.splitext(f.filename)[1]
            f.save(upload_dir + newname)
        except:
            flash('Failed to upload image: ' + f.filename)
            return False

        if imghdr.what(upload_dir + newname):
            sql = upsert("images", \
                         uid=0, \
                         uuid=fuuid, \
                         filename=newname, \
                         tag=escape(tag))
            data = doupsert(sql)

            sql = upsert("scarfimg", \
                         imgid=fuuid, \
                         scarfid=scarfuid)
            data = doupsert(sql)

            try:
                username = session['username']
            except KeyError:
                username = "anon"

            sql = upsert("imgmods", \
                         username=username, \
                         imgid=fuuid)
            data = doupsert(sql)

            flash('Uploaded ' + f.filename)
            return True
        else:
            try:
                os.remove(upload_dir + newname)
            except:
                app.logger.error("Error removing failed image upload: " + upload_dir + newname)
            flash(f.filename + " is not an image.")
        return False
