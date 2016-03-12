import MySQLdb
import socket
from time import time
import datetime
import inspect
import random
import string
import logging

from .. import config

logger = logging.getLogger(__name__)

# based on 
# https://code.activestate.com/recipes/280653-efficient-database-trees/
# PSF License

"""CREATE TABLE tree(ref int PRIMARY KEY AUTO_INCREMENT, parent int,
lhs int, rhs int, name varchar(255), UNIQUE INDEX(name))"""
class Tree(object):
    class Anon: pass
    
    def __init__(self, root):
        get_db()
        self.conn = db 

        try:
            self.retrieve(root)
        except IndexError:
            self.create_root(root)
    
    def insert_siblings(self, names, siblingname):
        self.conn.begin()
        sibling = self.retrieve(siblingname)
        cur = self.conn.cursor()
        cur.execute("UPDATE tree SET lhs = lhs + %s WHERE lhs > %s", (len(names)*2, sibling.rhs))
        cur.execute("UPDATE tree SET rhs = rhs + %s WHERE rhs > %s", (len(names)*2, sibling.rhs))
        
        cur.executemany("INSERT INTO tree SET (lhs, rhs, parent, name) VALUES  (%s, %s, %s, %s)",
                        [(sibling.rhs + 2*offset + 1,
                          sibling.rhs + 2*offset + 2,
                          sibling.parent, name) for offset, name in enumerate(names)])
        self.conn.commit()

    def insert_children(self, names, parentname):
        self.conn.begin()
        parent = self.retrieve(parentname)
        cur = self.conn.cursor()
        cur.execute("UPDATE tree SET lhs = lhs + %s WHERE lhs >= %s", (len(names)*2, parent.rhs))
        cur.execute("UPDATE tree SET rhs = rhs + %s WHERE rhs >= %s", (len(names)*2, parent.rhs))
        
        cur.executemany("INSERT INTO tree (lhs, rhs, parent, name) VALUES (%s, %s, %s, %s)",
                        [(parent.rhs + 2*offset,
                          parent.rhs + 2*offset + 1,
                          parent.ref, name) for offset, name in enumerate(names)])
        self.conn.commit()

    def rename(self, nodename, newname):
        self.conn.begin()
        node = self.retrieve(nodename)
        cur = self.conn.cursor()
        cur.execute("UPDATE tree SET name = %s WHERE name = %s", (newname, nodename))
        self.conn.commit()

    def delete(self, nodename):
        self.conn.begin()
        node = self.retrieve(nodename)
        cur = self.conn.cursor()
        cur.execute("DELETE FROM tree WHERE lhs BETWEEN %s AND %s", (node.lhs, node.rhs))
        diff = node.rhs - node.lhs + 1;
        cur.execute("UPDATE tree SET lhs = lhs - %s WHERE lhs > %s", (diff, node.rhs))
        cur.execute("UPDATE tree SET rhs = rhs - %s WHERE rhs > %s", (diff, node.rhs))
        self.conn.commit()
        return True

    def create_root(self, name):
        self.conn.begin()
        cur = self.conn.cursor()
        cur.execute("SELECT MAX(rhs) FROM tree");
        maxrhs = cur.fetchall()[0][0]
        if maxrhs is None: maxrhs = 1
        else: maxrhs = int(maxrhs)
        cur.execute("INSERT INTO tree (lhs, rhs, parent, name) VALUES (%s, %s, NULL, %s)", (maxrhs+1, maxrhs+2,name))
        self.conn.commit()

    def retrieve(self, name):
        cur = self.conn.cursor()
        cur.execute("SELECT ref, lhs, rhs, parent FROM tree WHERE name = %s", (name,))
        result = cur.fetchall()[0]
        retval = self.Anon()
        retval.name = name
        retval.ref = int(result[0])
        retval.lhs = int(result[1])
        retval.rhs = int(result[2])
        if(result[3]):
            retval.parent = int(result[3])
        else:
            retval.parent = None
        return retval

    def draw_tree(self, rootname):
        root = self.retrieve(rootname)
        cur = self.conn.cursor()
        cur.execute(
            """SELECT COUNT(t2.name) AS indentation, t1.name 
            FROM tree AS t1, tree AS t2
            WHERE t1.lhs BETWEEN t2.lhs AND t2.rhs
            AND t2.lhs BETWEEN %s AND %s
            GROUP BY t1.name
            ORDER BY t1.lhs""", (root.lhs, root.rhs))
        res = list()
        for result in cur.fetchall():
            res.append((result[1], int(result[0]-1)))
        return res

    def all_children_of(self, rootname):
        cur = self.conn.cursor()
        cur.execute(
            """SELECT t1.name FROM tree AS t1, tree AS t2
            WHERE t1.lhs BETWEEN t2.lhs AND t2.rhs AND t1.name != t2.name AND t2.name = %s
            ORDER BY t1.lhs""", (rootname,))
        return [result[0] for result in cur.fetchall()]

    def exact_children_of(self, rootname):
        cur = self.conn.cursor()
        cur.execute(
            """SELECT t1.name FROM tree AS t1, tree AS t2
            WHERE t1.parent = t2.ref AND t2.name = %s
            ORDER BY t1.lhs""", (rootname,))
        return [result[0] for result in cur.fetchall()]
    
    def all_siblings_of(self, siblingname):
        cur = self.conn.cursor()
        cur.execute(
            """SELECT t1.name FROM tree AS t1, tree AS t2
            WHERE t1.parent = t2.parent AND t2.name = %s AND t1.name != %s
            ORDER BY t1.lhs""", (siblingname, siblingname))
        return [result[0] for result in cur.fetchall()]
    
    def leaves_below(self, rootname):
        cur = self.conn.cursor()
        cur.execute(
            """SELECT t1.name FROM tree AS t1, tree AS t2
            WHERE t1.lhs BETWEEN t2.lhs AND t2.rhs AND t1.lhs + 1 = t1.rhs AND t2.name = %s
            ORDER BY t1.lhs""", (rootname,))
        return [result[0] for result in cur.fetchall()]

    def parent_of(self, childname):
        cur = self.conn.cursor()
        cur.execute(
            """SELECT t1.name FROM tree AS t1, tree AS t2
            WHERE t1.ref = t2.parent AND t2.name = %s""", (childname,))
        return cur.fetchall()[0][0]
    
    def path_to(self, childname):
        cur = self.conn.cursor()
        cur.execute(
            """SELECT t1.name FROM tree AS t1, tree AS t2
            WHERE t2.lhs BETWEEN t1.lhs AND t1.rhs AND t2.name = %s
            ORDER BY t1.lhs""", (childname,))
        return [result[0] for result in cur.fetchall()]

    def reparent(self, node, parent):
        if parent == self.parent_of(node):
            logger.error('reparent: null op!')
            return
            
        if node == parent:
            logger.error('reparent: attempted to reparent into myself!')
            return

        if node in self.all_children_of('parent'):
            logger.error('reparent: attempted to reparent into a child!')
            return

        temp_node = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(20))

        self.insert_children([temp_node], parent)

        children = self.exact_children_of(node)
        for child in children:
            self.reparent(child, temp_node)

        Tree(self.root).delete(node)
        self.rename(temp_node, node)

