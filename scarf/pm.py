from scarf import app
from flask import escape, flash, render_template, session, request, redirect
from scarflib import pagedata, NoItem, NoUser, siteuser, redirect_back, user_by_uid, send_pm, pmessage, messagestatus
from main import page_not_found

@app.route('/user/<username>/pm/<messageid>')
def viewpm(username, messageid):
    pd = pagedata()

    if not 'username' in session or not pd.authuser.username == username:
        return page_not_found(404)

    if 'username' in session:
        app.logger.debug(messageid)
        pm = pmessage(escape(messageid))

        pm.read()

        pd.pm = pm

    return render_template('pm.html', pd=pd)
 
@app.route('/user/<username>/pm', methods=['GET', 'POST'])
def pm(username):
    pd = pagedata()

    try:
        pd.recipient = siteuser(escape(username))
    except (NoItem, NoUser):
        return page_not_found(404)

    if 'username' in session:
        if request.method == 'POST':
            message = request.form['body']

            if message:
                messageid = send_pm(pd.authuser.uid, pd.recipient.uid, message, messagestatus['unread_pm'])

                if messageid:
                    flash('Message sent!')
                    return redirect('/user/' + pd.authuser.username + '/pm/' + str(messageid))
            else:
                return redirect('/user/' + username + '/pm')

    return render_template('sendpm.html', pd=pd)
