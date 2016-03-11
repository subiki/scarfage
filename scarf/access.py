from functools import wraps
from flask import redirect, url_for, session, flash

from main import PageData

def check_level(level):
    pd = PageData()
    if 'username' not in session or pd.authuser.accesslevel < level:
        return False
    else:
        return True

def check_admin(func):
    @wraps(func)
    def inner(*args, **kwargs): #1
        if not check_level(255):
            flash('You are not an admin')
            return redirect(url_for('accessdenied'))
        else:
            return func(*args, **kwargs) #
    return inner

def check_mod(func):
    @wraps(func)
    def inner(*args, **kwargs): #1
        if not check_level(10):
            flash('You are not a moderator')
            return redirect(url_for('accessdenied'))
        else:
            return func(*args, **kwargs) #
    return inner
