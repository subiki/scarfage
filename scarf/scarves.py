import os.path
from scarf import app
from flask import redirect, url_for, request, render_template, session, escape, flash
from werkzeug import secure_filename
from scarflib import check_login

def get_upload(f, name):
    if not f.filename == '':
        newname = name + os.path.splitext(f.filename)[1]
        try:
            f.save('/srv/data/web/vhosts/default/static/uploads/' + secure_filename(newname))
        except:
            flash('Error uploading ' + f.filename)
            return

        flash('Uploaded ' + f.filename)

@app.route('/scarf/<scarf_id>')
def show_post(scarf_id):
    if check_login():
        return render_template('scarf.html', title=scarf_id, scarfname=scarf_id, user=session['username'])
    else:
        return render_template('scarf.html', title=scarf_id, scarfname=scarf_id)

@app.route('/scarf/newscarf', methods=['GET', 'POST'])
def newscarf():
    if request.method == 'POST':
        if not check_login():
            flash('You must be logged in to create a scarf.')
            return redirect(url_for('/newuser'))

        if request.form['name'] == '':
            flash('This scarf has no name?')
            return redirect('/scarf/newscarf')

        flash('Adding scarf...')

        get_upload(request.files['front'], escape(request.form['name']) + "_front")
        get_upload(request.files['back'], escape(request.form['name']) + "_back")

        return redirect('/scarf/' + escape(request.form['name']))

    if check_login():
        return render_template('newscarf.html', title="Add New Scarf", user=session['username'])
    else:
        return render_template('newscarf.html', title="Add New Scarf")
