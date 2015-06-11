import re
from scarf import app
from flask import redirect, url_for, render_template, session, escape, request, flash
from scarflib import redirect_back, pagedata, siteuser, NoUser, new_user, AuthFail

from config import secret_key
app.secret_key = secret_key

def check_new_user(request):
    ret = True
    try:
        user = siteuser.create(escape(request.form['username']))
        flash("User already exists")
        ret = False
    except NoUser:
        invalid = '[]{}\'"<>;/\\'
        for c in invalid:
            if c in request.form['username']:
                flash("Invalid character in username: " + c)
                ret = False

        pass1 = escape(request.form['password'])
        pass2 = escape(request.form['password2'])

        if pass1 != pass2:
            flash("The passwords entered don't match.")
            ret = False
        else:
            if len(pass1) < 6:
                flash("Your password is too short, it must be at least 6 characters")
                ret = False

        if not re.match("[^@]+@[^@]+\.[^@]+", escape(request.form['email'])):
            flash("Invalid email address")
            ret = False

    return ret

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            user = siteuser.create(escape(request.form['username']))
            user.authenticate(escape(request.form['password']))
        except (NoUser, AuthFail) as e:
            app.logger.warning("Failed login: " + e.args[0]) 
            flash('Login unsuccessful.')
            return redirect(url_for('index'))

        user.seen()

        session['username'] = user.username
        flash('You were successfully logged in')
        return redirect_back('index')

    return redirect(url_for('error'))

@app.route('/newuser', methods=['GET', 'POST'])
def newuser():
    pd = pagedata();
    pd.title = "New User"

    if 'username' in session:
        flash('Don\'t be greedy')
        return redirect(url_for('index'))
    else:
        if request.method == 'POST':
            if not check_new_user(request):
                pd.username = request.form['username']
                pd.email = request.form['email']
                return render_template('newuser.html', pd=pd)

            if not new_user(escape(request.form['username']), escape(request.form['password']), escape(request.form['email'])):
                return render_template('error.html', pd=pd)

            session['username'] = escape(request.form['username'])
            flash('Welcome ' + session['username'])
            return redirect(url_for('index'))

        return render_template('newuser.html', pd=pd)

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    flash('You were successfully logged out')
    return redirect_back('index')
