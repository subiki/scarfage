from scarf import app
from flask import redirect, url_for, render_template, session, escape, request, flash
from scarflib import redirect_back, pagedata, NoUser, siteuser
from sql import read, doselect

def get_users():
    sql = read('users')
    result = doselect(sql)

    app.logger.debug(result)
    users = []

    for user in result:
        app.logger.debug(user[1])
        users.append(siteuser(user[1]))

    return users
@app.route('/admin')
def admin_users():
    pd = pagedata()

    if 'username' not in session or pd.authuser.accesslevel < 255:
        return redirect(url_for('accessdenied'))

    pd.title = "Admin" 

    pd.users = get_users()

    return render_template('admin.html', pd=pd)

@app.route('/admin/users/<user>/reallydelete')
def admin_reallydelete_user(user):
    pd = pagedata()

    if 'username' not in session or pd.authuser.accesslevel < 255:
        return redirect(url_for('accessdenied'))

    if session['username'] == pd.authuser.username:
        return redirect(url_for('accessdenied'))

    try:
        deluser = siteuser(escape(user))
        deluser.delete()

        flash('Deleted user: ' + user)
    except:
        flash('Error deleting user: ' + user)

    return redirect('/admin')

@app.route('/admin/users/<user>/delete')
def admin_delete_user(user):
    pd = pagedata()

    if 'username' not in session or pd.authuser.accesslevel < 255:
        return redirect(url_for('accessdenied'))

    pd.title="Deleting user " + escape(user)

    pd.accessreq = 255
    pd.conftext = "Deleting user " + escape(user)
    pd.conftarget = "/admin/users/" + escape(user) + "/reallydelete"
    pd.conflinktext = "Yup, I'm sure"

    return render_template('confirm.html', pd=pd)

@app.route('/admin/users/<user>/accesslevel/<level>')
def admin_set_accesslevel(user, level):
    pd = pagedata()

    if 'username' not in session or pd.authuser.accesslevel < 10:
        return redirect(url_for('accessdenied'))

    if session['username'] == user:
        flash("WTF, you can't edit your own permissions!")
        return redirect_back('index')

    if pd.authuser.accesslevel != 255 and pd.authuser.accesslevel <= level:
        flash("No.")
        return redirect_back('index')

    try:
        moduser = siteuser(escape(user))

    except NoUser:
        pd.title = "User does not exist"
        pd.errortext = "The user does not exist"
        return render_template('error.html', pd=pd)

    if pd.authuser.accesslevel != 255 and moduser.accesslevel >= pd.authuser.accesslevel:
        flash("Please contact an admin to modify this user's account.")
        return redirect_back('index')

    moduser.newaccesslevel(escape(level))
    flash('User ' + user + '\'s accesslevel has been set to ' + level)

    return redirect_back('/admin')
