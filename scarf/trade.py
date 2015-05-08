from scarf import app
from flask import escape, flash, render_template, session, request, redirect
from scarflib import pagedata, NoItem, NoUser, siteuser, siteitem, redirect_back, item_by_uid, user_by_uid
from main import page_not_found

from sql import upsert, doupsert, read, doquery

messagestatus = {'active_trade': 0, 'closed_trade': 1, 'unread_pm': 2, 'read_pm': 3}

#+------------+---------+------+-----+---------+----------------+
#| Field      | Type    | Null | Key | Default | Extra          |
#+------------+---------+------+-----+---------+----------------+
#| uid        | int(32) | NO   | PRI | NULL    | auto_increment |
#| fromuserid | int(32) | NO   |     | NULL    |                |
#| touserid   | int(32) | NO   |     | NULL    |                |
#| message    | text    | NO   |     | NULL    |                |
#| status     | int(8)  | NO   |     | NULL    |                |
#+------------+---------+------+-----+---------+----------------+

class pmessage:
    def __init__(self, messageid):
        sql = read('messages', **{"messageid": messageid})
        result = doquery(sql)
        app.logger.debug(result)

        self.uid = result[0]
        self.from_uid = result[1]
        self.to_uid = result[2]
        self.message = result[3]
        self.status = result[4]

class tradeitem:
    def __init__(self):
        self.uid = 0
        self.itemid = 0
        self.messageid = 0
        self.userid = 0
        self.acceptstatus = 0

#+--------------+------------+------+-----+---------+----------------+
#| Field        | Type       | Null | Key | Default | Extra          |
#+--------------+------------+------+-----+---------+----------------+
#| uid          | int(32)    | NO   | PRI | NULL    | auto_increment |
#| itemid       | int(32)    | NO   |     | NULL    |                |
#| messageid    | int(32)    | NO   |     | NULL    |                |
#| userid       | int(32)    | NO   |     | NULL    |                |
#| acceptstatus | tinyint(1) | NO   |     | NULL    |                |
#+--------------+------------+------+-----+---------+----------------+
class trademessage(pmessage):
    def __init__(self, messageid):
        sql = read('messages', **{"uid": messageid})
        result = doquery(sql)

        try:
            self.uid = result[0][0]
            self.from_uid = result[0][1]
            self.to_uid = result[0][2]
            self.message = result[0][3]
            self.status = result[0][4]
        except IndexError:
            pass

        self.items = []

        sql = read('tradelist', **{"messageid": messageid})
        result = doquery(sql)

        for item in result:
            ti = tradeitem()
            ti.uid = item[0]
            ti.itemid = item[1]
            ti.messageid = item[2]
            ti.userid = item[3]
            ti.acceptstatus = item[4]
            ti.item = siteitem(item_by_uid(ti.itemid))
            ti.user = siteuser(user_by_uid(ti.userid))

            self.items.append(ti)

def send_pm(fromuserid, touserid, message, status):
    try:
        sql = upsert("messages", \
                     uid=0, \
                     fromuserid=fromuserid, \
                     touserid=touserid, \
                     message=message, \
                     status=status)
        data = doupsert(sql)
    except Exception as e:
        raise

    return data

def add_tradeitem(itemid, messageid, userid, acceptstatus):
    try:
        sql = upsert("tradelist", \
                     uid=0, \
                     itemid=itemid, \
                     messageid=messageid, \
                     userid=userid, \
                     acceptstatus=acceptstatus)
        data = doupsert(sql)
    except Exception as e:
        return False

    return True

@app.route('/user/<username>/pm/<messageid>')
def viewpm(username, messageid):
    pd = pagedata()

    if not pd.authuser.username == username:
        return page_not_found(404)

    if 'username' in session:
        t = trademessage(escape(messageid))

        app.logger.debug(t)

        pd.pm = t

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
                    add_tradeitem(item, messageid, pd.authuser.uid, messagestatus['active_trade'])

                add_tradeitem(siteitem(itemid).uid, messageid, pd.tradeuser.uid, messagestatus['active_trade'])

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
