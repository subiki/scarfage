from functools import wraps
from flask import redirect, url_for, session, flash
import logging

from main import PageData

logger = logging.getLogger(__name__)

def check_level(level):
    """
    Function to check the user's access level

    :param level: Minimum level to allow access
    :return: True or False
    """

    pd = PageData()
    if 'username' not in session:
        logger.info('check_level failed: no session')
        return False

    if pd.authuser.accesslevel < level:
        logger.info('check_level failed for {}: {} < {}'.format(session['username'], pd.authuser.accesslevel, level))
        return False
    else:
        logger.info('check_level succeeded for {} ({}): {}'.format(session['username'], pd.authuser.accesslevel, level))
        return True

def check_admin(func):
    """
    Decorator to check if the user is an admin and redirect to the access denied page if they aren't
    """

    @wraps(func)
    def inner(*args, **kwargs): #1
        if not check_level(255):
            flash('You are not an admin')
            return redirect(url_for('accessdenied'))
        else:
            return func(*args, **kwargs) #
    return inner

def check_mod(func):
    """
    Decorator to check if the user is a moderator and redirect to the access denied page if they aren't
    """

    @wraps(func)
    def inner(*args, **kwargs): #1
        if not check_level(10):
            flash('You are not a moderator')
            return redirect(url_for('accessdenied'))
        else:
            return func(*args, **kwargs) #
    return inner
