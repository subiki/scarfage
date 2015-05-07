from scarf import app
from flask import escape, flash, render_template, session, request
from scarflib import pagedata, NoItem, NoUser, siteuser, siteitem, redirect_back
from main import page_not_found

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

# insert into messages
#+------------+---------+------+-----+---------+----------------+
#| Field      | Type    | Null | Key | Default | Extra          |
#+------------+---------+------+-----+---------+----------------+
#| uid        | int(32) | NO   | PRI | NULL    | auto_increment |
#| fromuserid | int(32) | NO   |     | NULL    |                |
#| touserid   | int(32) | NO   |     | NULL    |                |
#| message    | text    | NO   |     | NULL    |                |
#| status     | int(8)  | NO   |     | NULL    |                |
#+------------+---------+------+-----+---------+----------------+

            for item in items:
                pass
# insert into tradelist
#+--------------+------------+------+-----+---------+----------------+
#| Field        | Type       | Null | Key | Default | Extra          |
#+--------------+------------+------+-----+---------+----------------+
#| uid          | int(32)    | NO   | PRI | NULL    | auto_increment |
#| itemid       | int(32)    | NO   |     | NULL    |                |
#| messageid    | int(32)    | NO   |     | NULL    |                |
#| userid       | int(32)    | NO   |     | NULL    |                |
#| acceptstatus | tinyint(1) | NO   |     | NULL    |                |
#+--------------+------------+------+-----+---------+----------------+
            return redirect_back('index')

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
