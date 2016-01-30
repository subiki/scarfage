from scarf import app
from flask import flash, render_template, session, request, redirect
from scarflib import pagedata, NoItem, NoUser, siteuser, siteitem, redirect_back, item_by_uid, user_by_uid, send_pm, add_tradeitem, pmessage, trademessage, messagestatus, tradeitem, tradestatus, deobfuscate, obfuscate
from main import page_not_found

# fix these URLs s/pm/trade/
@app.route('/user/<username>/pm/<messageid>/accept/<item>')
def accepttradeitem(username, messageid, item):
    pd = pagedata()

    if not pd.authuser.username == username:
        return page_not_found(404)

    if 'username' in session:
        try:
            ti = tradeitem(item)
        except:
            return page_not_found(404)

        try:
            t = trademessage.create(deobfuscate(messageid))
        except:
            return page_not_found(404)

        ti.accept()

    return redirect_back('index')

@app.route('/user/<username>/pm/<messageid>/reject/<item>')
def rejecttradeitem(username, messageid, item):
    pd = pagedata()

    if not pd.authuser.username == username:
        return page_not_found(404)

    # TODO: this doesn't check messageid...
    if 'username' in session:
        try:
            t = tradeitem(item)
            t.reject()
        except NoItem:
            return page_not_found(404)

    return redirect_back('index')

@app.route('/user/<username>/pm/<messageid>/settle')
def settletrade(username, messageid):
    pd = pagedata()

    if not pd.authuser.username == username:
        return page_not_found(404)

    if 'username' in session:
        try:
            t = trademessage.create(deobfuscate(messageid))
            t.settle()
        except NoItem:
            return page_not_found(404)

    return redirect_back('index')

@app.route('/user/<username>/pm/<messageid>/reject')
def rejecttrade(username, messageid):
    pd = pagedata()

    if not pd.authuser.username == username:
        return page_not_found(404)

    if 'username' in session:
        try:
            t = trademessage.create(deobfuscate(messageid))
            t.reject()
        except NoItem:
            return page_not_found(404)

    return redirect_back('index')


@app.route('/user/<username>/trade/<itemid>/debug', methods=['GET'], defaults={'debug': True})
@app.route('/user/<username>/trade/<itemid>', methods=['GET', 'POST'], defaults={'debug': False})
def trade(username, itemid, debug):
    pd = pagedata()

    try:
        pd.tradeuser = siteuser.create(username)
    except (NoItem, NoUser):
        return page_not_found(404)

    if 'username' in session:
        if request.method == 'POST':
            items = request.form.getlist('item')
            message = request.form['body']
            subject = request.form['subject']

            try:
                parent = request.form['parent']
            except:
                parent = None

            if message and subject:
                messageid = send_pm(pd.authuser.uid, pd.tradeuser.uid, subject, message, messagestatus['unread_trade'], parent)

                for item in items:
                    add_tradeitem(item, messageid, pd.authuser.uid, tradestatus['accepted'])

                add_tradeitem(siteitem(itemid).uid, messageid, pd.tradeuser.uid, tradestatus['unmarked'])

                if messageid:
                    flash('Submitted trade request!')
                    return redirect('/user/' + pd.authuser.username + '/pm/' + obfuscate(messageid))

            return redirect('/item/' + itemid)

    pd.title = "Trade for " + itemid

    try:
        pd.authuser.ownwant = pd.authuser.query_collection(itemid)
    except AttributeError:
        pass

    try:
        pd.tradeuser.ownwant = pd.tradeuser.query_collection(itemid)
        pd.item = siteitem(itemid)
    except (NoItem, NoUser):
        return page_not_found(404)

    if debug:
        if 'username' in session and pd.authuser.accesslevel == 255:
            pd.debug = dbg(pd)

    return render_template('trade.html', pd=pd)
