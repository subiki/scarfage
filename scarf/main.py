# -*- coding: utf-8 -*-
import base64
import logging
import datetime
import bleach
import os, sys
from pytz import timezone

import core
import config
import markdown
from scarf import app
from flask import render_template, session, request, flash, send_from_directory
from core import redirect_back
from nocache import nocache

md_extensions = ['markdown.extensions.extra', 'markdown.extensions.nl2br', 'markdown.extensions.sane_lists']

if 'LOGFILE' in config.__dict__:
    logging.basicConfig(filename=config.LOGFILE,level=logging.INFO)

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

def handle_exception(exc_type, exc_value, exc_traceback):
    """
    Log exceptions
    """

    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

class PageData(object):
    """
    Convenience object to make various objects and functions available to the template. 

    :Attributes:
       * prefix          - URL prefix for static content
       * accesslevels    - core.accesslevels
       * authuser        - core.SiteUser.create(session['username'])
       * encode()        - base64.b32encode()
       * decode()        - base64.b32decode()
       * escape_html     - core.escape_html()
       * obfuscate       - core.obfuscate()
       * deobfuscate     - core.deobfuscate()
       * uid_by_user     - core.uid_by_user()
       * user_by_uid     - core.user_by_uid()
       * uid_by_item     - core.uid_by_item()
       * item_by_uid     - core.item_by_uid()
       * render_markdown - render_markdown()

    """
    def __init__(self):
        try:
            self.prefix = config.PREFIX
        except NameError:
            self.prefix = ''

        self.accesslevels = core.accesslevels

        self.encode = base64.b32encode
        self.decode = base64.b32decode

        self.escape_html = core.escape_html
        self.obfuscate = core.obfuscate
        self.deobfuscate = core.deobfuscate
        self.uid_by_user = core.uid_by_user
        self.user_by_uid = core.user_by_uid
        self.uid_by_item = core.uid_by_item
        self.item_by_uid = core.item_by_uid
        self.render_markdown = render_markdown

        if 'username' in session:
            try:
                self.authuser = core.SiteUser.create(session['username'])
                self.authuser.seen()
            except core.NoUser:
                del session['username']

    def localtime(self, timestamp):
        """
        Convert a timestamp into the user's local timezone

        :param timestamp: Datetime object to convert
        :return: Datetime object in local time
        """
        utc = timezone('UTC')
        utc_dt = utc.localize(timestamp)

        if 'username' in session:
            user_tz = timezone(self.authuser.profile().profile['timezone'])
        else:
            user_tz = timezone('America/Los_Angeles')

        return utc_dt.astimezone(user_tz)

def render_markdown(string):
    """
    Escapes the HTML in a string, renders any markdown present, then linkifys all bare URLs.

    :param string: string to process
    :return: rendered string
    """
    return bleach.linkify(markdown.markdown(core.escape_html(unicode(string)), md_extensions))

def request_wants_json():
    """
    Check the request to see if the client wants JSON instead of rendered HTML

    :return: True or False
    """
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']

@app.errorhandler(404)
def page_not_found(error=None):
    """
    Error handler for 404 errors

    :param error: The error that occurred 
    :return: A rendered 404 page
    """

    print error
    pd = PageData()
    logger.error('404! Referrer was: ' + str(request.referrer))
    pd.title = "File not found"
    pd.errorcode="404"
    pd.errortext="Not the scarf you're looking for..."
    return render_template('error.html', pd=pd), 404

@app.errorhandler(500)
def own_goal(error=None):
    """
    Error handler for 500 errors

    :param error: The error that occurred 
    :return: A rendered 500 page
    """
    pd = PageData()
    logger.error('500! Referrer was: {}, error is: {}'.format(str(request.referrer), error))
    pd.title = "Oh noes!"
    pd.errorcode="500"
    pd.errortext="(╯°□°）╯︵ ┻━┻"
    return render_template('error.html', pd=pd), 500

@app.route('/upload_error')
def upload_error():
    """
    :URL: /upload_error

    On the main site any over-size uploads will be redirected here.
    Flash a message to the user and attempt to redirect_back()
    """
    flash('Your upload is too large, please resize it and try again.')
    return redirect_back('error')

@app.route('/error')
def error():
    """
    :URL: /error

    Renders a generic non-500 error page
    """
    pd = PageData()
    pd.title = "Error!"
    pd.errortext="Oh noes!!"
    return render_template('error.html', pd=pd)

@app.route('/accessdenied')
def accessdenied():
    """
    :URL: /accessdenied

    Renders a generic access denied page
    """
 
    pd = PageData()
    pd.title = "Access Denied"
    pd.errortext = "Access Denied"
    return render_template('error.html', pd=pd), 403

@app.route('/robots.txt')
#@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

@app.route('/about')
def about():
    """
    :URL: /about

    About page
    """
    pd = PageData()
    pd.title = "Scarfage"

    return render_template('about.html', pd=pd)

@app.route('/')
@nocache
def index():
    """
    :URL: /

    The main site index
    """
    pd = PageData()
    pd.title = "Scarfage"

    pd.welcomebanner = core.SiteString('welcomebanner').string

    # TODO: remove this once reimplemented with JS. #81
    pd.items = core.latest_items(10)

    return render_template('index.html', pd=pd)

@app.route('/ping')
@nocache
def ping():
    """
    :URL: /ping
    
    Basic health check for the main site
    """

    return "OK!"
