from scarf import app
from core import SiteUser, NoUser, SiteItem, NoItem, new_item, redirect_back, new_edit, uid_by_item, latest_items
from main import page_not_found, PageData, request_wants_json, render_markdown
from nocache import nocache
import core
import json

from flask import redirect, url_for, request, render_template, session, flash
from werkzeug import secure_filename
from access import check_admin
import logging

logger = logging.getLogger(__name__)

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
        delitem = SiteItem.create(item_id)
    except NoItem: 
        return page_not_found()

    delitem.delete()

    if request_wants_json():
        return '{}'
    else:
        return redirect(url_for('index'))

@app.route('/item/<item_id>/delete')
@check_admin
def delete_item(item_id):
    try:
        delitem = SiteItem.create(item_id)
    except NoItem: 
        return page_not_found()

    pd = PageData()

    pd.title=delitem.name

    pd.accessreq = 255
    pd.conftext =  "Items may take some time to disappear from the indexes."
    pd.conftarget = "/item/" + str(delitem.uid) + "/reallydelete"
    pd.conflinktext = "I want to delete '{}' and accept the consequences of this action.".format(delitem.name)

    return render_template('confirm.html', pd=pd)

@app.route('/item/<item_id>/history/<edit>')
@app.route('/item/<item_id>')
@nocache
def show_item(item_id, edit=None):
    """
    :URLs:
        * /item/<item_id>/history/<edit>
        * /item/<item_id>

    :Methods: GET

    Setting the accept:application/json header will return JSON.

    :Sample response:

    .. code-block:: javascript
    {
        "added": "2016-05-23 20:52:12",
        "body": "",
        "body_rendered": "",
        "description": 384,
        "images": [
            443,
            444
        ],
        "modified": "2016-05-23 20:53:19",
        "name": "SSFC",
        "tags": {
            "FO": false,
            "Front Office": true,
            "MLS": true,
        },
        "uid": 388
    }

    * added         - Date added, always UTC
    * modified      - Late modified, also always UTC
    * name          - Item's name
    * body          - raw unrendered description body for the active edit
    * body_rendered - rendered content for the active edit
    * description   - edit identifier
    * images        - array of image ids associated with this item
    * tags          - dict of tags, keys are the tag title. the value is a bool which will be set to true if the tag was directly applied and false if inherited.
    """

    if item_id is 'new':
        return redirect("/item/" + item_id + "/edit")

    try:
        showitem = SiteItem.create(item_id)

        if showitem.deleted:
            return page_not_found()

        if edit:
            edit = int(edit)

        showitem.edit = edit

        if edit and edit not in [int(i.uid) for i in showitem.history()]:
            return page_not_found()
    except (NoItem, ValueError):
        return page_not_found()

    if request_wants_json():
        values = showitem.values(edit)
        values['body_rendered'] = render_markdown(values['body'])

        return json.dumps(values)
    else:
        pd = PageData()

        pd.title = showitem.name
        pd.item = showitem

        return render_template('item.html', pd=pd)

@app.route('/item/<item_id>/revert/<edit>')
@nocache
def revert_item_edit(item_id, edit):
    pd = PageData()

    try:
        item = SiteItem.create(item_id)

        item.old = True
        item.edit = edit
    except NoItem:
        return page_not_found()

    pd.title="Reverting: " + item.name
    pd.item_name = item.name
    pd.item = item

    return render_template('edititem.html', pd=pd)

@app.route('/item/<item_id>/history')
@nocache
def show_item_history(item_id):
    pd = PageData()

    try:
        showitem = SiteItem.create(item_id)
    except NoItem:
        return redirect("/item/" + item_id + "/edit")

    pd.title = showitem.name
    pd.item = showitem

    return render_template('itemhistory.html', pd=pd)

@app.route('/item/<item_id>/edit', methods=['GET', 'POST'])
@app.route('/item/edit', methods=['GET', 'POST'])
@nocache
def edititem(item_id=None):
    pd = PageData()
    if request.method == 'POST':
        if 'username' in session:
            userid = pd.authuser.uid
        else:
            userid = 0 

        if 'desc' in request.form:
            if request.form['name'] == '':
                flash('No name for this item?')
                return redirect_back("/item/new")

            try:
                item = SiteItem.create(request.form['uid'])

                item_id = uid_by_item(request.form['name'])
                if not item_id or item_id == int(request.form['uid']):
                    uid = request.form['uid']
                    ip = request.remote_addr

                    if item.name != request.form['name']:
                        item.name = request.form['name']
                        item.update()

                    old = core.digest(item.body())
                    new = core.digest(request.form['desc'])

                    # silently discard null edits
                    if old != new:
                        new_edit(uid, request.form['desc'], userid, ip)
                        logger.info('item {} edited by user {} ({})'.format(uid, userid, ip))
                    else:
                        logger.info('null edit discarded for item {} by user {} ({})'.format(uid, userid, ip))

                    return redirect('/item/' + str(uid))
                else:
                    flash(item.name + " already exists!")
                    item_id = request.form['uid']
            except NoItem:
                if uid_by_item(request.form['name']):
                    flash(request.form['name'] + " already exists!")
                    return redirect_back("/item/new")

                uid = new_item(request.form['name'], request.form['desc'], userid, request.remote_addr)
                return redirect('/item/' + str(uid))

    if item_id:
        try:
            pd.item = SiteItem.create(item_id)
        except NoItem:
            return page_not_found()
     
        pd.title="Editing: %s" % pd.item.name
    else:
        pd.title="Editing: New Item"

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
                item = SiteItem.create(request.form['uid'])
                item.add_tag(request.form['tag'][:64])
                return redirect('/item/' + str(item.uid))
            except NoItem:
                return page_not_found()

@app.route('/item/<item_id>/untag/<tag_ob>')
def untag_item(item_id, tag_ob):
    try:
        item = SiteItem.create(item_id)
    except NoItem: 
        return page_not_found()

    pd = PageData()
    item.remove_tag(pd.decode(tag_ob))
    return redirect('/item/' + str(item.uid))
