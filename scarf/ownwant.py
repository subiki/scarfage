from scarflib import siteuser, NoUser, siteitem, NoItem

from scarf import app
from flask import redirect, url_for, request, render_template, session, escape, flash
from sql import upsert, doupsert, read, doselect, delete
from scarflib import redirect_back

@app.route('/scarf/<item_id>/donthave')
def donthave(item_id):
    update = dict(willtrade=0, own=0)
    ownwant(escape(item_id), update)
    return redirect_back('/scarf/' + escape(item_id))

@app.route('/scarf/<item_id>/have')
def have(item_id):
    update = dict(own=1)
    ownwant(escape(item_id), update)
    return redirect_back('/scarf/' + escape(item_id))

@app.route('/scarf/<item_id>/hide')
def hide(item_id):
    update = dict(hide=1)
    ownwant(escape(item_id), update)
    return redirect_back('/scarf/' + escape(item_id))

@app.route('/scarf/<item_id>/show')
def show(item_id):
    update = dict(hide=0)
    ownwant(escape(item_id), update)
    return redirect_back('/scarf/' + escape(item_id))

@app.route('/scarf/<item_id>/wonttrade')
def wonttrade(item_id):
    update = dict(willtrade=0)
    ownwant(escape(item_id), update)
    return redirect_back('/scarf/' + escape(item_id))

@app.route('/scarf/<item_id>/willtrade')
def willtrade(item_id):
    update = dict(own=1, hidden=0, willtrade=1)
    ownwant(escape(item_id), update)
    return redirect_back('/scarf/' + escape(item_id))

@app.route('/scarf/<item_id>/want')
def want(item_id):
    update = dict(want=1)
    ownwant(escape(item_id), update)
    return redirect_back('/scarf/' + escape(item_id))

@app.route('/scarf/<item_id>/dontwant')
def dontwant(item_id):
    update = dict(want=0)
    ownwant(escape(item_id), update)
    return redirect_back('/scarf/' + escape(item_id))

# TODO move to user object
def ownwant(item_id, values):
    moditem = siteitem(item_id)
    try:
        moditem = siteitem(item_id)
    except: #FIXME
        return

    try:
        user = siteuser(session['username'])
    except NoUser:
        return

    result = user.query_collection(item_id)

    try:
        iuid = result[0]
    except IndexError: 
        iuid=0

    update = dict(uid=iuid, userid=user.uid, scarfid=moditem.uuid)
    update.update(values)

    sql = upsert("ownwant", \
                 **update)

    data = doupsert(sql)

    sql = delete('ownwant', **{ 'own': '0', 'willtrade': '0', 'want': '0', 'hidden': '0' })
    result = doselect(sql)

    return 