db = None

def read(table, **kwargs):
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    logger.error("deprecated function read called by " + calframe[1][3])
 
    """ Generates SQL for a SELECT statement matching the kwargs passed. """
    sql = list()
    sql.append("SELECT * FROM %s " % table)
    if kwargs:
        sql.append("WHERE " + " AND ".join("%s = '%s'" % (k, v) for k, v in kwargs.iteritems()))
    sql.append(";")
    return "".join(sql)

def upsert(table, **kwargs):
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    logger.error("deprecated function upsert called by " + calframe[1][3])
    
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

    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    logger.error("deprecated function delete called by " + calframe[1][3])


    sql = list()
    sql.append("DELETE FROM %s " % table)
    sql.append("WHERE " + " AND ".join("%s = '%s'" % (k, v) for k, v in kwargs.iteritems()))
    sql.append(";")
    return "".join(sql)

def get_db():
    global db

    try:
        if db is None:
            logger.info("Connecting to db host")
            db = MySQLdb.connect(host=config.DBHOST, db=config.DBNAME, user=config.DBUSER, passwd=config.DBPASS)

            db.set_character_set('utf8')

    except MySQLdb.MySQLError as e:
        db = None
        logger.error("Cannot connect to database. MySQL error: " + str(e))
        raise

def doupsert(query):
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    logger.error("deprecated function doupsert called by " + calframe[1][3])

    get_db()
    cursor = db.cursor()
    cursor.execute('SET NAMES utf8;')
    cursor.execute('SET CHARACTER SET utf8;')
    cursor.execute('SET character_set_connection=utf8;')

    cursor.execute(query)
    db.commit()
    cursor.close()
    data = cursor.lastrowid

    return data

def doquery(query, data=None, select=True):
    global db

    try:
        if db is None:
            logger.info("Connecting to db host")
            db = MySQLdb.connect(host=config.DBHOST, db=config.DBNAME, user=config.DBUSER, passwd=config.DBPASS)

            db.set_character_set('utf8')
            cursor = db.cursor()
            cursor.execute('SET NAMES utf8;')
            cursor.execute('SET CHARACTER SET utf8;')
            cursor.execute('SET character_set_connection=utf8;')
            db.commit()
            cursor.close()

        cur = db.cursor()
        cur.execute(query, data)

        #logger.info((query, data, 'rows: ' + str(cur.rowcount)))

        if select:
            data = cur.fetchall()
        else:
            data = cur.lastrowid

        db.commit()
        cur.close()

        return data

    except MySQLdb.MySQLError as e:
        db = None
        logger.error("Cannot connect to database. MySQL error: " + str(e))
        raise
