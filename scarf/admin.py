from scarf import app
from flask import redirect, url_for, render_template, session, escape, request, flash
from scarflib import check_login, redirect_back, hit_lastseen, pagedata, get_userinfo, is_admin
from sql import doupsert, upsert, doselect, read, delete

def get_users():
    sql = read('users')
    result = doselect(sql)

    try:
        uid = result[0][0]
        return result
    except: 
        return []

@app.route('/admin')
def admin_users():
    pd = pagedata()

    if 'username' not in session or pd.accesslevel < 255:
        return redirect(url_for('accessdenied'))

    pd.title = "Admin" 

    pd.users = get_users()

    return render_template('admin.html', pd=pd)

@app.route('/admin/users/<user>/reallydelete')
def admin_reallydelete_user(user):
    pd = pagedata()

    if 'username' not in session or pd.accesslevel < 255:
        return redirect(url_for('accessdenied'))

    try:
        uid = get_userinfo(escape(user))[0][0]

        sql = delete('users', **{"uid": uid})
        result = doselect(sql)

        sql = delete('ownwant', **{"userid": uid})
        result = doselect(sql)
    except:
        pd.title = "SQL error"
        pd.errortext = "SQL error"
        return render_template('error.html', pd=pd)

    return redirect('/admin')

@app.route('/admin/users/<user>/delete')
def admin_delete_user(user):
    pd = pagedata()

    if 'username' not in session or pd.accesslevel < 255:
        return redirect(url_for('accessdenied'))

    pd.title="Deleting user " + escape(user)

    pd.accessreq = 255
    pd.conftext = "Deleting user " + escape(user)
    pd.conftarget = "/admin/users/" + escape(user) + "/reallydelete"
    pd.conflinktext = "Yup, I'm sure"

    return render_template('confirm.html', pd=pd)

@app.route('/admin/users/<user>/accesslevel/<level>')
def admin_ban_user(user, level):
    pd = pagedata()

    if 'username' not in session or pd.accesslevel < 255:
        return redirect(url_for('accessdenied'))

    try:
        uid = get_userinfo(escape(user))[0][0]
    except:
        return render_template('error.html', errortext="SQL error")

    sql = upsert("users", \
                 uid=uid, \
                 accesslevel=level)
    data = doupsert(sql)

    return redirect_back('/admin')
