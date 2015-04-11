from scarf import app
from flask import request, session, redirect, url_for
from urlparse import urlparse, urljoin

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
