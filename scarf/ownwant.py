from scarf import app
from core import SiteUser, NoUser, SiteItem, NoItem, redirect_back, OwnWant
from main import page_not_found

from flask import redirect, url_for, request, render_template, session, flash

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
        moditem = SiteItem(item_id)
    except NoItem:
        return page_not_found(404)

    try:
        user = SiteUser.create(session['username'])
    except (NoUser, KeyError):
        flash('You must be logged in to add items to a collection')
        return redirect('newuser')

    OwnWant(item_id, user.uid).update(values)
