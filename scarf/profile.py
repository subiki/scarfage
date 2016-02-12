import re
from scarf import app
from flask import redirect, url_for, render_template, session, request, flash
from scarflib import redirect_back, pagedata, siteuser, NoUser, check_email
from main import page_not_found
from debug import dbg
from string import ascii_letters, digits
from mail import send_mail
import random

@app.route('/forgotpw', methods=['GET', 'POST'])
def userupdate():
    def forgot_pw_reset(userobj):
        newpw = ''.join([random.choice(ascii_letters + digits) for _ in range(12)])
        userobj.newpassword(newpw)

        message = render_template('email/pwreset.html', username=userobj.username, email=userobj.email, newpw=newpw, ip=request.environ['REMOTE_ADDR'])
        send_mail(recipient=userobj.email, subject='Password Reset', message=message)

    pd = pagedata()
    if request.method == 'POST':
        try:
            user = siteuser.create(request.form['username'])
            forgot_pw_reset(user)
        except NoUser:
            email_user = check_email(request.form['email'])
            if email_user:
                forgot_pw_reset(email_user)

        flash('A new password has been sent.')

    return render_template('forgotpw.html', pd=pd)

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
                return redirect('/user/' + user.username)

            email = request.form['email']

            if not re.match("[^@]+@[^@]+\.[^@]+", request.form['email']):
                flash("Invalid email address")
                return redirect('/user/' + user.username)

            user.newemail(email)

            flash("Your email address has been changed.")
            return redirect('/user/' + user.username)

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
                return redirect('/user/' + user.username)

            pass1 = request.form['newpassword']
            pass2 = request.form['newpassword2']

            if pass1 != pass2:
                flash("The passwords entered don't match.")
                ret = True

            if len(pass1) < 6:
                flash("Your new password is too short, it must be at least 6 characters")
                ret = True

            if ret:
                return redirect('/user/' + user.username)

            user.newpassword(request.form['newpassword'])

            flash("Your password has been reset.")
            return redirect('/user/' + user.username)

    return redirect(url_for('index'))

@app.route('/user/<username>/debug', defaults={'debug': True})
@app.route('/user/<username>', defaults={'debug': False})
def show_user_profile(username, debug):
    pd = pagedata()
    pd.title = "Profile for " + username

    try:
        pd.profileuser = siteuser.create(username)
    except NoUser:
        return page_not_found(404)

    if debug:
        if 'username' in session and pd.authuser.accesslevel == 255:
            pd.debug = dbg(pd)

    return render_template('profile.html', pd=pd)
