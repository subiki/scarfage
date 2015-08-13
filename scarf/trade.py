from scarf import app
from flask import escape, flash, render_template, session, request, redirect
from scarflib import pagedata, NoItem, NoUser, siteuser, siteitem, redirect_back, item_by_uid, user_by_uid, send_pm, add_tradeitem, pmessage, trademessage, messagestatus, tradeitem, tradestatus
from main import page_not_found

# fix these URLs s/pm/trade/
@app.route('/user/<username>/pm/<messageid>/accept/<item>')
def accepttradeitem(username, messageid, item):
    pd = pagedata()

    if not pd.authuser.username == username:
        return page_not_found(404)

    if 'username' in session:
        try:
            ti = tradeitem(escape(item))
        except:
            return page_not_found(404)

        try:
            t = trademessage.create(escape(messageid))
        except:
            return page_not_found(404)

        ti.accept()

    return redirect_back('index')

@app.route('/user/<username>/pm/<messageid>/reject/<item>')
def rejecttradeitem(username, messageid, item):
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

@app.route('/user/<username>/pm/<messageid>/settle')
def settletrade(username, messageid):
    pd = pagedata()

    if not pd.authuser.username == username:
        return page_not_found(404)

    if 'username' in session:
        t = trademessage.create(escape(messageid))
        t.settle()
            #return page_not_found(404)

    return redirect_back('index')

@app.route('/user/<username>/pm/<messageid>/reject')
def rejecttrade(username, messageid):
    pd = pagedata()

    if not pd.authuser.username == username:
        return page_not_found(404)

    if 'username' in session:
        try:
            t = trademessage.create(escape(messageid))
            t.reject()
        except:
            return page_not_found(404)

    return redirect_back('index')

@app.route('/user/<username>/trade/<itemid>', methods=['GET', 'POST'])
def trade(username, itemid):
    pd = pagedata()

    try:
        pd.tradeuser = siteuser.create(escape(username))
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
                parent = 0

            if items and message and subject:
                messageid = send_pm(pd.authuser.uid, pd.tradeuser.uid, subject, message, messagestatus['unread_trade'], parent)

                for item in items:
                    add_tradeitem(item, messageid, pd.authuser.uid, tradestatus['accepted'])

                add_tradeitem(siteitem(itemid).uid, messageid, pd.tradeuser.uid, tradestatus['unmarked'])

                if messageid:
                    flash('Submitted trade request!')
                    return redirect('/user/' + pd.authuser.username + '/pm/' + str(messageid))

            return redirect('/item/' + itemid)

    pd.title = "Trade for " + itemid

    try:
        pd.authuser.pop_collection()
        pd.authuser.ownwant = pd.authuser.query_collection(escape(itemid))
    except AttributeError:
        pass

    try:
        pd.tradeuser.pop_collection()
        pd.tradeuser.ownwant = pd.tradeuser.query_collection(escape(itemid))
        pd.item = siteitem(escape(itemid))
    except (NoItem, NoUser):
        return page_not_found(404)

    return render_template('trade.html', pd=pd)
