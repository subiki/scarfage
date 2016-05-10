# regression test for https://github.com/cmazuc/scarfage/issues/50
# regression test for https://github.com/cmazuc/scarfage/issues/47
# regression test for https://github.com/cmazuc/scarfage/issues/38
# regression test for https://github.com/cmazuc/scarfage/issues/36
# regression test for https://github.com/cmazuc/scarfage/issues/25
# regression test for https://github.com/cmazuc/scarfage/issues/11

import os, sys
import scarf
import unittest
import flask
import string
import random
import logging
import base64
import json

from scarf import app

logging.basicConfig(filename='tests.log',level=logging.DEBUG)

def generator(size=6, chars=string.ascii_lowercase + string.ascii_uppercase + string.digits):
   return ''.join(random.choice(chars) for _ in range(size))

class SiteItemTestCase(unittest.TestCase):
    def setUp(self):
        scarf.app.config['TESTING'] = True
        self.username = generator(12)
        self.domain = generator(12)
        self.password = generator(12)

        with app.test_request_context(''):
            uid = scarf.core.new_user(self.username, self.password, '{}@{}'.format(self.username, self.domain), '0.0.0.0')

        assert uid is not False 
        assert isinstance(uid, (int, long)) is True

        self.siteuser = scarf.core.SiteUser.create(self.username)

    def tearDown(self):
        self.siteuser.delete()

    def test_new_item_naughty_names_and_descriptions(self):
        with open('blns.base64.json', 'r') as f:
            for naughty_string in json.load(f):
                decoded = base64.b64decode(naughty_string)
                try:
                    itemid = scarf.core.new_item(decoded, decoded, self.siteuser.uid, '0.0.0.0')
                    item = scarf.core.SiteItem(itemid)
                    item.delete()
                except scarf.core.NoItem:
                    pass

if __name__ == '__main__':
    unittest.main()
