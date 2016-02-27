from scarf import app
from flask import redirect, url_for, request, render_template, session, flash
from werkzeug import secure_filename
from scarflib import pagedata, siteuser, NoUser, siteitem, NoItem, new_item, redirect_back, new_edit, uid_by_item, latest_items
from main import page_not_found
from nocache import nocache
from debug import dbg
from sql import read, doquery

import markdown
md_extensions = ['markdown.extensions.extra', 'markdown.extensions.nl2br', 'markdown.extensions.sane_lists']

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
    pd.conftext = delitem.name + " has been deleted. I hope you meant to do that."
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
    pd.conftarget = "/item/" + str(delitem.uid) + "/reallydelete"
    pd.conflinktext = "Yup, I'm sure"

    return render_template('confirm.html', pd=pd)

@app.route('/item/<item_id>/debug', defaults={'debug': True})
@app.route('/item/<item_id>', defaults={'debug': False})
@nocache
def show_item(item_id, debug):
    pd = pagedata()

    if item_id is 'new':
        return redirect("/item/" + item_id + "/edit")

    try:
        showitem = siteitem(item_id)
        # todo: http://htmlpurifier.org/

        showitem.description_html = markdown.markdown(str(showitem.body()), md_extensions)
    except NoItem:
        return page_not_found(404)

    if 'username' in session:
        try:
            user = siteuser.create(session['username'])
            pd.iteminfo = user.query_collection(showitem.uid)
        except (NoUser, NoItem):
            pass

    pd.title = item_id
    pd.item = showitem

    if debug:
        if 'username' in session and pd.authuser.accesslevel == 255:
            pd.debug = dbg(pd)

    return render_template('item.html', pd=pd)

@app.route('/item/<item_id>/revert/<edit>/debug', defaults={'debug': True})
@app.route('/item/<item_id>/revert/<edit>', defaults={'debug': False})
@nocache
def revert_item_edit(item_id, edit, debug):
    pd = pagedata()

    try:
        pd.item = siteitem(item_id)

        showitem.old = True
        showitem.editid = edit
    except:
        pass

    pd.title="Reverting: " + item_id
    pd.item_name = item_id

    if debug:
        if 'username' in session and pd.authuser.accesslevel == 255:
            pd.debug = dbg(pd)

    return render_template('edititem.html', pd=pd)

@app.route('/item/<item_id>/history/<edit>/debug', defaults={'debug': True})
@app.route('/item/<item_id>/history/<edit>', defaults={'debug': False})
@nocache
def show_item_edit(item_id, edit, debug):
    pd = pagedata()

    try:
        showitem = siteitem(item_id)
        showitem.old = True
        showitem.editid = edit

        showitem.description_html = markdown.markdown(str(showitem.body()), md_extensions)
    except NoItem:
        return redirect("/item/" + item_id + "/edit")

    pd.title = item_id
    pd.item = showitem

    if debug:
        if 'username' in session and pd.authuser.accesslevel == 255:
            pd.debug = dbg(pd)

    return render_template('item.html', pd=pd)

@app.route('/item/<item_id>/history/debug', defaults={'debug': True})
@app.route('/item/<item_id>/history', defaults={'debug': False})
@nocache
def show_item_history(item_id, debug):
    pd = pagedata()

    try:
        showitem = siteitem(item_id)
    except NoItem:
        return redirect("/item/" + item_id + "/edit")

    pd.title = item_id
    pd.item = showitem

    if debug:
        if 'username' in session and pd.authuser.accesslevel == 255:
            pd.debug = dbg(pd)

    return render_template('itemhistory.html', pd=pd)

@app.route('/item/edit/debug', methods=['GET', 'POST'], defaults={'debug': True})
@app.route('/item/<item_id>/edit', methods=['GET', 'POST'], defaults={'debug': False})
@app.route('/item/edit', methods=['GET', 'POST'], defaults={'debug': False})
@nocache
def edititem(debug, item_id=None):
    pd = pagedata()
    if request.method == 'POST':
        if 'username' in session:
            userid = pd.authuser.uid
        else:
            userid = 0 

        if 'desc' in request.form:
            try:
                item = siteitem(request.form['uid'])

                item_id = uid_by_item(request.form['name'])
                if not item_id or item_id == int(request.form['uid']):
                    item.name = request.form['name']
                    item.update()

                    # todo: check for null edits
                    new_edit(request.form['uid'], request.form['desc'], userid)

                    uid = request.form['uid']
                    flash('Edited item!')
                    return redirect('/item/' + str(uid))
                else:
                    flash(request.form['name'] + " already exists!")
                    item_id = request.form['uid']
            except NoItem:
                if uid_by_item(request.form['name']):
                    flash(request.form['name'] + " already exists!")
                    return redirect_back("/item/new")

                uid = new_item(request.form['name'], request.form['desc'], userid)
                return redirect('/item/' + str(uid))

    if item_id:
        try:
            pd.item = siteitem(item_id)
        except:
            return page_not_found(404)
     
        pd.title="Editing: " + str(item_id)
    else:
        pd.title="Editing: New Item"

    if debug:
        if 'username' in session and pd.authuser.accesslevel == 255:
            pd.debug = dbg(pd)

    return render_template('edititem.html', pd=pd)
