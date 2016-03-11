# -*- coding: utf-8 -*-
import base64

import core
from scarf import app
from flask import render_template, session, request, flash
from core import redirect_back
from nocache import nocache

class PageData(object):
    pass

    def __init__(self):
        try:
            self.prefix = prefix
        except NameError:
            self.prefix = ''

        self.accesslevels = core.accesslevels

        self.encode = base64.b32encode
        self.decode = base64.b32decode

        self.uid_by_user = core.uid_by_user
        self.user_by_uid = core.user_by_uid

        if 'username' in session:
            try:
                self.authuser = core.SiteUser.create(session['username'])
            except:
                self.authuser = None
                pass

@app.errorhandler(404)
def page_not_found(error):
    pd = PageData()
    app.logger.error('404! Referrer was: ' + str(request.referrer))
    pd.title = "File not found"
    pd.errorcode="404"
    pd.errortext="File not found."
    return render_template('error.html', pd=pd), 404

@app.errorhandler(500)
def own_goal(error):
    pd = PageData()
    app.logger.error('500! Referrer was: ' + str(request.referrer))
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

    pd.items = core.latest_items(50)

    return render_template('index.html', pd=pd)
