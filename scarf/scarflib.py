import datetime
from scarf import app
from flask import request, session, redirect, url_for, escape
from urlparse import urlparse, urljoin
from sql import upsert, doupsert, read, doselect

class pagedata:
    pass

def removeNonAscii(s): return "".join(i for i in s if ord(i)<128)

def check_login():
    if 'username' in session:
        return True
    else:
        return False

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
        return

def is_admin(user):
    accesslevel = get_userinfo(user)[0][8]

    if accesslevel == 255:
       return True

    return False
