# -*- coding: utf-8 -*-
from scarf import app
from flask import render_template, session, request, flash
from sql import doquery, read
from scarflib import pagedata, latest_items, redirect_back
from nocache import nocache

@app.errorhandler(404)
def page_not_found(error):
    pd = pagedata()
    app.logger.debug('404!')
    pd.title = "File not found"
    pd.errorcode="404"
    pd.errortext="File not found."
    return render_template('error.html', pd=pd), 404

@app.errorhandler(500)
def own_goal(error):
    pd = pagedata()
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
    pd = pagedata()
    pd.title = "Error!"
    pd.errortext="Oh noes!!"
    return render_template('error.html', pd=pd)

@app.route('/accessdenied')
def accessdenied():
    pd = pagedata()
    pd.title = "Access Denied"
    pd.errortext = "Access Denied"
    return render_template('error.html', pd=pd), 403

@app.route('/')
@nocache
def index():
    pd = pagedata()
    pd.title = "Scarfage"

    pd.items = latest_items(50)

    return render_template('index.html', pd=pd)
