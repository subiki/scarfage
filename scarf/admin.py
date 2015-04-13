from scarf import app
from flask import redirect, url_for, render_template, session, escape, request, flash
from scarflib import check_login, redirect_back, hit_lastseen, pagedata, get_userinfo, is_admin
from sql import doupsert, upsert, doselect, read

def get_users():
    sql = read('users')
    result = doselect(sql)

    try:
        uid = result[0][0]
        return result
    except: 
        return []

@app.route('/admin/users')
def admin_users():
    pd = pagedata()

    if 'username' not in session:
        return redirect(url_for('accessdenied'))

    if not pd.accesslevel == 255:
        return redirect(url_for('accessdenied'))

    pd.title = "Admin - User List" 

    pd.users = get_users()

    return render_template('admin_users.html', pd=pd)

@app.route('/admin/users/<user>/accesslevel/<level>')
def admin_ban_user(user, level):
    pd = pagedata()

    if 'username' not in session:
        return redirect(url_for('accessdenied'))

    if not pd.accesslevel == 255:
        return redirect(url_for('accessdenied'))

    try:
        uid = get_userinfo(escape(user))[0][0]
    except:
        return render_template('error.html', errortext="SQL error")

    sql = upsert("users", \
                 uid=uid, \
                 accesslevel=level)
    data = doupsert(sql)

    return redirect_back('/admin/users')
