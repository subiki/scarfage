import os
import datetime
import imghdr
import uuid
from scarf import app
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
    accesslevels = {-1: 'anonymous', 0:'banned', 1:'user', 10:'moderator', 255:'admin'}
    pass

    def __init__(self):
        self.accesslevel = -1
        if 'username' in session:
            hit_lastseen(session['username'])
            self.user = session['username']
            self.accesslevel = get_accesslevel(session['username'])

def removeNonAscii(s): return "".join(i for i in s if ord(i)<128)

def check_login():
    if 'username' in session:
        return True
    else:
        return False

def get_accesslevel(user):
    return get_userinfo(user)[0][8]

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
    except:
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
    except:
        return scarfimgs

    return scarfimgs

def hit_lastseen(user):
    sql = read('users', **{"username": user})
    result = doselect(sql)

    try:
        uid = result[0][0]
    except: 
        return False

    sql = upsert("users", \
                 uid=uid, \
                 lastseen=datetime.datetime.now())
    data = doupsert(sql)

def get_userinfo(user):
    sql = read('users', **{"username": user})
    result = doselect(sql)

    try:
        return result
    except:
        flash('no user')
        return

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

            sql = upsert("imgmods", \
                         username=session['username'], \
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
