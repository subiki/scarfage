import os
import uuid
import datetime
from scarf import app
from flask import redirect, url_for, render_template, session, escape, request, flash
from scarflib import check_login, redirect_back
from sql import doupsert, upsert, doselect, read

def get_userinfo(user):
    sql = read('users', **{"username": user})
    result = doselect(sql)

    try:
        return result
    except:
        return

@app.route('/pwreset')
def pwreset():
    if 'username' in session:
        return render_template('pwreset.html', user=escape(session['username']), title="Reset Password")
    else:
        return redirect(url_for('index'))

@app.route('/user/<username>')
def show_user_profile(username):
    userinfo = get_userinfo(escape(username))
    try:
        uid = userinfo[0][1]
    except:
         return render_template('error.html', errortext="SQL error")

    if 'username' in session:
        return render_template('profile.html', user=escape(session['username']), userinfo=userinfo[0], title="Profile for " + escape(username))
    else:
        return render_template('profile.html', userinfo=userinfo[0], title="Profile for " + escape(username))
