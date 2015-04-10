from flask import Flask, abort, redirect, url_for, render_template, session, escape, request, flash

app = Flask(__name__)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html', title="Page not found", errorcode="404", errortext="File not found."), 404

@app.route('/error')
def error():
    return render_template('error.html', title="Error!", errortext="Oh noes!")

@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html', title="Scarfage", user=escape(session['username']))
    else:
        return render_template('index.html', title="Scarfage")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] != 'admin' or \
                request.form['password'] != 'secret':
            flash('Login unsuccessful. Check your username and password and try again.')
            return redirect(url_for('index'))
        else:
            session['username'] = escape(request.form['username'])
            flash('You were successfully logged in')
            return redirect(url_for('index'))
    return redirect(url_for('error'))

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    flash('You were successfully logged out')
    return redirect(url_for('index'))

@app.route('/user/<username>')
def show_user_profile(username):
    # show the user profile for that user
    return 'User %s' % username

@app.route('/post/<scarf_id>')
def show_post(post_id):
    # show the post with the given id, the id is an integer
    return 'Post %d' % post_id

# set the secret key.  keep this really secret:
app.secret_key = '\x8bN\xe5\xe8Q~p\xbdb\xe5\xa5\x894i\xb0\xd9\x07\x10\xe6\xa0\xe5\xbd\x1e\xf8'

if __name__ == '__main__':
    app.debug = True
    app.run()







