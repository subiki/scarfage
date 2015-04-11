import MySQLdb
from scarf import app
from flask import redirect, url_for

dbHost = 'localhost'
dbName = 'scarfage'
dbUser = 'scarfage'
dbPass = '4AybHApWa7n6VRp6'

def read(table, **kwargs):
    """ Generates SQL for a SELECT statement matching the kwargs passed. """
    sql = list()
    sql.append("SELECT * FROM %s " % table)
    if kwargs:
        sql.append("WHERE " + " AND ".join("%s = '%s'" % (k, v) for k, v in kwargs.iteritems()))
    sql.append(";")
    return "".join(sql)


def upsert(table, **kwargs):
    """ update/insert rows into objects table (update if the row already exists)
        given the key-value pairs in kwargs """
    keys = ["%s" % k for k in kwargs]
    values = ["'%s'" % v for v in kwargs.values()]
    sql = list()
    sql.append("INSERT INTO %s (" % table)
    sql.append(", ".join(keys))
    sql.append(") VALUES (")
    sql.append(", ".join(values))
    sql.append(") ON DUPLICATE KEY UPDATE ")
    sql.append(", ".join("%s = '%s'" % (k, v) for k, v in kwargs.iteritems()))
    sql.append(";")
    return "".join(sql)


def delete(table, **kwargs):
    """ deletes rows from table where **kwargs match """
    sql = list()
    sql.append("DELETE FROM %s " % table)
    sql.append("WHERE " + " AND ".join("%s = '%s'" % (k, v) for k, v in kwargs.iteritems()))
    sql.append(";")
    return "".join(sql)

def insert(query, ret):
    app.logger.debug(query)
    try:
        db = MySQLdb.connect(host=dbHost, db=dbName, user=dbUser, passwd=dbPass)

        cursor = db.cursor()
        cursor.execute(query)
        cursor.commit(query)
        cursor.close()
        if ret:
            data = cursor.fetch_row(maxrows=0)
        else:
            data = cursor.lastrowid

        db.close()

        return data

    except MySQLdb.MySQLError, err:
        app.logger.error("Cannot connect to database. MySQL error: " + str(err))
        return 

    app.logger.error("Cannot connect to database. MySQL error")
