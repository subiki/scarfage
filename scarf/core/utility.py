import bleach
import base64
from urlparse import urlparse, urljoin
from flask import request, redirect, url_for
from werkzeug.routing import BuildError

from mail import send_mail
from sql import doquery
from .. import config

def redirect_back(endpoint, **values):
    """
    Attempt to redirect back to the referrer. If redirect to the requester's referrer isn't possible 
    then attempt to redirect to the provided endpoint.
    """

    def is_safe_url(target):
        ref_url = urlparse(request.host_url)
        test_url = urlparse(urljoin(request.host_url, target))
        return test_url.scheme in ('http', 'https') and \
               ref_url.netloc == test_url.netloc

    target = request.referrer
    if not target or not is_safe_url(target):
        try:
            target = url_for(endpoint, **values)
        except BuildError:
            target = endpoint

    return redirect(target)

def escape_html(text):
    """
    Strip the naughty bits out of a string
    """

    return bleach.clean(text)

def xor_strings(s,t):
    """
    XOR two strings, used for obfuscation
    """

    return "".join(chr(ord(a)^ord(b)) for a,b in zip(s,t))

def obfuscate(string):
    """
    Obfuscate a string. Not secure. Modifying this value will change various generated URLs and break bookmarks.
    """

    try:
        return base64.b16encode(xor_strings('\xaa\x99\x95\x167\xd3\xe1A\xec\x92\xff\x9eR\xb8\xd9\xa85\xc8\xe2\x92$\xaf\xd7\x16', str(string))).lower()
    except TypeError:
        return None

def deobfuscate(string):
    """
    Deobfuscate a string generated with our crappy obfuscate function
    """

    try:
        return xor_strings('\xaa\x99\x95\x167\xd3\xe1A\xec\x92\xff\x9eR\xb8\xd9\xa85\xc8\xe2\x92$\xaf\xd7\x16', base64.b16decode(str(string.upper())))
    except TypeError:
        return None

def ip_uid(ip, readonly=False):
    """
    Get the UID of an IP from the ip table. Insert it if it doesn't have an entry.

    :param ip: 
    :param readonly: Set to True if the IP should only be checked (don't modify the ip table)
    :return: UID of the IP from the ip table
    """

    try:
        sql = "select uid from ip where ip = %(ip)s;"
        result = doquery(sql, { 'ip': ip })
        return result[0][0]
    except IndexError:
        if readonly:
            return None
        sql = "insert into ip (ip) values ( %(ip)s );"
        result = doquery(sql, { 'ip': ip })
        return ip_uid(ip, True)
