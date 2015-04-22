import os
import uuid
import datetime
import re
from scarf import app
from flask import redirect, url_for, render_template, session, escape, request, flash
from scarflib import check_login, redirect_back, pagedata, get_userinfo
from sql import doupsert, upsert, doselect, read
from main import page_not_found
from user import check_pw, gen_pwhash

@app.route('/userupdate')
def userupdate():
    pd = pagedata()
    if 'username' in session:
        pd.title = title="Update User Account"
        return render_template('userupdate.html', pd=pd)

    return redirect(url_for('index'))

@app.route('/emailupdate', methods=['GET', 'POST'])
def emailupdate():
    pd = pagedata()
    if 'username' in session:
        if request.method == 'POST':
            userinfo = get_userinfo(escape(session['username']))

            try:
                pd.userinfo=userinfo[0]
                uid = userinfo[0][0]
            except IndexError:
                pd.title = "SQL Error"
                pd.errortext = "SQL Error"
                return render_template('error.html', pd=pd)

            ret = False
            if not check_pw(escape(session['username']), escape(request.form['password'])):
                flash("Please check your password and try again")
                ret = True

            email = escape(request.form['email'])

            if not re.match("[^@]+@[^@]+\.[^@]+", escape(request.form['email'])):
                flash("Invalid email address")
                ret = True

            if ret:
                return redirect_back(url_for('userupdate'))

            sql = upsert("users", \
                         uid=uid, \
                         email=email)
            app.logger.debug(sql)

            data = doupsert(sql)

            flash("Your email address has been changed.")
            return redirect(url_for('userupdate'))

    return redirect(url_for('index'))


 
@app.route('/pwreset', methods=['GET', 'POST'])
def pwreset():
    pd = pagedata()
    if 'username' in session:
        if request.method == 'POST':
            userinfo = get_userinfo(escape(session['username']))

            try:
                pd.userinfo=userinfo[0]
                uid = userinfo[0][0]
            except IndexError:
                pd.title = "SQL Error"
                pd.errortext = "SQL Error"
                return render_template('error.html', pd=pd)

            ret = False
            if not check_pw(escape(session['username']), escape(request.form['password'])):
                flash("Please check your current password and try again")
                ret = True

            pass1 = escape(request.form['newpassword'])
            pass2 = escape(request.form['newpassword2'])

            if pass1 != pass2:
                flash("The passwords entered don't match.")
                ret = True

            if len(pass1) < 6:
                flash("Your new password is too short, it must be at least 6 characters")
                ret = True

            if ret:
                return redirect_back(url_for('userupdate'))

            salt=str(uuid.uuid4().get_hex().upper()[0:6])
            app.logger.debug(salt)

            app.logger.debug(request.form)
            pwhash=gen_pwhash(escape(request.form['newpassword']), salt)
            app.logger.debug(pwhash)

            sql = upsert("users", \
                         uid=uid, \
                         pwhash=pwhash, \
                         pwsalt=salt)
            app.logger.debug(sql)

            data = doupsert(sql)

            flash("Your password has been reset.")
            return redirect(url_for('userupdate'))

    return redirect(url_for('index'))

@app.route('/user/<username>')
def show_user_profile(username):
    pd = pagedata()
    pd.scarves = []
    pd.title = "Profile for " + escape(username)

    userinfo = get_userinfo(escape(username))

    try:
        pd.userinfo=userinfo[0]
        uid = userinfo[0][0]

        sql = read('ownwant', **{"userid": uid})
        result = doselect(sql)
        for scarf in result:
            sql = read('scarves', **{"uuid": scarf[2]})
            sresult = doselect(sql)

            try:
                pd.scarves.append({'name': sresult[0][2], 'own': scarf[3], 'willtrade': scarf[4], 'want': scarf[5], 'hidden': scarf[6]})
            except IndexError:
                app.logger.debug('SQL error reading scarves table for profile')
    except IndexError:
        return page_not_found(404)

    return render_template('profile.html', pd=pd)
