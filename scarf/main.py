# -*- coding: utf-8 -*-
from scarf import app
from flask import render_template, session, request, flash
from sql import doquery, read
from scarflib import pagedata, latest_items, get_whores_table, get_contribs_table, get_needy_table, get_willtrade_table
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

    pd.topcollectors = get_whores_table()
    pd.topcontributors = get_contribs_table()
    pd.topneedy = get_needy_table()
    pd.topwilltrade = get_willtrade_table()
    pd.items = latest_items(50)

    return render_template('index.html', pd=pd)
