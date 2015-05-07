from scarf import app
from flask import redirect, url_for, request, render_template, session, escape, flash
from sql import upsert, doupsert, read, doquery, delete
from scarflib import siteuser, NoUser, siteitem, NoItem, redirect_back

@app.route('/item/<item_id>/donthave')
def donthave(item_id):
    update = dict(willtrade=0, own=0)
    ownwant(escape(item_id), update)
    return redirect_back('/item/' + escape(item_id))

@app.route('/item/<item_id>/have')
def have(item_id):
    update = dict(own=1)
    ownwant(escape(item_id), update)
    return redirect_back('/item/' + escape(item_id))

@app.route('/item/<item_id>/hide')
def hide(item_id):
    update = dict(hidden=1)
    ownwant(escape(item_id), update)
    return redirect_back('/item/' + escape(item_id))

@app.route('/item/<item_id>/show')
def show(item_id):
    update = dict(hidden=0)
    ownwant(escape(item_id), update)
    return redirect_back('/item/' + escape(item_id))

@app.route('/item/<item_id>/wonttrade')
def wonttrade(item_id):
    update = dict(willtrade=0)
    ownwant(escape(item_id), update)
    return redirect_back('/item/' + escape(item_id))

@app.route('/item/<item_id>/willtrade')
def willtrade(item_id):
    update = dict(own=1, hidden=0, willtrade=1)
    ownwant(escape(item_id), update)
    return redirect_back('/item/' + escape(item_id))

@app.route('/item/<item_id>/want')
def want(item_id):
    update = dict(want=1)
    ownwant(escape(item_id), update)
    return redirect_back('/item/' + escape(item_id))

@app.route('/item/<item_id>/dontwant')
def dontwant(item_id):
    update = dict(want=0)
    ownwant(escape(item_id), update)
    return redirect_back('/item/' + escape(item_id))

def ownwant(item_id, values):
    try:
        moditem = siteitem(item_id)
    except NoItem:
        return

    if username in session:
        try:
            user = siteuser(session['username'])
        except NoUser:
            return
    else:
        return

    result = user.query_collection(item_id)

    try:
        iuid = result.uid
    except AttributeError: 
        iuid=0

    update = dict(uid=iuid, userid=user.uid, itemid=moditem.uid)
    update.update(values)

    sql = upsert("ownwant", \
                 **update)

    data = doupsert(sql)

    sql = delete('ownwant', **{ 'own': '0', 'willtrade': '0', 'want': '0', 'hidden': '0' })
    result = doquery(sql)

    return 
