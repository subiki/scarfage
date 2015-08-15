from scarf import app
from flask import redirect, url_for, request, render_template, session, flash
from werkzeug import secure_filename
from scarflib import pagedata, siteuser, NoUser, siteitem, NoItem, new_item, redirect_back
from main import page_not_found
from nocache import nocache

import markdown

import sys
reload(sys)  
sys.setdefaultencoding('utf8')

@app.route('/item/')
def itemroot():
    return redirect(url_for('index'))

@app.route('/item/<item_id>/reallydelete')
def reallydelete_item(item_id):
    try:
        delitem = siteitem(item_id)
    except NoItem: 
        return page_not_found(404)

    pd = pagedata()

    if not pd.authuser.accesslevel == 255:
        return redirect(url_for('accessdenied'))

    pd.title=item_id + " has been deleted"

    delitem.delete()

    pd.accessreq = 255
    pd.conftext = delitem.name + " and its images have been deleted. I hope you meant to do that."
    pd.conftarget = ""
    pd.conflinktext = ""
    return render_template('confirm.html', pd=pd)

@app.route('/item/<item_id>/delete')
def delete_item(item_id):
    try:
        delitem = siteitem(item_id)
    except NoItem: 
        return page_not_found(404)

    pd = pagedata()

    if not pd.authuser.accesslevel == 255:
        return redirect(url_for('accessdenied'))

    pd.title=item_id

    pd.accessreq = 255
    pd.conftext = "Deleting item " + delitem.name + ". This will also delete all trades but not the associated PMs. If this item has open trades you are going to confuse people. Are you really sure you want to do this?"
    pd.conftarget = "/item/" + delitem.name + "/reallydelete"
    pd.conflinktext = "Yup, I'm sure"

    return render_template('confirm.html', pd=pd)

@app.route('/item/<item_id>')
@nocache
def show_item(item_id):
    pd = pagedata()

    try:
        showitem = siteitem(item_id)
        showitem.description_html = markdown.markdown(showitem.description)
    except NoItem:
        return redirect("/item/" + item_id + "/edit")

    if 'username' in session:
        try:
            user = siteuser.create(session['username'])
            pd.iteminfo = user.query_collection(showitem.name)
        except (NoUser, NoItem):
            pass

    pd.title = item_id
    pd.item = showitem

    return render_template('item.html', pd=pd)

@app.route('/item/<item_id>/edit', methods=['GET', 'POST'])
@nocache
def edititem(item_id):
    pd = pagedata()
    if request.method == 'POST':
            #return redirect("/item/" + item_id + "/edit")
        if 'username' in session:
            uid = pd.authuser.uid
        else:
            uid = 0 

        if 'desc' in request.form:
            try:
                pd.item = siteitem(item_id)
                pd.item.description = request.form['desc']
                pd.item.update()
            except NoItem:
                new_item(item_id, request.form['desc'], uid)

        flash('Edited item!')
        return redirect('/item/' + item_id)

    try:
        pd.item = siteitem(item_id)
    except:
        pass

    pd.title="Editing: " + item_id
    pd.item_name = item_id
    return render_template('edititem.html', pd=pd)


@app.route('/new', methods=['GET', 'POST'])
def newitem():
    pd = pagedata()
    if request.method == 'POST':
        if request.form['name'] == '':
            flash('No name?')
            return redirect(url_for('newitem'))

        invalid = '[]{}\'"<>;/\\'
        for c in invalid:
            if c in request.form['name']:
                flash("Invalid character in name: " + c)
                return redirect(url_for('newitem'))

        if 'username' in session:
            uid = pd.authuser.uid
        else:
            uid = 0 

        if request.form['imgtag'] == '':
            flash('Please add a tag for this picture.')
# TODO: re fill form
            return redirect(url_for('newitem'))

        try:
            newitem = siteitem(request.form['name'])
            flash('An item with that name already exists')
            return redirect(url_for('newitem'))
        except NoItem:
            new_item(request.form['name'], request.form['desc'], uid)

        try:
            newitem = siteitem(request.form['name'])

            file = request.files['img']
            if file:
                newitem.newimg(request.files['img'], request.form['imgtag'])

        except NoItem:
            flash('Error adding item!')
            return redirect(url_for('newitem'))

        flash('Added item!')
        return redirect('/item/' + request.form['name'])

    pd.title="Add New Item"

    return render_template('upload.html', pd=pd)
