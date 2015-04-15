import os
import imghdr
import uuid
import re
import datetime
from scarf import app
from flask import redirect, url_for, request, render_template, session, escape, flash
from werkzeug import secure_filename
from scarflib import check_login
from sql import upsert, doupsert, read, doselect, delete
from profile import get_userinfo
from scarflib import redirect_back, check_scarf, scarf_imgs, pagedata, get_imgupload, upload_dir
from main import page_not_found

def inc_scarfcount(user):
    sql = read('users', **{"username": escape(user)})
    result = doselect(sql)

    try:
        uid = result[0][0]
        numadds = result[0][7]
    except IndexError: 
        return False

    numadds=numadds+1

    sql = upsert("users", \
                 uid=uid, \
                 numadds=numadds, \
                 lastseen=datetime.datetime.now())
    data = doupsert(sql)

@app.route('/scarf/')
def scarfroot():
    return redirect(url_for('index'))

@app.route('/scarf/<scarf_id>/reallydelete')
def reallydelete_scarf(scarf_id):
    scarf = check_scarf(escape(scarf_id))
    if scarf == False:
        return page_not_found(404)

    pd = pagedata()

    if not pd.accesslevel == 255:
        return redirect(url_for('accessdenied'))

    pd.title=escape(scarf_id) + " has been deleted"
    pd.scarfname=escape(scarf_id)
    pd.scarfimg=scarf_imgs(scarf[1])

    for i in pd.scarfimg:
        try:
            os.remove(upload_dir + i[0][2])

            sql = delete('images', **{"uuid": i[0][1]})
            result = doselect(sql)
        except:
            flash("Error removing image: " + i[0][2])
            app.logger.error("Error removing image: " + i[0][2])

    sql = delete('scarves', **{"uuid": scarf[1]})
    result = doselect(sql)

    sql = delete('scarfimg', **{"scarfid": scarf[1]})
    result = doselect(sql)

    sql = delete('ownwant', **{"scarfid": scarf[1]})
    result = doselect(sql)

    pd.accessreq = 255
    pd.conftext = pd.scarfname + " and its images have been deleted. I hope you meant to do that."
    pd.conftarget = ""
    pd.conflinktext = ""
    return render_template('confirm.html', pd=pd)

@app.route('/scarf/<scarf_id>/delete')
def delete_scarf(scarf_id):
    scarf = check_scarf(escape(scarf_id))
    if scarf == False:
        return page_not_found(404)

    pd = pagedata()

    if not pd.accesslevel == 255:
        return redirect(url_for('accessdenied'))

    pd.title=escape(scarf_id)
    pd.scarfname=escape(scarf_id)
    pd.scarfimg=scarf_imgs(scarf[1])
    pd.scarf = scarf

    pd.accessreq = 255
    pd.conftext = "Deleting scarf " + pd.scarfname
    pd.conftarget = "/scarf/" + pd.scarfname + "/reallydelete"
    pd.conflinktext = "Yup, I'm sure"

    return render_template('confirm.html', pd=pd)

@app.route('/scarf/<scarf_id>')
def show_scarf(scarf_id):
    scarf = check_scarf(escape(scarf_id))
    if scarf == False:
        return page_not_found(404)

    pd = pagedata()

    sql = read('ownwant', **{"scarfid": scarf[1], "own": "1"})
    res = doselect(sql)
    pd.have = len(res)
    pd.haveusers = []
    for user in res:
        sql = read('users', **{"uid": user[1]})
        res = doselect(sql)
        pd.haveusers.append(res[0][1])

    sql = read('ownwant', **{"scarfid": scarf[1], "want": "1"})
    res = doselect(sql)
    pd.want = len(res)
    pd.wantusers = []
    for user in res:
        sql = read('users', **{"uid": user[1]})
        res = doselect(sql)
        pd.wantusers.append(res[0][1])

    sql = read('ownwant', **{"scarfid": scarf[1], "willtrade": "1"})
    res = doselect(sql)
    pd.willtrade = len(res)
    pd.willtradeusers = []
    for user in res:
        sql = read('users', **{"uid": user[1]})
        res = doselect(sql)
        pd.willtradeusers.append(res[0][1])

    if check_login():
        userinfo = get_userinfo(session['username'])
        try:
            uid = userinfo[0][0]
        except IndexError:
            return render_template('error.html', errortext="SQL error")

        sql = read('ownwant', **{"userid": uid, "scarfid": scarf[1]})
        result = doselect(sql)

        try:
            iuid = result[0][0]
            pd.myscarfinfo = result[0]
        except IndexError:
            pd.myscarfinfo = []

    pd.title=scarf_id
    pd.scarfname=scarf_id
    pd.scarfimg=scarf_imgs(scarf[1])
    pd.scarf = scarf

    return render_template('scarf.html', pd=pd)

@app.route('/scarf/newscarf', methods=['GET', 'POST'])
def newscarf():
    pd = pagedata()
    if request.method == 'POST':
#        if not check_login():
#            flash('You must be logged in to create a scarf.')
#            return redirect(url_for('/newuser'))

        if request.form['name'] == '':
            flash('This scarf has no name?')
            return redirect('/scarf/newscarf')

        if request.form['name'] == 'newscarf':
            flash('Very funny')
            return redirect('/scarf/newscarf')

        invalid = '[]{}\'"<>;/\\'
        for c in invalid:
            if c in request.form['name']:
                flash("Invalid character in name: " + c)
                return redirect('/scarf/newscarf')

        if check_scarf(escape(request.form['name'])):
            flash('A scarf with that name already exists')
            return redirect('/scarf/newscarf')

        suuid=uuid.uuid4().get_hex()

        get_imgupload(request.files['front'], suuid, "front")
        get_imgupload(request.files['back'], suuid, "back")

        sql = upsert("scarves", \
                     uid=0, \
                     uuid=suuid, \
                     name=escape(request.form['name']), \
                     description=escape(request.form['desc']), \
                     added=datetime.datetime.now(), \
                     modified=datetime.datetime.now())

        data = doupsert(sql)
        if not data:
            pd.errortext="SQL error"
            return render_template('error.html', pd=pd)

        flash('Added scarf!')

        try:
            inc_scarfcount(session['username'])
        except KeyError:
            flash('Log in to add this scarf to your collection.')

        return redirect('/scarf/' + escape(request.form['name']))

    pd.title="Add New Scarf"

    return render_template('newscarf.html', pd=pd)
