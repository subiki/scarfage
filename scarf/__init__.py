from flask import Flask
app = Flask(__name__)

@app.route('/')
def index():
    return 'Index Page'

@app.route('/error')
def error():
    return render_template('error.html')

if __name__ == '__main__':
    app.debug = True
    app.run()
