from scarf import app
from flask import session, redirect, url_for

def removeNonAscii(s): return "".join(i for i in s if ord(i)<128)

def check_login():
    if 'username' in session:
        return True
    else:
        return False
