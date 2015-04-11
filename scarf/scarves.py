from scarf import app
from flask import redirect, url_for, request, render_template, session, escape, flash
from werkzeug import secure_filename
from scarflib import check_login
import os
import imghdr
import uuid
import datetime
from sql import upsert, doupsert, read, doselect

def get_imgupload(f, name, tag):
    if not f.filename == '':
        try:
            newname = '/srv/data/web/vhosts/default/static/uploads/' + secure_filename(name) + os.path.splitext(f.filename)[1]
            f.save(newname)
        except:
            flash('Error uploading ' + f.filename)
            return

        if imghdr.what(newname):
            sql = upsert("images", \
                         uid=0, \
                         uuid=uuid.uuid4(), \
                         filename=newname, \
                         tag=escape(tag))
            data = doupsert(sql)
            if not data:
                return render_template('error.html', errortext="SQL error")

            flash('Uploaded ' + f.filename)
        else:
            os.remove(newname)
            flash(f.filename + " is not an image.")

def check_scarf(name):
    sql = read('scarves', **{"name": escape(name)})
    result = doselect(sql)

    if result:
        return True

    return False

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

@app.route('/scarf/<scarf_id>')
def show_post(scarf_id):
    if not check_scarf(escape(scarf_id)):
        return render_template('error.html', title="Scarf not found", errorcode="404", errortext="Scarf not found."), 404

    if check_login():
        return render_template('scarf.html', title=scarf_id, scarfname=scarf_id, user=session['username'])
    else:
        return render_template('scarf.html', title=scarf_id, scarfname=scarf_id)

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

        if check_scarf(escape(request.form['name'])):
            flash('A scarf with that name already exists')
            return redirect('/scarf/newscarf')

        get_imgupload(request.files['front'], escape(request.form['name']), "front")
        get_imgupload(request.files['back'], escape(request.form['name']), "back")

        #TODO image table & join

        sql = upsert("scarves", \
                     uid=0, \
                     uuid=uuid.uuid4(), \
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
