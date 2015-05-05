import os
import uuid
import datetime
import re
from scarf import app
from flask import redirect, url_for, render_template, session, escape, request, flash
from scarflib import redirect_back, pagedata, siteuser, NoUser
from sql import doupsert, upsert, doselect, read
from main import page_not_found

@app.route('/userupdate')
def userupdate():
    pd = pagedata()
    if 'username' in session:
        pd.title = title="Update User Account"
        return render_template('userupdate.html', pd=pd)

    return redirect(url_for('index'))

@app.route('/emailupdate', methods=['GET', 'POST'])
def emailupdate():
    pd = pagedata()
    if 'username' in session:
        if request.method == 'POST':
            try:
                user = siteuser(session['username'])
            except NoUser:
                return render_template('error.html', pd=pd)

            try:
                user.authenticate(request.form['password'])
            except AuthFail:
                flash("Please check your current password and try again")
                return redirect(url_for('userupdate'))

            email = escape(request.form['email'])

            if not re.match("[^@]+@[^@]+\.[^@]+", escape(request.form['email'])):
                flash("Invalid email address")
                return redirect(url_for('userupdate'))

            user.newemail(email)

            flash("Your email address has been changed.")
            return redirect(url_for('userupdate'))

    return redirect(url_for('index'))
 
@app.route('/pwreset', methods=['GET', 'POST'])
def pwreset():
    pd = pagedata()
    if 'username' in session:
        ret = False
        if request.method == 'POST':
            try:
                user = siteuser(session['username'])
            except NoUser:
                return render_template('error.html', pd=pd)

            try:
                user.authenticate(request.form['password'])
            except AuthFail:
                flash("Please check your current password and try again")
                return redirect(url_for('userupdate'))

            pass1 = escape(request.form['newpassword'])
            pass2 = escape(request.form['newpassword2'])

            if pass1 != pass2:
                flash("The passwords entered don't match.")
                ret = True

            if len(pass1) < 6:
                flash("Your new password is too short, it must be at least 6 characters")
                ret = True

            if ret:
                return redirect_back(url_for('userupdate'))

            user.newpassword(escape(request.form['newpassword']))

            flash("Your password has been reset.")
            return redirect(url_for('userupdate'))

    return redirect(url_for('index'))

@app.route('/user/<username>')
def show_user_profile(username):
    pd = pagedata()
    pd.scarves = []
    pd.title = "Profile for " + escape(username)

    try:
        pd.profileuser = siteuser(escape(username))
        pd.profileuser.collection = pd.profileuser.get_collection()
    except NoUser:
        return page_not_found(404)

    return render_template('profile.html', pd=pd)
