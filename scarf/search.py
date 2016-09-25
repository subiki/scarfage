from scarf import app
from core import SiteUser, NoUser, SiteItem, NoItem, new_item, redirect_back, new_edit, uid_by_item, latest_items
from main import page_not_found, PageData, request_wants_json, render_markdown
from nocache import nocache
import core
import json

from flask import redirect, url_for, request, render_template, session, flash
import logging

logger = logging.getLogger(__name__)

import sys
reload(sys)  
sys.setdefaultencoding('utf8')

@app.route('/item/search')
@nocache
def search():
    """
    :URL: /item/search?page=<page>&type=<query type>&limit=<max results>&query=<search query>&sort=<sort type>

    :Method: GET

    :Query Types:
        * item - Item Search
        * user - User Search

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
    pd.search_type = request.args.get('type')
    pd.query = request.args.get('query')
    pd.limit = request.args.get('limit')
    pd.page = request.args.get('page')
    pd.sort = request.args.get('sort')

    try:
        if not pd.limit:
            pd.limit = 20
        else:
            pd.limit = int(pd.limit)

        if not pd.page:
            pd.page = 1
        else:
            pd.page = int(pd.page)
    except ValueError:
        return page_not_found()

    if pd.search_type == "items":
        return item_search(pd)
    elif pd.search_type == "users":
        return user_search(pd)
    elif pd.search_type == "tags":
        return tag_search(pd)
    else:
        return page_not_found()

def item_search(pd):
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

    return render_template('search/items.html', pd=pd)

def user_search(pd):
    offset = (pd.page - 1) * pd.limit
    results = core.user_search(pd.query, pd.limit, offset, pd.sort)

    pd.results = results['users']
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

    return render_template('search/users.html', pd=pd)

def tag_search(pd):
    offset = (pd.page - 1) * pd.limit
    results = core.tag_search(pd.query, pd.limit, offset, pd.sort)

    pd.results = results['tags']
    pd.num_results = results['maxresults']
    pd.num_pages = -(-pd.num_results // pd.limit) # round up

    if pd.num_results == 0:
        pd.results = [None]

    if request_wants_json():
        resp = dict()
        resp['results'] = pd.results
        resp['query'] = pd.query
        resp['num_results'] = pd.num_results
        resp['num_pages'] = pd.num_pages
        resp['limit'] = pd.limit
        return json.dumps(resp)

    return render_template('search/tags.html', pd=pd)
