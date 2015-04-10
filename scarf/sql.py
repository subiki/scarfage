import MySQLdb

dbHost = '127.0.0.1'
dbName = 'scarfage'
dbUser = 'scarfage'
dbPass = 'cwydPKmEykjZRyLSwLeBRMFTyAcMJl'

try:
    db = MySQLdb.connect(host=dbHost, db=dbName, user=dbUser, passwd=dbPass)
except MySQLdb.MySQLError, err:
    print "Cannot connect to database. MySQL error: " + str(err)
