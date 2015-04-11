import os
import uuid
import hashlib
from scarf import app
from flask import redirect, url_for, render_template, session, escape, request, flash
from scarflib import check_login, redirect_back
from sql import insert, upsert, select

#TODO change me
app.secret_key = '\x8bN\xe5\xe8Q~p\xbdb\xe5\xa5\x894i\xb0\xd9\x07\x10\xe6\xa0\xe5\xbd\x1e\xf8'

def gen_pwhash(password, salt):
    return hashlib.sha224(password + salt).hexdigest()

def check_pw(user, password):
    sql = 'SELECT `username`, `pwhash`, `pwsalt` FROM `users` WHERE username = `' + user + '`;'
    data = select(sql)
    app.logger.debug(data)

    return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    if check_login():
        return redirect(url_for('index'))

    if request.method == 'POST':
        auth = check_pw(escape(request.form['username']), escape(request.form['password']))

        if not auth:
            flash('Login unsuccessful. Check your username and password and try again.')
            return redirect(url_for('index'))
        else:
            session['username'] = escape(request.form['username'])
            flash('You were successfully logged in')
            return redirect_back('index')
    return redirect(url_for('error'))

@app.route('/newuser', methods=['GET', 'POST'])
def newuser():
    try:
        if session['username'] != "":
            flash('Don\'t be greedy')
            return redirect(url_for('index'))
    except:
        if request.method == 'POST':
            flash('Creating user')
            salt=str(uuid.uuid4().get_hex().upper()[0:6])
            sql = upsert("users", \
                         uid=0, \
                         username=escape(request.form['username']), \
                         pwhash=gen_pwhash(request.form['password'], salt), \
                         pwsalt=salt, \
                         email=escape(request.form['email']), \
                         joined="2015-04-01", \
                         lastseen="2015-04-01", \
                         numadds=0, \
                         accesslevel=0)
            data = insert(sql)
            if not data:
                return render_template('error.html', errortext="SQL error")
            else:
                flash(data)

            session['username'] = escape(request.form['username'])
            return redirect(url_for('index'))

        return render_template('newuser.html', title="New User")

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    flash('You were successfully logged out')
    return redirect_back('index')

@app.route('/user/<username>')
def show_user_profile(username):
    # show the user profile for that user
    return 'User %s' % username
