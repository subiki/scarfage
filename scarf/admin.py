import config
from scarf import app
from access import check_mod, check_admin
from core import redirect_back, NoUser, SiteUser, get_users, new_string, SiteString
from main import PageData

from flask import redirect, url_for, render_template, session, request, flash
import os.path, time
import jsonpickle

@app.route('/admin')
@check_admin
def admin_users():
    """
    :URL: /admin

    Render the admin.html template
    """
    pd = PageData()
    pd.sf_conf = config

    pd.title = "Admin" 

    pd.welcomebanner = SiteString('welcomebanner').string

    pd.users = get_users()
    try:
        with open(config.DEPFILE, 'r') as depfile:
            frozen = depfile.read()
        pd.deployment = jsonpickle.decode(frozen)
        pd.mode = 'prod'
    except (OSError, IOError):
        pd.mode = "dev"

    return render_template('admin.html', pd=pd)

@app.route('/admin/strings/edit', methods=['POST'])
@check_admin
def editstring():
    """
    :URL: /admin/strings/edit
    :Method: POST

    Update a SiteString object.

    .. todo:: Only supports the welcome banner right now... not very useful.

    """
    if request.method == 'POST':
        if 'text' in request.form:
            if request.form['text'] == '':
                return redirect_back('index')

            ss = SiteString('welcomebanner')
            ss.string = request.form['text']
            ss.update()

    return redirect_back('index')

@app.route('/admin/users/<user>/accesslevel/<level>')
@check_mod
def admin_set_accesslevel(user, level):
    """
    :URL: /admin/users/<user>/accesslevel/<level>

    Change a user's access level. The user requesting the access level change must be more privileged
    than the level they are setting. 

    Redirects back if there was an error, otherwise redirects to the user's profile.
    """
    pd = PageData()

    if pd.authuser.accesslevel != 255 and pd.authuser.accesslevel <= int(level):
        app.logger.error('Accesslevel change was denied for user: ' + pd.authuser.username)
        flash("Access level change denied.")
        return redirect_back('index')

    try:
        moduser = SiteUser.create(user)

        if pd.authuser.accesslevel != 255 and moduser.accesslevel >= pd.authuser.accesslevel:
            flash("Please contact an admin to modify this user's account.")
            return redirect_back('index')
    except NoUser:
        app.logger.error('Accesslevel change attempted for invalid user by: ' + pd.authuser.username)
        pd.title = "User does not exist"
        pd.errortext = "The user does not exist"
        return render_template('error.html', pd=pd)

    moduser.newaccesslevel(level)
    flash('User ' + user + '\'s accesslevel has been set to ' + level)

    return redirect_back('index')

@app.route('/admin/users/<user>/resetpw')
@check_admin
def admin_reset_pw(user):
    """
    :URL: /admin/users/<user>/resetpw

    Reset the password for a user. Must be an admin.
    """

    pd = PageData()

    try:
        user = SiteUser.create(user)
        user.forgot_pw_reset(ip='0.0.0.0', admin=True)
    except NoUser:
        return page_not_found()

    flash('A new password has been e-mailed to ' + user.username + '.')

    return redirect_back('/admin')
