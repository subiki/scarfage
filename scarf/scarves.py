from scarf import app
from flask import redirect, url_for, request, render_template, session, escape, flash
from werkzeug import secure_filename
from scarflib import check_login
import os
import imghdr
import uuid
import re
import datetime
from sql import upsert, doupsert, read, doselect
from profile import get_userinfo
from scarflib import redirect_back

# DEBUG
import socket 
if socket.gethostname() == "grenadine":
    upload_dir = '/home/pq/sf/site/scarf/static/uploads/'
else: 
    upload_dir = '/srv/data/web/vhosts/default/static/uploads/'

def get_imgupload(f, scarfuid, tag):
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
                return render_template('error.html', errortext="SQL error")

            sql = upsert("scarfimg", \
                         imgid=fuuid, \
                         scarfid=scarfuid)
            data = doupsert(sql)
            if not data:
                return render_template('error.html', errortext="SQL error")


            flash('Uploaded ' + f.filename)
        else:
            os.remove(upload_dir + newname)
            flash(f.filename + " is not an image.")

def check_scarf(name):
    sql = read('scarves', **{"name": escape(name)})
    result = doselect(sql)

    try:
        return result[0]
    except:
        return False

def scarf_imgs(scarf_uid):
    sql = read('scarfimg', **{"scarfid": scarf_uid})
    result = doselect(sql)
    scarfimgs = []

    try:
        for scarfimg in result:
            sql = read('images', **{"uuid": scarfimg[1]})
            result = doselect(sql)
            scarfimgs.append(result)
    except:
        return scarfimgs

    return scarfimgs

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

@app.route('/remove/<scarf_id>')
def remove(scarf_id):
    ownwant(scarf_id, 4, 0)
    ownwant(scarf_id, 5, 0)
    ownwant(scarf_id, 6, 0)
    ownwant(scarf_id, 7, 0)
    return redirect_back('/scarf/' + escape(scarf_id))

@app.route('/ihave/<scarf_id>')
def ihave(scarf_id):
    ownwant(scarf_id, 4, 1)
    return redirect_back('/scarf/' + escape(scarf_id))

@app.route('/hide/<scarf_id>')
def hide(scarf_id):
    ownwant(scarf_id, 7, 1)
    return redirect_back('/scarf/' + escape(scarf_id))

@app.route('/show/<scarf_id>')
def show(scarf_id):
    ownwant(scarf_id, 7, 0)
    return redirect_back('/scarf/' + escape(scarf_id))

@app.route('/wonttrade/<scarf_id>')
def wonttrade(scarf_id):
    ownwant(scarf_id, 5, 0)
    return redirect_back('/scarf/' + escape(scarf_id))

@app.route('/willtrade/<scarf_id>')
def willtrade(scarf_id):
    ownwant(scarf_id, 4, 1)
    ownwant(scarf_id, 5, 1)
    return redirect_back('/scarf/' + escape(scarf_id))

@app.route('/want/<scarf_id>')
def want(scarf_id):
    ownwant(scarf_id, 4, 0)
    ownwant(scarf_id, 6, 1)
    return redirect_back('/scarf/' + escape(scarf_id))

@app.route('/dontwant/<scarf_id>')
def dontwant(scarf_id):
    ownwant(scarf_id, 6, 0)
    return redirect_back('/scarf/' + escape(scarf_id))

def ownwant(scarf_id, index, value):
    scarf = check_scarf(escape(scarf_id))
    if scarf == False:
        return

    if check_login():
        userinfo = get_userinfo(escape(session['username']))
        try:
            uid = userinfo[0][0]
        except:
            flash('userinfo')
            return

        sql = read('ownwant', **{"userid": uid, "scarfid": scarf[1]})
        result = doselect(sql)
        app.logger.debug(result)

        iuid=0
        try:
            iuid = result[0][0]
        except: 
            iuid=0

        if index == 4:
            sql = upsert("ownwant", \
                         uid=iuid,
                         userid=uid, \
                         scarfid=scarf[1], \
                         own=value)

        if index == 5:
            sql = upsert("ownwant", \
                         uid=iuid,
                         userid=uid, \
                         scarfid=scarf[1], \
                         willtrade=value)

        if index == 6:
            sql = upsert("ownwant", \
                         uid=iuid,
                         userid=uid, \
                         scarfid=scarf[1], \
                         want=value)
        if index == 7:
            sql = upsert("ownwant", \
                         uid=iuid,
                         userid=uid, \
                         scarfid=scarf[1], \
                         hidden=value)

        data = doupsert(sql)

    else:
        flash("You must be logged in to modify a collection.")

    return 

@app.route('/scarf/<scarf_id>')
def show_post(scarf_id):
    scarf = check_scarf(escape(scarf_id))
    if scarf == False:
        return render_template('error.html', title="Scarf not found", errorcode="404", errortext="Scarf not found."), 404

    if check_login():
        userinfo = get_userinfo(escape(session['username']))
        try:
            uid = userinfo[0][0]
        except:
            flash('userinfo')
            return render_template('error.html', errortext="SQL error")

        sql = read('ownwant', **{"userid": uid, "scarfid": scarf[1]})
        result = doselect(sql)

        try:
            iuid = result[0][0]
            return render_template('scarf.html', title=scarf_id, myscarfinfo=result[0], scarfname=scarf_id, scarfimgs=scarf_imgs(scarf[1]), scarf=scarf, user=session['username'])
        except: 
            return render_template('scarf.html', title=scarf_id, scarfname=scarf_id, scarfimgs=scarf_imgs(scarf[1]), scarf=scarf, user=session['username'])

    return render_template('scarf.html', title=scarf_id, scarfname=scarf_id, scarfimgs=scarf_imgs(scarf[1]), scarf=scarf)

@app.route('/scarf/newscarf', methods=['GET', 'POST'])
def newscarf():
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

        if '/' in request.form['name'] or  '\\' in request.form['name']:
            flash('No slashes in names please')
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
            return render_template('error.html', errortext="SQL error")

        flash('Added scarf!')
        inc_scarfcount(session['username'])
        return redirect('/scarf/' + escape(request.form['name']))


    if check_login():
        return render_template('newscarf.html', title="Add New Scarf", user=session['username'])
    else:
        return render_template('newscarf.html', title="Add New Scarf")
