from scarf import app
from flask import flash, render_template, session, request, redirect
from core import NoItem, NoUser, SiteUser, SiteItem, redirect_back, item_by_uid, user_by_uid, send_pm, add_tradeitem, PrivateMessage, TradeMessage, messagestatus, TradeItem, tradeitemstatus, deobfuscate, obfuscate
import core
from main import page_not_found, PageData

@app.route('/user/<username>/trade/<messageid>/<action>/<item>')
@app.route('/user/<username>/trade/<messageid>/<action>')
def accepttradeitem(username, messageid, action, item=None):
    pd = PageData()

    if not pd.authuser.username == username:
        return page_not_found(404)

    if 'username' in session:
        if item:
            try:
                ti = TradeItem(item)
            except NoItem:
                return page_not_found(404)

            if action == "accept":
                ti.accept()
            elif action == "reject":
                ti.reject()
            else:
                return page_not_found(404)
        else:
            try:
                t = TradeMessage.create(deobfuscate(messageid))
            except NoItem:
                return page_not_found(404)

            if action == "settle":
                t.settle()
            elif action == "cancel":
                t.cancel()
            elif action == "reject":
                t.reject()
            elif action == "reopen":
                t.unread()
                t.read()
            elif action == "add":
                flash('Coming soon...')
                return redirect_back('/')
            else:
                return page_not_found(404)

    return redirect_back('index')

@app.route('/user/<username>/modifytrade/<messageid>', methods=['GET', 'POST'])
@app.route('/user/<username>/trade/<itemid>', methods=['GET', 'POST'])
def trade(username, itemid=None, messageid=None):
    pd = PageData()

    status = messagestatus['unread_trade']

    try:
        pd.tradeuser = SiteUser.create(username)
    except NoUser:
        return page_not_found(404)

    if 'username' in session:
        if request.method == 'POST':
            authuseritems = request.form.getlist('authuseritem')
            tradeuseritems = request.form.getlist('tradeuseritem')
            message = request.form['body']
            subject = request.form['subject']

            if 'parent' in request.form:
                parent = request.form['parent']
            else:
                if messageid:
                    parent = core.deobfuscate(messageid)
                    messageid = parent
                    status = messagestatus['unread_pm']
                    flashmsg = 'Message sent!'
                else:
                    parent = None
                    messageid = None
                    flashmsg = 'Submitted trade request!'

            if message and subject:
                pmid = send_pm(pd.authuser.uid, pd.tradeuser.uid, subject, message, status, parent)

                if not messageid:
                    messageid = pmid
                elif tradeuseritems or authuseritems:
                    flashmsg = 'Trade updated'

                for item in authuseritems:
                    add_tradeitem(item, messageid, pd.authuser.uid, tradeitemstatus['accepted'])

                for item in tradeuseritems:
                    add_tradeitem(item, messageid, pd.tradeuser.uid, tradeitemstatus['unmarked'])

                flash(flashmsg)
                return redirect('/user/' + pd.authuser.username + '/pm/' + obfuscate(messageid))

            if message == '':
                flash('Please add a message')

            return redirect_back('/')

    pd.title = "Trading with {}".format(username)

    try:
        pd.authuser.ownwant = pd.authuser.query_collection(itemid)
    except AttributeError:
        pass

    try:
        pd.tradeuser.ownwant = pd.tradeuser.query_collection(itemid)
        pd.item = SiteItem.create(itemid)
    except NoItem:
        if messageid:
            try:
                pd.trademessage = TradeMessage.create(deobfuscate(messageid))
            except NoItem:
                return page_not_found(404)
        else:
            return page_not_found(404)

    return render_template('trade.html', pd=pd)
