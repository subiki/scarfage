from scarf import app
from flask import redirect, url_for, request, render_template, session, escape, flash
from scarflib import check_login

@app.route('/scarf/<scarf_id>')
def show_post(scarf_id):
    return 'Post %s' % escape(scarf_id)

@app.route('/scarf/newscarf', methods=['GET', 'POST'])
def newscarf():
    if request.method == 'POST':
        if not check_login():
            flash('You must be logged in to create a scarf.')
            return redirect(url_for('/newuser'))

        flash('Creating scarf')
        return redirect(url_for('/scarf/' + request['name']))

    return render_template('newscarf.html', title="Add New Scarf", user=session['username'])
