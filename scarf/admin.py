from scarf import app
from flask import redirect, url_for, render_template, session, escape, request, flash
from scarflib import check_login, redirect_back, hit_lastseen, pagedata, get_userinfo, is_admin
from sql import doupsert, upsert, doselect, read

accesslevels = {0:'banned', 1:'user', 10:'moderator', 255:'admin'}

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

    if not is_admin(session['username']):
        return redirect(url_for('accessdenied'))

    pd.title = "Admin - User List" 
    pd.user = session['username']
    pd.admin = 1

    pd.users = get_users()
    pd.accesslevels = accesslevels

    return render_template('admin_users.html', pd=pd)
