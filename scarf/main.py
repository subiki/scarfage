from scarf import app

from flask import render_template, session, escape

@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html', title="File not found", errorcode="404", errortext="File not found."), 404

@app.route('/error')
def error():
    return render_template('error.html', title="Error!", errortext="Oh noes!")

@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html', title="Scarfage", user=escape(session['username']))
    else:
        return render_template('index.html', title="Scarfage")
