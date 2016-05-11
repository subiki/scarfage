# -*- coding: utf-8 -*-
import base64
import logging
import datetime
import os, sys

import core
import config
from scarf import app
from flask import render_template, session, request, flash
from core import redirect_back
from nocache import nocache

if 'LOGFILE' in config.__dict__:
    logging.basicConfig(filename=config.LOGFILE,level=logging.INFO)

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

class PageData(object):
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

        if 'username' in session:
            try:
                self.authuser = core.SiteUser.create(session['username'])
            except core.NoUser:
                self.authuser = None
                pass

@app.errorhandler(404)
def page_not_found(error):
    pd = PageData()
    logger.error('404! Referrer was: ' + str(request.referrer))
    pd.title = "File not found"
    pd.errorcode="404"
    pd.errortext="File not found."
    return render_template('error.html', pd=pd), 404

@app.errorhandler(500)
def own_goal(error):
    pd = PageData()
    logger.error('500! Referrer was: ' + str(request.referrer))
    pd.title = "Oh noes!"
    pd.errorcode="500"
    pd.errortext="(╯°□°）╯︵ ┻━┻"
    return render_template('error.html', pd=pd), 500

@app.route('/upload_error')
def upload_error():
    flash('Your upload is too large, please resize it to be smaller than 10 MB and try again.')
    return redirect_back('error')

@app.route('/error')
def error():
    pd = PageData()
    pd.title = "Error!"
    pd.errortext="Oh noes!!"
    return render_template('error.html', pd=pd)

@app.route('/accessdenied')
def accessdenied():
    pd = PageData()
    pd.title = "Access Denied"
    pd.errortext = "Access Denied"
    return render_template('error.html', pd=pd), 403

@app.route('/')
@nocache
def index():
    pd = PageData()
    pd.title = "Scarfage"

    pd.items = core.latest_items(10)

    return render_template('index.html', pd=pd)

@app.route('/ping')
@nocache
def ping():
    return "OK!"
