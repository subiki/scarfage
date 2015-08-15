from scarf import app
from flask import redirect, url_for, request, render_template, session, flash
from werkzeug import secure_filename
from scarflib import pagedata, siteuser, NoUser, siteitem, NoItem, new_item, redirect_back
from main import page_not_found
from nocache import nocache
from debug import dbg

import markdown

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

@app.route('/item/<item_id>', defaults={'debug': False})
@app.route('/item/<item_id>/debug', defaults={'debug': True})
@nocache
def show_item(item_id, debug):
    pd = pagedata()

    try:
        showitem = siteitem(item_id)
        # todo: http://htmlpurifier.org/
        # todo: memoize
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

    if debug:
        if 'username' in session and pd.authuser.accesslevel == 255:
            pd.debug = dbg(pd)

    return render_template('item.html', pd=pd)

@app.route('/item/<item_id>/edit', methods=['GET', 'POST'], defaults={'debug': False})
@app.route('/item/<item_id>/edit/debug', methods=['GET', 'POST'], defaults={'debug': True})
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

    if debug:
        if 'username' in session and pd.authuser.accesslevel == 255:
            pd.debug = dbg(pd)

    return render_template('edititem.html', pd=pd)
