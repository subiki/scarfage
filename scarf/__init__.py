from flask import Flask
app = Flask(__name__)

@app.route('/')
def index():
    return 'Index Page'

@app.route('/hello')
def hello():
    return 'Hello World'

@app.route('/monkey')
def monkey():
    return 'MONKEYS'

if __name__ == '__main__':
    app.debug = True
    app.run()
