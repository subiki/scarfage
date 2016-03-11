from scarf import app
from flask import redirect, url_for, request, render_template, session, flash
from werkzeug import secure_filename
from core import PageData, SiteUser, NoUser, SiteItem, NoItem, new_item, redirect_back, new_edit, uid_by_item, latest_items, escape_html
from main import page_not_found
from nocache import nocache
from debug import dbg
from sql import read, doquery, Tree
from access import check_admin

import markdown
md_extensions = ['markdown.extensions.extra', 'markdown.extensions.nl2br', 'markdown.extensions.sane_lists']

import sys
reload(sys)  
sys.setdefaultencoding('utf8')

@app.route('/item/')
def itemroot():
    return redirect(url_for('index'))

@app.route('/item/<item_id>/reallydelete')
@check_admin
def reallydelete_item(item_id):
    try:
        delitem = SiteItem(item_id)
    except NoItem: 
        return page_not_found(404)

    pd = PageData()

    pd.title=delitem.name + " has been deleted"

    delitem.delete()

    pd.accessreq = 255
    pd.conftext = delitem.name + " has been deleted. I hope you meant to do that."
    pd.conftarget = ""
    pd.conflinktext = ""
    return render_template('confirm.html', pd=pd)

@app.route('/item/<item_id>/delete')
@check_admin
def delete_item(item_id):
    try:
        delitem = SiteItem(item_id)
    except NoItem: 
        return page_not_found(404)

    pd = PageData()

    pd.title=delitem.name

    pd.accessreq = 255
    pd.conftext = "Deleting item " + delitem.name + ". This will also delete all trades but not the associated PMs. If this item has open trades you are going to confuse people. Are you really sure you want to do this?"
    pd.conftarget = "/item/" + str(delitem.uid) + "/reallydelete"
    pd.conflinktext = "Yup, I'm sure"

    return render_template('confirm.html', pd=pd)

@app.route('/item/<item_id>/debug', defaults={'debug': True})
@app.route('/item/<item_id>', defaults={'debug': False})
@nocache
def show_item(item_id, debug):
    pd = PageData()

    if item_id is 'new':
        return redirect("/item/" + item_id + "/edit")

    try:
        showitem = SiteItem(item_id)

        showitem.description_html = markdown.markdown(escape_html(str(showitem.body())), md_extensions)
    except NoItem:
        return page_not_found(404)

    if 'username' in session:
        try:
            user = SiteUser.create(session['username'])
            pd.iteminfo = user.query_collection(showitem.uid)
        except (NoUser, NoItem):
            pass

    pd.title = showitem.name
    pd.item = showitem

    if debug:
        if 'username' in session and pd.authuser.accesslevel == 255:
            pd.debug = dbg(pd)

    return render_template('item.html', pd=pd)

@app.route('/item/<item_id>/revert/<edit>/debug', defaults={'debug': True})
@app.route('/item/<item_id>/revert/<edit>', defaults={'debug': False})
@nocache
def revert_item_edit(item_id, edit, debug):
    pd = PageData()

    try:
        item = SiteItem(item_id)

        item.old = True
        item.description = edit
    except:
        pass

    pd.title="Reverting: " + item.name
    pd.item_name = item.name
    pd.item = item

    if debug:
        if 'username' in session and pd.authuser.accesslevel == 255:
            pd.debug = dbg(pd)

    return render_template('edititem.html', pd=pd)

@app.route('/item/<item_id>/history/<edit>/debug', defaults={'debug': True})
@app.route('/item/<item_id>/history/<edit>', defaults={'debug': False})
@nocache
def show_item_edit(item_id, edit, debug):
    pd = PageData()

    try:
        showitem = SiteItem(item_id)
        showitem.old = True
        showitem.description = edit

        showitem.description_html = markdown.markdown(escape_html(str(showitem.body(edit))), md_extensions)
    except NoItem:
        return redirect("/item/" + item_id + "/edit")

    pd.title = showitem.name
    pd.item = showitem

    if debug:
        if 'username' in session and pd.authuser.accesslevel == 255:
            pd.debug = dbg(pd)

    return render_template('item.html', pd=pd)

@app.route('/item/<item_id>/history/debug', defaults={'debug': True})
@app.route('/item/<item_id>/history', defaults={'debug': False})
@nocache
def show_item_history(item_id, debug):
    pd = PageData()

    try:
        showitem = SiteItem(item_id)
    except NoItem:
        return redirect("/item/" + item_id + "/edit")

    pd.title = showitem.name
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
    pd = PageData()
    if request.method == 'POST':
        if 'username' in session:
            userid = pd.authuser.uid
        else:
            userid = 0 

        if 'desc' in request.form:
            try:
                item = SiteItem(request.form['uid'])

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
                    flash(item.name + " already exists!")
                    item_id = request.form['uid']
            except NoItem:
                if uid_by_item(request.form['name']):
                    flash(request.form['name'] + " already exists!")
                    return redirect_back("/item/new")

                uid = new_item(request.form['name'], request.form['desc'], userid)
                return redirect('/item/' + str(uid))

    if item_id:
        try:
            pd.item = SiteItem(item_id)
        except:
            return page_not_found(404)
     
        pd.title="Editing: %s" % pd.item.name
    else:
        pd.title="Editing: New Item"

    if debug:
        if 'username' in session and pd.authuser.accesslevel == 255:
            pd.debug = dbg(pd)

    return render_template('edititem.html', pd=pd)

@app.route('/item/tag', methods=['POST'])
@nocache
def tagitem():
    pd = PageData()
    if request.method == 'POST':
        if 'username' in session:
            userid = pd.authuser.uid
        else:
            userid = 0 

        if 'tag' in request.form:
            if request.form['tag'] == '':
                return redirect_back('index')

            try:
                item = SiteItem(request.form['uid'])
                item.add_tag(request.form['tag'][:64])
                return redirect('/item/' + str(item.uid))
            except NoItem:
                return page_not_found(404)

@app.route('/item/<item_id>/untag/<tag_ob>')
def untag_item(item_id, tag_ob):
    try:
        item = SiteItem(item_id)
    except NoItem: 
        return page_not_found(404)

    pd = PageData()
    item.remove_tag(pd.decode(tag_ob))
    return redirect('/item/' + str(item.uid))
