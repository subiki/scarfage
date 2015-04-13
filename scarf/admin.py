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
    pd.title = "Access Denied"
    pd.errortext = "Access Denied"

    if 'username' not in session:
        return render_template('error.html', pd=pd), 403

    if not is_admin(session['username']):
       return render_template('error.html', pd=pd), 403

    pd.title = "Admin - User List" 
    pd.user = session['username']
    pd.admin = 1

    pd.users = get_users()

    return render_template('admin_users.html', pd=pd)
