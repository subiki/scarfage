import re
from scarf import app
from flask import redirect, url_for, render_template, session, request, flash
from scarflib import redirect_back, pagedata, siteuser, NoUser
from main import page_not_found
from debug import dbg

#TODO /user/<user>/<whatever>
@app.route('/userupdate')
def userupdate():
    pd = pagedata()
    if 'username' in session:
        pd.title = title="Update User Account"
        return render_template('userupdate.html', pd=pd)

    return redirect(url_for('index'))

#TODO /user/<user>/<whatever>
@app.route('/emailupdate', methods=['GET', 'POST'])
def emailupdate():
    pd = pagedata()
    if 'username' in session:
        if request.method == 'POST':
            try:
                user = siteuser.create(session['username'])
            except NoUser:
                return render_template('error.html', pd=pd)

            try:
                user.authenticate(request.form['password'])
            except AuthFail:
                flash("Please check your current password and try again")
                return redirect(url_for('userupdate'))

            email = request.form['email']

            if not re.match("[^@]+@[^@]+\.[^@]+", request.form['email']):
                flash("Invalid email address")
                return redirect(url_for('userupdate'))

            user.newemail(email)

            flash("Your email address has been changed.")
            return redirect(url_for('userupdate'))

    return redirect(url_for('index'))
 
#TODO /user/<user>/<whatever>
@app.route('/pwreset', methods=['GET', 'POST'])
def pwreset():
    pd = pagedata()
    if 'username' in session:
        ret = False
        if request.method == 'POST':
            try:
                user = siteuser.create(session['username'])
            except NoUser:
                return render_template('error.html', pd=pd)

            try:
                user.authenticate(request.form['password'])
            except AuthFail:
                flash("Please check your current password and try again")
                return redirect(url_for('userupdate'))

            pass1 = request.form['newpassword']
            pass2 = request.form['newpassword2']

            if pass1 != pass2:
                flash("The passwords entered don't match.")
                ret = True

            if len(pass1) < 6:
                flash("Your new password is too short, it must be at least 6 characters")
                ret = True

            if ret:
                return redirect_back(url_for('userupdate'))

            user.newpassword(request.form['newpassword'])

            flash("Your password has been reset.")
            return redirect(url_for('userupdate'))

    return redirect(url_for('index'))

@app.route('/user/<username>/debug', defaults={'debug': True})
@app.route('/user/<username>', defaults={'debug': False})
def show_user_profile(username, debug):
    pd = pagedata()
    pd.title = "Profile for " + username

    try:
        pd.profileuser = siteuser.create(username)
        pd.profileuser.pop_collection()
        pd.profileuser.pop_messages()
    except NoUser:
        return page_not_found(404)

    if debug:
        if 'username' in session and pd.authuser.accesslevel == 255:
            pd.debug = dbg(pd)

    return render_template('profile.html', pd=pd)
