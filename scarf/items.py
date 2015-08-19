from scarf import app
from flask import redirect, url_for, request, render_template, session, flash
from werkzeug import secure_filename
from scarflib import pagedata, siteuser, NoUser, siteitem, NoItem, new_item, redirect_back, new_edit, uid_by_item
from main import page_not_found
from nocache import nocache
from debug import dbg
from sql import read, doquery, sql_escape

import markdown
from markdown.extensions.wikilinks import WikiLinkExtension
md_extensions = ['markdown.extensions.extra', 'markdown.extensions.admonition', WikiLinkExtension(base_url='/item/', end_url=''), 'markdown.extensions.sane_lists']

import sys
reload(sys)  
sys.setdefaultencoding('utf8')

@app.route('/item/')
def itemroot():
    return redirect(url_for('newitem'))

@app.route('/newitem')
def newitem():
    pd = pagedata()
    return render_template('contribute.html', pd=pd)

@app.route('/editinghelp')
def editinghelp():
    pd = pagedata()
    return render_template('editinghelp.html', pd=pd)

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

@app.route('/item/<item_id>/debug', defaults={'debug': True})
@app.route('/item/<item_id>', defaults={'debug': False})
@nocache
def show_item(item_id, debug):
    pd = pagedata()

    try:
        showitem = siteitem(item_id)
        # todo: http://htmlpurifier.org/
        # todo: memoize

        sql = "SELECT body FROM itemedits WHERE uid = '%s';" % showitem.description 
        showitem.description = doquery(sql)[0][0]

        showitem.description_html = markdown.markdown(str(showitem.description), md_extensions)
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

        sql = "SELECT body FROM itemedits WHERE itemid = '%s' and uid = '%s';" % (pd.item.uid, sql_escape(edit))
        pd.item.description = doquery(sql)[0][0]
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
        # todo: http://htmlpurifier.org/
        sql = "SELECT body FROM itemedits WHERE uid = '%s' and itemid = '%s';" % (sql_escape(edit), showitem.uid)
        showitem.description = doquery(sql)[0][0]
        showitem.old = True
        showitem.editid = edit

        showitem.description_html = markdown.markdown(str(showitem.description), md_extensions)
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

@app.route('/item/<item_id>/edit/debug', methods=['GET', 'POST'], defaults={'debug': True})
@app.route('/item/<item_id>/edit', methods=['GET', 'POST'], defaults={'debug': False})
@nocache
def edititem(item_id, debug):
    pd = pagedata()
    if request.method == 'POST':
        if 'username' in session:
            uid = pd.authuser.uid
        else:
            uid = 0 

        if 'desc' in request.form:
            try:
                item = siteitem(item_id)
                item.description = request.form['desc']
                item.update()

                # todo: check for null edits
                new_edit(uid_by_item(item_id), request.form['desc'], uid)
            except NoItem:
                new_item(item_id, request.form['desc'], uid)

        flash('Edited item!')
        return redirect('/item/' + item_id)

    try:
        pd.item = siteitem(item_id)

        sql = "SELECT body FROM itemedits WHERE uid = '%s';" % pd.item.description 
        pd.item.description = doquery(sql)[0][0]
    except:
        pass

    pd.title="Editing: " + item_id
    pd.item_name = item_id

    if debug:
        if 'username' in session and pd.authuser.accesslevel == 255:
            pd.debug = dbg(pd)

    return render_template('edititem.html', pd=pd)
