from scarf import app
from core import SiteUser, NoUser, SiteItem, NoItem, redirect_back, OwnWant
from main import page_not_found, own_goal

import json
from flask import redirect, url_for, request, render_template, session, flash

actions = dict(donthave = dict(willtrade=0, own=0, hidden=0),
               have = dict(own=1, hidden=1),
               hide = dict(willtrade=0, hidden=1),
               show = dict(hidden=0),
               wonttrade = dict(willtrade=0),
               willtrade = dict(own=1, hidden=0, willtrade=1),
               want = dict(want=1),
               dontwant = dict(want=0))

def ownwant(item_id, user_id, values):
    moditem = SiteItem(item_id)
    OwnWant(item_id, user_id).update(values)

@app.route('/item/<item_id>/<action>', methods=['GET', 'POST'])
def itemaction(item_id, action):
    """
    URL: /item/<item_id>/<action>
    Methods: GET, POST

    Update or query the logged in user's record for an item.

    If a POST request is received then the current record is returned instead of a redirect back to the previous page.

    Allowed actions:
    'status'    - Return the item's current status
    'have'      - Mark an item as part of the user's collection
    'donthave'  - Remove the item from the user's collection
    'show'      - If the item is in the user's collection mark it as visible to others
    'hide'      - If the item is in the user's collection hide it from others
    'willtrade' - Mark the item as available for trade
    'wonttrade' - Don't show this item as available for trade
    'want'      - Add this item to the user's want list
    'dontwant ' - Remove this item from the user's want list

    Sample record:
    {"hidden": 1, "want": 0, "have": 1, "willtrade": 0}
    """

    try:
        user = SiteUser.create(session['username'])
    except (NoUser, KeyError):
        user = None

    def get_record():
        return json.dumps(user.query_collection(item_id).values())

    if action == 'status':
        if not user:
            return '{}'
        else:
            return get_record()

    if user:
        try: 
            ownwant(item_id, user.uid, actions[action])
        except (NoItem, KeyError):
            return page_not_found(404)

        if request.method == 'POST':
            return get_record()
    else:
        flash('You must be logged in to have a collection')

    return redirect_back('/item/' + item_id)
