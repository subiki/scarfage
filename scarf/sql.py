import MySQLdb
from scarf import app
from flask import redirect, url_for

dbHost = 'localhost'
dbName = 'scarfage'
dbUser = 'scarfage'
dbPass = '4AybHApWa7n6VRp6'

def do_sql(query):
    try:
        db = MySQLdb.connect(host=dbHost, db=dbName, user=dbUser, passwd=dbPass)

        cursor = db.cursor()
        cursor.execute(query)
        #data = cursor.fetch_row(maxrows=0)
        data = cursor.fetchone()
        db.close()

        app.logger.error("connected to db")
        return data
    except MySQLdb.MySQLError, err:
        app.logger.error("Cannot connect to database. MySQL error: " + str(err))
        return 


    app.logger.error("Cannot connect to database. MySQL error")
