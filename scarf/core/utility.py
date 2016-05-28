import bleach
import base64
from urlparse import urlparse, urljoin
from flask import request, redirect, url_for
from werkzeug.routing import BuildError

from mail import send_mail
from sql import doquery
from .. import config

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

def redirect_back(endpoint, **values):
    target = request.referrer
    if not target or not is_safe_url(target):
        try:
            target = url_for(endpoint, **values)
        except BuildError:
            target = endpoint

    return redirect(target)

def escape_html(text):
    """
    Strip the naughty bits out of a string and turn URLs into links while we're at it
    """
    return bleach.linkify(bleach.clean(text))

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
        return ip_uid(ip, True)
