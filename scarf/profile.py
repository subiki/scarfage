import os
import uuid
import datetime
from scarf import app
from flask import redirect, url_for, render_template, session, escape, request, flash
from scarflib import check_login, redirect_back, pagedata, get_userinfo, is_admin
from sql import doupsert, upsert, doselect, read

@app.route('/pwreset')
def pwreset():
    if 'username' in session:
        pd = pagedata()
        pd.title = title="Reset Password"
        pd.user = session['username']
        pd.admin = is_admin(session['username'])
        return render_template('pwreset.html', pd=pd)
    else:
        return redirect(url_for('index'))

@app.route('/user/<username>')
def show_user_profile(username):
    pd = pagedata()
    pd.scarves = []
    pd.title = "Profile for " + escape(username)
    pd.admin = is_admin(username)

    userinfo = get_userinfo(escape(username))

    try:
        pd.userinfo=userinfo[0]
        uid = userinfo[0][0]

        sql = read('ownwant', **{"userid": uid})
        result = doselect(sql)
        try:
            for scarf in result:
                sql = read('scarves', **{"uuid": scarf[2]})
                sresult = doselect(sql)

                try:
                    pd.scarves.append({'name': sresult[0][2], 'own': scarf[3], 'willtrade': scarf[4], 'want': scarf[5], 'hidden': scarf[6]})
                except:
                    app.logger.debug('SQL error reading scarves table for profile')
        except: 
            app.logger.debug(result)
    except:
         return render_template('error.html', errortext="SQL error")

    if 'username' in session:
        pd.user = session['username']

    return render_template('profile.html', pd=pd)
