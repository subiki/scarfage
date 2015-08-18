# -*- coding: utf-8 -*-
from scarf import app
from flask import render_template, session, request, flash
from sql import doquery, read
from scarflib import pagedata, latest_items
from nocache import nocache

@app.errorhandler(404)
def page_not_found(error):
    pd = pagedata()
    pd.title = "File not found"
    pd.errorcode="404"
    pd.errortext="File not found."
    return render_template('error.html', pd=pd), 404

@app.errorhandler(500)
def page_not_found(error):
    pd = pagedata()
    pd.title = "Oh noes!"
    pd.errorcode="500"
    pd.errortext="(╯°□°）╯︵ ┻━┻"
    return render_template('error.html', pd=pd), 500

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

    pd.items = latest_items()

    return render_template('index.html', pd=pd)
