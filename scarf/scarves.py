import os
import imghdr
import uuid
import re
import datetime
from scarf import app
from flask import redirect, url_for, request, render_template, session, escape, flash
from werkzeug import secure_filename
from scarflib import check_login, is_admin
from sql import upsert, doupsert, read, doselect, delete
from profile import get_userinfo
from scarflib import redirect_back, check_scarf, scarf_imgs, hit_lastseen, pagedata
from main import page_not_found

# DEBUG
import socket 
if socket.gethostname() == "grenadine":
    upload_dir = '/home/pq/sf/site/scarf/static/uploads/'
else: 
    upload_dir = '/srv/data/web/vhosts/default/static/uploads/'

def get_imgupload(f, scarfuid, tag):
    pd = pagedata()
    if not f.filename == '':
        fuuid = uuid.uuid4().get_hex()
        try:
            newname = fuuid + os.path.splitext(f.filename)[1]
            f.save(upload_dir + newname)
        except:
            flash('Error uploading ' + f.filename)
            return

        if imghdr.what(upload_dir + newname):
            sql = upsert("images", \
                         uid=0, \
                         uuid=fuuid, \
                         filename=newname, \
                         tag=escape(tag))
            data = doupsert(sql)
            if not data:
                pd.errortext="SQL error"
                return render_template('error.html', pd=pd)

            sql = upsert("scarfimg", \
                         imgid=fuuid, \
                         scarfid=scarfuid)
            data = doupsert(sql)
            if not data:
                pd.errortext="SQL error"
                return render_template('error.html', pd=pd)

            flash('Uploaded ' + f.filename)
        else:
            try:
                os.remove(upload_dir + newname)
            except:
                app.logger.error("Error removing failed image upload: " + upload_dir + newname)
            flash(f.filename + " is not an image.")

def inc_scarfcount(user):
    sql = read('users', **{"username": escape(user)})
    result = doselect(sql)

    try:
        uid = result[0][0]
        numadds = result[0][7]
    except: 
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

    sql = read('ownwant', **{"scarfid": scarf[1]})
    sresult = doselect(sql)

    pd = pagedata()

    try:
        pd.swants = 0
        for res in sresult:
            if res[5] == 1:
                pd.swants = pd.swants + 1
    except:
        pd.swants = 0

    try:
        pd.shave = 0
        for res in sresult:
            if res[3] == 1:
                pd.shave = pd.shave + 1
    except:
        pd.shave = 0

    try:
        pd.willtrade = 0
        for res in sresult:
            if res[4] == 1:
                pd.willtrade = pd.willtrade + 1
    except:
        pd.willtrade = 0

    if check_login():
        userinfo = get_userinfo(session['username'])
        try:
            uid = userinfo[0][0]
        except:
            return render_template('error.html', errortext="SQL error")

        sql = read('ownwant', **{"userid": uid, "scarfid": scarf[1]})
        result = doselect(sql)

        try:
            iuid = result[0][0]
            pd.myscarfinfo=result[0]
        except: 
            app.logger.debug('')

    pd.title=scarf_id
    pd.scarfname=scarf_id
    pd.scarfimg=scarf_imgs(scarf[1])
    pd.scarf = scarf

    return render_template('scarf.html', pd=pd)

@app.route('/scarf/newscarf', methods=['GET', 'POST'])
def newscarf():
    pd = pagedata()
    if request.method == 'POST':
        if not check_login():
            flash('You must be logged in to create a scarf.')
            return redirect(url_for('/newuser'))

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

        hit_lastseen(session['username'])

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
        inc_scarfcount(session['username'])
        return redirect('/scarf/' + escape(request.form['name']))

    pd.title="Add New Scarf"

    return render_template('newscarf.html', pd=pd)
