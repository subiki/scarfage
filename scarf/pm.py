from scarf import app
from flask import flash, render_template, session, request, redirect
from scarflib import pagedata, NoItem, NoUser, siteuser, redirect_back, user_by_uid, send_pm, pmessage, messagestatus, trademessage
from main import page_not_found

@app.route('/user/<username>/pm/<messageid>')
def viewpm(username, messageid):
    pd = pagedata()

    if not 'username' in session or pd.authuser.username != username:
        return page_not_found(404)

    if 'username' in session:
        pm = trademessage.create(messageid)
        pm.read()
        pm.load_replies()

        if pm.messagestatus < messagestatus['unread_pm']:
            pm = trademessage.create(messageid)

        pd.pm = pm

        return render_template('pm.html', pd=pd)
 
@app.route('/user/<username>/pm', methods=['GET', 'POST'])
def pm(username):
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
                parent = request.form['parent']
            except:
                parent = 0

            if message and subject:
                messageid = send_pm(pd.authuser.uid, pd.recipient.uid, subject, message, messagestatus['unread_pm'], parent)

                if messageid:
                    flash('Message sent!')
                    return redirect('/user/' + pd.authuser.username + '/pm/' + str(messageid))
            else:
# TODO re-fill form
                flash('No message or subject')
                return redirect_back('/user/' + username + '/pm')

    return render_template('sendpm.html', pd=pd)
