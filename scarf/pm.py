from scarf import app
from flask import flash, render_template, session, request, redirect
from scarflib import pagedata, NoItem, NoUser, siteuser, redirect_back, user_by_uid, send_pm, pmessage, messagestatus, trademessage, deobfuscate, obfuscate
from main import page_not_found
from debug import dbg


@app.route('/user/<username>/pm/<messageid>/debug', defaults={'debug': True})
@app.route('/user/<username>/pm/<messageid>', defaults={'debug': False})
def viewpm(username, messageid, debug):
    pd = pagedata()

    if not 'username' in session or pd.authuser.username != username:
        return page_not_found(404)

    if 'username' in session:
        pm = trademessage.create(deobfuscate(messageid))
        pm.read()

        if pm.messagestatus < messagestatus['unread_pm']:
            pm = trademessage.create(messageid)

        pd.pm = pm

        if debug:
            if 'username' in session and pd.authuser.accesslevel == 255:
                pd.debug = dbg(pd)

        return render_template('pm.html', pd=pd)
 
@app.route('/user/<username>/pm/debug', methods=['GET'], defaults={'debug': True})
@app.route('/user/<username>/pm', methods=['GET', 'POST'], defaults={'debug': False})
def pm(username, debug):
    pd = pagedata()

    try:
        pd.recipient = siteuser.create(username)
    except (NoItem, NoUser):
        return page_not_found(404)

    if 'username' in session:
        if request.method == 'POST':
            message = request.form['body']
            subject = request.form['subject']

            try:
                parent = deobfuscate(request.form['parent'])
            except:
                parent = 0

            if message and subject:
                messageid = send_pm(pd.authuser.uid, pd.recipient.uid, subject, message, messagestatus['unread_pm'], parent)

                if messageid:
                    flash('Message sent!')
                    return redirect('/user/' + pd.authuser.username + '/pm/' + obfuscate((messageid)))
            else:
# TODO re-fill form
                flash('No message or subject')
                return redirect_back('/user/' + username + '/pm')

    if debug:
        if 'username' in session and pd.authuser.accesslevel == 255:
            pd.debug = dbg(pd)

    return render_template('sendpm.html', pd=pd)
