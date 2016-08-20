"""
Insert fake test data into the database

If a 'testimgs' directory exists in the project root then those images will
be randomly added to items.
"""

import os, sys
sys.path.insert(1, os.path.join(sys.path[0], '../../..'))

import scarf
import flask
import string
import random
import logging
from faker import Factory
from scarf import app

logging.basicConfig(filename='ersatz.log',level=logging.DEBUG)
fake = Factory.create()

def make_user():
    username = fake.user_name()
    email = fake.safe_email()
    password = fake.password()

    uid = scarf.core.new_user(username, password, email, fake.ipv4(network=False))
    print "Created user {} / {} - {} - {}".format(uid, username, password, email)

    siteuser = scarf.core.SiteUser.create(username)
    return siteuser

def make_item(siteuser):
    name = fake.text(max_nb_chars=30)
    description = fake.text()

    itemid = scarf.core.new_item(name, description, siteuser.uid, fake.ipv4(network=False))
    item = scarf.core.SiteItem.create(itemid)
    print "Created item {} / {}".format(itemid, name)
    return item

def add_image(item, userid, directory):
    title = fake.text(max_nb_chars=30)

    try:
        filename = random.choice(os.listdir(directory))
    except OSError:
        print "Unable to load test images, skipping image addition for {}\n-----\n{} directory is missing or otherwise inaccessible!!\n-----".format(item.name, directory)
        return

    with open(os.path.join(directory, filename), "r") as f:
        img = scarf.core.new_img(f, title, item.uid, userid, fake.ipv4(network=False))
        print "Added image {} to item {} by userid {}".format(title, item.name, userid)

with app.test_request_context(''):
    for _ in range(0,10):
        user = make_user()
        for _ in range(0,10):
            item = make_item(user)
            for _ in range(0,2):
                add_image(item, user.uid, 'testimgs')
