from scarf import app
from flask import redirect, url_for, render_template, session, request, flash
from core import redirect_back, PageData, NoUser, SiteUser
from sql import read, doquery
from debug import dbg
import os.path, time
import jsonpickle
import config as sf_conf

from config import dep_file
from access import check_mod, check_admin

def get_users():
    sql = read('users')
    result = doquery(sql)

    users = []

    for user in result:
        users.append(SiteUser.create(user[1]))

    return users

@app.route('/admin/debug', defaults={'debug': True})
@app.route('/admin', defaults={'debug': False})
@check_admin
def admin_users(debug):
    pd = PageData()
    pd.sf_conf = sf_conf

    pd.title = "Admin" 

    pd.users = get_users()
    try:
        with open(sf_conf.dep_file, 'r') as depfile:
            frozen = depfile.read()
        pd.deployment = jsonpickle.decode(frozen)
        pd.mode = 'prod'
    except (OSError, IOError):
        pd.mode = "dev"

    if debug:
        pd.debug = dbg(pd)

    return render_template('admin.html', pd=pd)

@app.route('/admin/users/<user>/accesslevel/<level>')
@check_mod
def admin_set_accesslevel(user, level):
    pd = PageData()

    if pd.authuser.accesslevel != 255 and pd.authuser.accesslevel <= level:
        app.logger.error('Accesslevel change was denied for user: ' + pd.authuser.username)
        flash("Access level change denied.")
        return redirect_back('index')

    if pd.authuser.accesslevel != 255 and moduser.accesslevel >= pd.authuser.accesslevel:
        flash("Please contact an admin to modify this user's account.")
        return redirect_back('index')

    try:
        moduser = SiteUser.create(user)
    except NoUser:
        app.logger.error('Accesslevel change attempted for invalid user by: ' + pd.authuser.username)
        pd.title = "User does not exist"
        pd.errortext = "The user does not exist"
        return render_template('error.html', pd=pd)

    moduser.newaccesslevel(level)
    app.logger.info('Accesslevel change for ' + user)
    flash('User ' + user + '\'s accesslevel has been set to ' + level)

    return redirect_back('/admin')

@app.route('/admin/users/<user>/resetpw')
@check_admin
def admin_reset_pw(user):
    pd = PageData()

    try:
        user = SiteUser.create(user)
        user.forgot_pw_reset(admin=True)
    except NoUser:
        return page_not_found(404)

    flash('A new password has been e-mailed to ' + user.username + '.')

    return redirect_back('/admin')
