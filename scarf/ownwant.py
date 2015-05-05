from scarflib import siteuser

from scarf import app
from flask import redirect, url_for, request, render_template, session, escape, flash
from scarflib import check_scarf
from sql import upsert, doupsert, read, doselect, delete
from scarflib import redirect_back

@app.route('/scarf/<scarf_id>/donthave')
def donthave(scarf_id):
    update = dict(willtrade=0, own=0)
    ownwant(scarf_id, update)
    return redirect_back('/scarf/' + escape(scarf_id))

@app.route('/scarf/<scarf_id>/have')
def have(scarf_id):
    update = dict(own=1)
    ownwant(scarf_id, update)
    return redirect_back('/scarf/' + escape(scarf_id))

@app.route('/scarf/<scarf_id>/hide')
def hide(scarf_id):
    update = dict(hide=1)
    ownwant(scarf_id, update)
    return redirect_back('/scarf/' + escape(scarf_id))

@app.route('/scarf/<scarf_id>/show')
def show(scarf_id):
    update = dict(hide=0)
    ownwant(scarf_id, update)
    return redirect_back('/scarf/' + escape(scarf_id))

@app.route('/scarf/<scarf_id>/wonttrade')
def wonttrade(scarf_id):
    update = dict(willtrade=0)
    ownwant(scarf_id, update)
    return redirect_back('/scarf/' + escape(scarf_id))

@app.route('/scarf/<scarf_id>/willtrade')
def willtrade(scarf_id):
    update = dict(own=1, hidden=0, willtrade=1)
    ownwant(scarf_id, update)
    return redirect_back('/scarf/' + escape(scarf_id))

@app.route('/scarf/<scarf_id>/want')
def want(scarf_id):
    update = dict(want=1)
    ownwant(scarf_id, update)
    return redirect_back('/scarf/' + escape(scarf_id))

@app.route('/scarf/<scarf_id>/dontwant')
def dontwant(scarf_id):
    update = dict(want=0)
    ownwant(scarf_id, update)
    return redirect_back('/scarf/' + escape(scarf_id))

def ownwant(scarf_id, values):
    scarf = check_scarf(escape(scarf_id))
    if scarf == False:
        return

    try:
        user = siteuser(escape(request.form['username']))
    except NoUser:
        return

    sql = read('ownwant', **{"userid": user.uid, "scarfid": scarf[1]})
    result = doselect(sql)
    app.logger.debug(result)

    iuid=0
    try:
        iuid = result[0][0]
    except IndexError: 
        iuid=0

    update = dict(uid=iuid, userid=user.uid, scarfid=scarf[1])
    update.update(values)

    sql = upsert("ownwant", \
                 **update)

    data = doupsert(sql)

    sql = delete('ownwant', **{ 'own': '0', 'willtrade': '0', 'want': '0', 'hidden': '0' })
    result = doselect(sql)

    return 
