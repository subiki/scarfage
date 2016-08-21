#!/usr/bin/env python2

import os, sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

import scarf
import flask
import logging
from scarf import app

logging.basicConfig(filename='util.log',level=logging.DEBUG)

try:
    username = sys.argv[1]
    level = int(sys.argv[2])
except IndexError:
    print "No username or accesslevel specified"
    sys.exit(1)
except ValueError:
    level = sys.argv[2]

if level not in scarf.core.accesslevels:
    print "Invalid accesslevel: {}".format(level)
    print "Valid accesslevels:"
    for accesslevel in scarf.core.accesslevels:
        print "  {}\t{}".format(accesslevel, scarf.core.accesslevels[accesslevel])
    sys.exit(2)

with app.test_request_context(''):
    try:
        siteuser = scarf.core.SiteUser.create(username)
    except scarf.core.NoUser:
        print "user {} doesn't exist, have you registered it yet?".format(username)
        sys.exit(3)

    prev = siteuser.accesslevel
    siteuser.newaccesslevel(level)
    print "user {}'s accesslevel is now {}, was previously {}".format(siteuser.username, scarf.core.accesslevels[level], scarf.core.accesslevels[prev])
