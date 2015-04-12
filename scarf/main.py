from scarf import app
from flask import render_template, session, escape, request, flash
from sql import doselect, read
from scarflib import hit_lastseen

@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html', title="File not found", errorcode="404", errortext="File not found."), 404

@app.route('/error')
def error():
    return render_template('error.html', title="Error!", errortext="Oh noes!")

@app.route('/')
def index():
    sql = read('scarves')
    result = doselect(sql)
    scarves = []

    try:
        for scarf in result:
            scarves.append(scarf)
    except: 
        flash('no scarves')

    if 'username' in session:
        hit_lastseen(escape(session['username']))
        return render_template('index.html', title="Scarfage", user=escape(session['username']), scarves=scarves)
    else:
        return render_template('index.html', title="Scarfage", scarves=scarves)
