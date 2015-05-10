from scarf import app
from flask import escape, flash, render_template, session, request, redirect
from scarflib import pagedata, NoItem, NoUser, siteuser, siteitem, redirect_back, item_by_uid, user_by_uid, send_pm, add_tradeitem, pmessage, trademessage, messagestatus, tradeitem, tradestatus
from main import page_not_found

@app.route('/user/<username>/pm/<messageid>/accept/<item>')
def accepttrade(username, messageid, item):
    pd = pagedata()

    if not pd.authuser.username == username:
        return page_not_found(404)

    if 'username' in session:
        try:
            ti = tradeitem(escape(item))
        except:
            return page_not_found(404)

        try:
            t = trademessage(escape(messageid))
        except:
            return page_not_found(404)

        ti.accept()

    return redirect_back('index')

@app.route('/user/<username>/pm/<messageid>/reject/<item>')
def rejecttrade(username, messageid, item):
    pd = pagedata()

    if not pd.authuser.username == username:
        return page_not_found(404)

    if 'username' in session:
        try:
            t = tradeitem(escape(item))
            t.reject()
        except:
            return page_not_found(404)

    return redirect_back('index')



@app.route('/user/<username>/pm/<messageid>')
def viewpm(username, messageid):
    pd = pagedata()

    if not 'username' in session or not pd.authuser.username == username:
        return page_not_found(404)

    if 'username' in session:
        t = trademessage(escape(messageid))

        pd.pm = t

        settle = True
        for item in t.items:
            if (item.acceptstatus != tradestatus['accepted']):
                settle = False

        if settle == True:
            pd.pm.status = messagestatus['closed_trade']

    return render_template('pm.html', pd=pd)
 

@app.route('/user/<username>/trade/<itemid>', methods=['GET', 'POST'])
def trade(username, itemid):
    pd = pagedata()

    try:
        pd.tradeuser = siteuser(escape(username))
    except (NoItem, NoUser):
        return page_not_found(404)

    if 'username' in session:
        if request.method == 'POST':
            items = request.form.getlist('item')
            message = request.form['body']

            if items and message:
                messageid = send_pm(pd.authuser.uid, pd.tradeuser.uid, message, 0)

                for item in items:
                    add_tradeitem(item, messageid, pd.authuser.uid, tradestatus['accepted'])

                add_tradeitem(siteitem(itemid).uid, messageid, pd.tradeuser.uid, tradestatus['unmarked'])

                if messageid:
                    flash('Submitted trade request!')
                    return redirect('/user/' + pd.authuser.username + '/pm/' + str(messageid))

            return redirect('/item/' + itemid)

    pd.title = "Trade for " + itemid

    try:
        pd.authuser.collection = pd.authuser.get_collection()
        pd.authuser.ownwant = pd.authuser.query_collection(escape(itemid))
    except AttributeError:
        pass

    try:
        pd.tradeuser.collection = pd.tradeuser.get_collection()
        pd.tradeuser.ownwant = pd.tradeuser.query_collection(escape(itemid))
        pd.item = siteitem(escape(itemid))
    except (NoItem, NoUser):
        return page_not_found(404)

    return render_template('trade.html', pd=pd)
