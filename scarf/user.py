import os
import uuid
import hashlib
import datetime
import re
from scarf import app
from flask import redirect, url_for, render_template, session, escape, request, flash
from scarflib import check_login, redirect_back, hit_lastseen, pagedata
from sql import doupsert, upsert, doselect, read


#TODO change me
app.secret_key = '\x8bN\xe5\xe8Q~p\xbdb\xe5\xa5\x894i\xb0\xd9\x07\x10\xe6\xa0\xe5\xbd\x1e\xf8'

class suser:
    def __init__(self, username):
        self.auth = False
        self.username = username
        self.collection = []

        sql = read('users', **{"username": user})
        result = doselect(sql)

        try:
            self.uid = result[0][0]
            self.pwhash = result[0][2]
            self.pwsalt = result[0][3]
            self.lastseen = result[0]#FIXME
            self.numadds = result[0][7]
            self.accesslevel = result[0][8]
        except:
            pass
            #return
            # TODO: throw nouser exception

        # Update lastseen if we're looking up the currently logged in user
        if 'username' in session:
            if session['username'] is username:
                self.seen()

    def writedb(self):
        try:
            sql = upsert("users", \
                         uid=self.uid, \
                         pwhash=self.pwhash,
                         pwsalt=self.pwsalt,
                         lastseen=self.lastseen) # TODO add the rest
            data = doupsert(sql)
        except:
            pass
            #TODO check for sql exceptions

    def seen(self):
        self.lastseen=datetime.datetime.now())
        self.writedb()
        # Update last seen column in user table

    def authenticate(self, password):
        if self.accesslevel == 0:
            flash('Your account has been banned')
        else:
            checkhash = gen_pwhash(password, self.pwsalt)

            if checkhash == self.pwhash:
                self.seen()
                self.auth = True

    def incadds(self):
        self.numadds=self.numadds+1
        self.writedb()

    def delete(self):
        sql = delete('users', **{"uid": self.uid})
        result = doselect(sql)

        sql = delete('ownwant', **{"userid": self.uid})
        result = doselect(sql)
    except IndexError:
        pass
        #TODO: throw SQLError

def gen_pwhash(password, salt):
    return hashlib.sha224(password + salt).hexdigest()

def check_new_user(request):
    ret = True
    try:
        user = suser(escape(request.form['username']))
        flash("User already exists")
        ret = False
    #FIXME this exception isn't thrown yet
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
    if check_login():
        return redirect(url_for('index'))

    if request.method == 'POST':
        auth = check_pw(escape(request.form['username']), escape(request.form['password']))

        if not auth:
            flash('Login unsuccessful.')
            return redirect(url_for('index'))
        else:
            sql = upsert("users", \
                         uid=auth, \
                         lastseen=datetime.datetime.now())
            data = doupsert(sql)

            session['username'] = escape(request.form['username'])
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
                # TODO, re-fill form
                return render_template('newuser.html', pd=pd)

            salt=str(uuid.uuid4().get_hex().upper()[0:6])
            sql = upsert("users", \
                         uid=0, \
                         username=escape(request.form['username']), \
                         pwhash=gen_pwhash(escape(request.form['password']), salt), \
                         pwsalt=salt, \
                         email=escape(request.form['email']), \
                         joined=datetime.datetime.now(), \
                         lastseen=datetime.datetime.now(), \
                         numadds=0, \
                         accesslevel=1)
            data = doupsert(sql)
            if not data:
#TODO fix for pd object
                return render_template('error.html', errortext="SQL error")

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
