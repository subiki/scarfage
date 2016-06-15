from scarf import app
from core import NoItem, NoUser, SiteUser, redirect_back, user_by_uid, send_pm, PrivateMessage, tradestatus, TradeMessage, deobfuscate, obfuscate
from main import page_not_found, PageData

from flask import flash, render_template, session, request, redirect

@app.route('/user/<username>/pm/<messageid>')
def viewpm(username, messageid):
    pd = PageData()
    dmid = deobfuscate(messageid)

    if not 'username' in session or pd.authuser.username != username or dmid is None:
        return render_template('pm_error.html', pd=pd)

    if 'username' in session:
        pm = TradeMessage.create(dmid)

        if session['username'] is pm.to_user:
            pd.tradeuser = pm.from_user
            pm.read(pm.to_user)
        else:
            pd.tradeuser = pm.to_user

        pd.pm = pm
        pd.title = pm.subject

        return render_template('pm.html', pd=pd)
 
@app.route('/user/<username>/pm', methods=['GET', 'POST'])
def pm(username):
    pd = PageData()

    try:
        pd.recipient = SiteUser.create(username)
    except (NoItem, NoUser):
        return page_not_found()

    if 'username' in session:
        if request.method == 'POST':
            message = request.form['body']
            subject = request.form['subject']

            if 'parent' in request.form:
                parent = deobfuscate(request.form['parent'])
            else:
                parent = None

            if message and subject:
                messageid = send_pm(pd.authuser.uid, pd.recipient.uid, subject, message, None, parent)

                if messageid:
                    flash('Message sent!')
                    if parent:
                        return redirect_back('/user/' + username + '/pm')
                    else:
                        return redirect('/user/' + pd.authuser.username + '/pm/' + obfuscate((messageid)))

            else:
# TODO re-fill form
                flash('No message or subject')
                return redirect_back('/user/' + username + '/pm')

    return render_template('sendpm.html', pd=pd)
