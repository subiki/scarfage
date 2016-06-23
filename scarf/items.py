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
        pd = PageData()
        pd.title=delitem.name + " has been deleted"
        pd.accessreq = 255
        pd.conftext = delitem.name + " has been deleted. I hope you meant to do that."
        pd.conftarget = ""
        pd.conflinktext = ""

        return render_template('confirm.html', pd=pd)

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
    pd.conftext = "Deleting item " + delitem.name + ". This will also delete all trades but not the associated PMs. If this item has open trades you are going to confuse people. Are you really sure you want to do this?"
    pd.conftarget = "/item/" + str(delitem.uid) + "/reallydelete"
    pd.conflinktext = "Yup, I'm sure"

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
    * body          - raw unrendered description body
    * body_rendered - rendered content
    * description   - edit identifier
    * images        - array of image ids associated with this item
    * tags          - dict of tags, keys are the tag title. the value is a bool which will be set to true if the tag was directly applied and false if inherited.
    """

    if item_id is 'new':
        return redirect("/item/" + item_id + "/edit")

    try:
        showitem = SiteItem.create(item_id)

        if edit:
            showitem.old = True
            showitem.edit = edit
        else:
            showitem.old = False
            showitem.edit = None

        showitem.description_content = showitem.body(edit)
    except NoItem:
        return page_not_found()

    if request_wants_json():
        values = showitem.values()
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
                    item.name = request.form['name']
                    item.update()

                    # todo: check for null edits
                    new_edit(request.form['uid'], request.form['desc'], userid, request.remote_addr)

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

@app.route('/item/search')
@nocache
def searchitem():
    """
    :URL: /item/search?page=<page>&limit=<max results>&query=<search query>&sort=<sort type>

    :Method: GET

    :Sort Types:
        * name - Alphabetical by name
        * added - By added date, latest first
        * modified - Last modified

    :Sample Response: Setting the accept:application/json header will return JSON. 

    .. code-block:: javascript

    {
        "limit": 2,
        "num_pages": 4,
        "num_results": 8,
        "query": "Cascadia",
        "results": [
            {
                "added": "2016-05-22 17:52:36",
                "body": "Blue/White (Cascadia Fringe, Gisele Currier Memorial Fundraiser)",
                "description": 460,
                "images": [
                    388,
                    389
                ],
                "modified": "2016-05-24 22:45:33",
                "name": "No Pity MLS Blue White Fringe (Cascadia Fringe) 2012",
                "uid": 362
            },
            {
                "added": "2016-05-22 17:02:15",
                "body": "",
                "description": 317,
                "images": [
                    364,
                    365
                ],
                "modified": "2016-05-22 17:02:15",
                "name": "Cascadia",
                "uid": 350
            }
        ]
    }
    """

    pd = PageData()
    pd.query = request.args.get('query')
    pd.limit = request.args.get('limit')
    pd.page = request.args.get('page')
    pd.sort = request.args.get('sort')

    if not pd.limit:
        pd.limit = 20
    else:
        pd.limit = int(pd.limit)

    if not pd.page:
        pd.page = 1
    else:
        pd.page = int(pd.page)

    offset = (pd.page - 1) * pd.limit

    results = core.item_search(pd.query, pd.limit, offset, pd.sort)

    pd.results = results['items']
    pd.num_results = results['maxresults']
    pd.num_pages = -(-pd.num_results // pd.limit) # round up

    if pd.num_results == 0:
        pd.results = [None]

    if request_wants_json():
        resp = dict()
        resp['results'] = list()
        for item in pd.results:
            resp['results'].append(item.values())

        resp['query'] = pd.query
        resp['num_results'] = pd.num_results
        resp['num_pages'] = pd.num_pages
        resp['limit'] = pd.limit
        return json.dumps(resp)

    return render_template('search.html', pd=pd)
