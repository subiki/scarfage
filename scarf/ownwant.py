from scarf import app
from flask import redirect, url_for, request, render_template, session, flash
from sql import upsert, doupsert, read, doquery, delete
from scarflib import siteuser, NoUser, siteitem, NoItem, redirect_back

#TODO more user feedback

@app.route('/item/<item_id>/donthave')
def donthave(item_id):
    update = dict(willtrade=0, own=0)
    ownwant(item_id, update)
    return redirect_back('/item/' + item_id)

@app.route('/item/<item_id>/have')
def have(item_id):
    update = dict(own=1, hidden=1)
    ownwant(item_id, update)
    return redirect_back('/item/' + item_id)

@app.route('/item/<item_id>/hide')
def hide(item_id):
    update = dict(willtrade=0, hidden=1)
    ownwant(item_id, update)
    return redirect_back('/item/' + item_id)

@app.route('/item/<item_id>/show')
def show(item_id):
    update = dict(hidden=0)
    ownwant(item_id, update)
    return redirect_back('/item/' + item_id)

@app.route('/item/<item_id>/wonttrade')
def wonttrade(item_id):
    update = dict(willtrade=0)
    ownwant(item_id, update)
    return redirect_back('/item/' + item_id)

@app.route('/item/<item_id>/willtrade')
def willtrade(item_id):
    update = dict(own=1, hidden=0, willtrade=1)
    ownwant(item_id, update)
    return redirect_back('/item/' + item_id)

@app.route('/item/<item_id>/want')
def want(item_id):
    update = dict(want=1)
    ownwant(item_id, update)
    return redirect_back('/item/' + item_id)

@app.route('/item/<item_id>/dontwant')
def dontwant(item_id):
    update = dict(want=0)
    ownwant(item_id, update)
    return redirect_back('/item/' + item_id)

def ownwant(item_id, values):
    try:
        moditem = siteitem(item_id)
    except NoItem:
        flash('Error adding ' + item_id + 'to your collection')
        return

    if 'username' in session:
        try:
            user = siteuser.create(session['username'])
        except NoUser:
            flash('You must be logged in to add items to a collection')
            return
    else:
        flash('You must be logged in to add items to a collection')
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

    sql = "delete from ownwant where own = '0' and want = '0' and willtrade = '0';"
    result = doquery(sql)
