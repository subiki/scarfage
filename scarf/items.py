from scarflib import pagedata, siteuser, NoUser, siteitem, NoItem, new_item

import os
import imghdr
import uuid
import re
import datetime
from scarf import app
from flask import redirect, url_for, request, render_template, session, escape, flash
from werkzeug import secure_filename

from scarflib import redirect_back
from main import page_not_found

@app.route('/scarf/')
def scarfroot():
    return redirect(url_for('index'))

@app.route('/scarf/<item_id>/reallydelete')
def reallydelete_item(item_id):
    try:
        delitem = siteitem(escape(item_id))
    except: #FIXME
        return page_not_found(404)

    pd = pagedata()

    if not pd.authuser.accesslevel == 255:
        return redirect(url_for('accessdenied'))

    pd.title=escape(item_id) + " has been deleted"

    delitem.delete()

    pd.accessreq = 255
    pd.conftext = delitem.name + " and its images have been deleted. I hope you meant to do that."
    pd.conftarget = ""
    pd.conflinktext = ""
    return render_template('confirm.html', pd=pd)

@app.route('/scarf/<item_id>/delete')
def delete_item(item_id):
    try:
        delitem = siteitem(escape(item_id))
    except: #FIXME
        return page_not_found(404)

    pd = pagedata()

    if not pd.authuser.accesslevel == 255:
        return redirect(url_for('accessdenied'))

    pd.title=escape(item_id)

    pd.accessreq = 255
    pd.conftext = "Deleting scarf " + delitem.name
    pd.conftarget = "/scarf/" + delitem.name + "/reallydelete"
    pd.conflinktext = "Yup, I'm sure"

    return render_template('confirm.html', pd=pd)

@app.route('/scarf/<item_id>')
def show_item(item_id):
    pd = pagedata()

    try:
        showitem = siteitem(escape(item_id))
    except NoItem:
        return page_not_found(404)

    if 'username' in session:
        try:
            user = siteuser(session['username'])
            pd.iteminfo = user.query_collection(showitem.name)
        except NoUser:
            pass

    pd.title = item_id
    pd.item = showitem

    return render_template('scarf.html', pd=pd)

@app.route('/new', methods=['GET', 'POST'])
def newscarf():
    pd = pagedata()
    if request.method == 'POST':
        if request.form['name'] == '':
            flash('No name?')
            return redirect(url_for('newscarf'))

        invalid = '[]{}\'"<>;/\\'
        for c in invalid:
            if c in request.form['name']:
                flash("Invalid character in name: " + c)
                return redirect(url_for('newscarf'))

        if 'username' in session:
            username = session['username']
        else:
            username = ""

        try:
            newitem = siteitem(escape(request.form['name']))
            flash('A scarf with that name already exists')
            return redirect(url_for('newscarf'))
        except: #FIXME NoItem
            new_item(escape(request.form['name']), escape(request.form['desc']), username)

        flash('Added scarf!')

        try:
            newitem = siteitem(escape(request.form['name']))
            newitem.newimg(request.files['front'], "front")
            newitem.newimg(request.files['back'], "back")
        except: #FIXME noitem
            flash('Error adding scarf!')
            return redirect(url_for('newscarf'))

        try:
            incuser = siteuser(username)
            incuser.incadd()
        except NoUser:
            flash('Log in to add this scarf to your collection.')

        return redirect('/scarf/' + escape(request.form['name']))

    pd.title="Add New Scarf"

    return render_template('newscarf.html', pd=pd)
