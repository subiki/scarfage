from scarf import app

from flask import Flask, abort, redirect, url_for, render_template, session, escape, request, flash

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] != 'admin' or \
                request.form['password'] != 'secret':
            flash('Login unsuccessful. Check your username and password and try again.')
            return redirect(url_for('index'))
        else:
            session['username'] = escape(request.form['username'])
            flash('You were successfully logged in')
            return redirect(url_for('index'))
    return redirect(url_for('error'))

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    flash('You were successfully logged out')
    return redirect(url_for('index'))

@app.route('/user/<username>')
def show_user_profile(username):
    # show the user profile for that user
    return 'User %s' % username
