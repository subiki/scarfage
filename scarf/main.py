from scarf import app
from flask import render_template, session, escape, request, flash
from sql import doselect, read
from scarflib import hit_lastseen, pagedata, is_admin


@app.errorhandler(404)
def page_not_found(error):
    pd = pagedata()
    pd.title = "File not found"
    pd.errorcode="404"
    pd.errortext="File not found."
    return render_template('error.html', pd=pd), 404

@app.route('/error')
def error():
    pd = pagedata()
    pd.title = "Error!"
    pd.errortext="Oh noes!"
    return render_template('error.html', pd=pd)

@app.route('/accessdenied')
def accessdenied():
    pd = pagedata()
    pd.title = "Access Denied"
    pd.errortext = "Access Denied"
    return render_template('error.html', pd=pd), 403

@app.route('/')
def index():
    pd = pagedata()
    pd.load()
    pd.title = "Scarfage"

    sql = read('scarves')
    result = doselect(sql)

    try:
        pd.scarves = result
    except: 
        pd.scarves = []

    return render_template('index.html', pd=pd)
