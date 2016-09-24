import re
import string
from scarf import app
from flask import redirect, url_for, render_template, session, request, flash
from core import redirect_back, SiteUser, NoUser, new_user, AuthFail, check_email
from main import PageData
import logging

import config
app.secret_key = config.SECRETKEY

logger = logging.getLogger(__name__)

def check_new_user(request):
    ret = True
    try:
        user = SiteUser.create(request.form['username'])
        flash("User already exists!")
        ret = False
    except NoUser:
        if check_email(request.form['email']):
            flash("You may not create multiple users with the same email address.")
            return False

        valid = string.ascii_letters + string.digits
        for c in request.form['username']:
            if c not in valid:
                flash("Invalid character in username: " + c)
                ret = False

        pass1 = request.form['password']
        pass2 = request.form['password2']

        if pass1 != pass2:
            flash("The passwords entered don't match.")
            ret = False
        else:
            if len(pass1) < 6:
                flash("Your password is too short, it must be at least 6 characters")
                ret = False

        if not re.match("[^@]+@[^@]+\.[^@]+", request.form['email']):
            flash("Invalid email address")
            ret = False

    return ret

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            user = SiteUser.create(request.form['username'])
        except NoUser as e:
            flash('Login unsuccessful.')
            return redirect(url_for('index'))

        try:
            user.authenticate(request.form['password'])
        except (NoUser, AuthFail) as e:
            if user.accesslevel is 0:
                flash('Your account has been banned')
            else:
                flash('Login unsuccessful.')
            return redirect(url_for('index'))

        user.seen()

        session['username'] = user.username
        flash('You were successfully logged in')
        return redirect_back('index')

    return redirect(url_for('error'))

@app.route('/newuser', methods=['GET', 'POST'])
def newuser():
    pd = PageData();
    pd.title = "New User"

    if 'username' in session:
        flash('You are already logged in.')
        return redirect(url_for('index'))
    else:
        if request.method == 'POST':
            if not check_new_user(request):
                pd.username = request.form['username']
                pd.email = request.form['email']
                return render_template('newuser.html', pd=pd)

            if not new_user(request.form['username'], request.form['password'], request.form['email'], request.remote_addr):
                return render_template('error.html', pd=pd)

            try:
                user = SiteUser.create(request.form['username'])
                user.authenticate(request.form['password'])
                session['username'] = user.username
            except (NoUser, AuthFail):
                return render_template('error.html', pd=pd)

            flash('Welcome ' + request.form['username'])
            return redirect(url_for('index'))

        return render_template('newuser.html', pd=pd)

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    flash('You were successfully logged out')
    return redirect_back('index')
