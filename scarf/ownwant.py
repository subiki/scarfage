from scarf import app
from flask import redirect, url_for, request, render_template, session, escape, flash
from scarflib import check_login, check_scarf
from sql import upsert, doupsert, read, doselect
from profile import get_userinfo
from scarflib import redirect_back

@app.route('/scarf/<scarf_id>/remove')
def remove(scarf_id):
    # TODO actually remove these at some point
    ownwant(scarf_id, 4, 0)
    ownwant(scarf_id, 5, 0)
    ownwant(scarf_id, 6, 0)
    ownwant(scarf_id, 7, 0)
    return redirect_back('/scarf/scarf/' + escape(scarf_id))

@app.route('/scarf/<scarf_id>/have')
def have(scarf_id):
    ownwant(scarf_id, 4, 1)
    ownwant(scarf_id, 6, 0)
    return redirect_back('/scarf/scarf/' + escape(scarf_id))

@app.route('/scarf/<scarf_id>/hide')
def hide(scarf_id):
    ownwant(scarf_id, 5, 0)
    ownwant(scarf_id, 7, 1)
    return redirect_back('/scarf/scarf/' + escape(scarf_id))

@app.route('/scarf/<scarf_id>/show')
def show(scarf_id):
    ownwant(scarf_id, 7, 0)
    return redirect_back('/scarf/scarf/' + escape(scarf_id))

@app.route('/scarf/<scarf_id>/wonttrade')
def wonttrade(scarf_id):
    ownwant(scarf_id, 5, 0)
    return redirect_back('/scarf/scarf/' + escape(scarf_id))

@app.route('/scarf/<scarf_id>/willtrade')
def willtrade(scarf_id):
    ownwant(scarf_id, 4, 1)
    ownwant(scarf_id, 5, 1)
    ownwant(scarf_id, 7, 0)
    return redirect_back('/scarf/scarf/' + escape(scarf_id))

@app.route('/scarf/<scarf_id>/want')
def want(scarf_id):
    ownwant(scarf_id, 4, 0)
    ownwant(scarf_id, 6, 1)
    return redirect_back('/scarf/' + escape(scarf_id))

@app.route('/scarf/<scarf_id>/dontwant')
def dontwant(scarf_id):
    ownwant(scarf_id, 6, 0)
    return redirect_back('/scarf/' + escape(scarf_id))

def ownwant(scarf_id, index, value):
    scarf = check_scarf(escape(scarf_id))
    if scarf == False:
        return

    if check_login():
        userinfo = get_userinfo(session['username'])
        try:
            uid = userinfo[0][0]
        except IndexError:
            return -1

        sql = read('ownwant', **{"userid": uid, "scarfid": scarf[1]})
        result = doselect(sql)
        app.logger.debug(result)

        iuid=0
        try:
            iuid = result[0][0]
        except IndexError: 
            iuid=0

        if index == 4:
            sql = upsert("ownwant", \
                         uid=iuid,
                         userid=uid, \
                         scarfid=scarf[1], \
                         own=value)

        if index == 5:
            sql = upsert("ownwant", \
                         uid=iuid,
                         userid=uid, \
                         scarfid=scarf[1], \
                         willtrade=value)

        if index == 6:
            sql = upsert("ownwant", \
                         uid=iuid,
                         userid=uid, \
                         scarfid=scarf[1], \
                         want=value)
        if index == 7:
            sql = upsert("ownwant", \
                         uid=iuid,
                         userid=uid, \
                         scarfid=scarf[1], \
                         hidden=value)

        data = doupsert(sql)

    return 
