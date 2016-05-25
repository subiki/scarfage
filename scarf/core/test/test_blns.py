import os, sys
import scarf
import unittest
import flask
import string
import random
import logging
import json
import base64

from scarf import app
from ..sql import doquery

logging.basicConfig(filename='tests.log',level=logging.DEBUG)
logger = logging.getLogger(__name__)

def generator(size=6, chars=string.ascii_lowercase + string.ascii_uppercase + string.digits):
   return ''.join(random.choice(chars) for _ in range(size))

class SiteStringsNaughtyStringsTestCase(unittest.TestCase):
    def __init__(self, methodName, naughty_string=''):
        scarf.app.config['TESTING'] = True
        super(SiteStringsNaughtyStringsTestCase, self).__init__(methodName)

        self.ns = unicode(base64.b64decode(naughty_string))
        self.encoded = naughty_string

    def runTest(self):
        if not self.ns:
            return

        try:
            uid = scarf.core.new_string(self.ns, self.ns, 'en')
        except scarf.core.NoString:
            return

        try:
            ss = scarf.core.SiteString.create(self.ns, 'en')
        except scarf.core.NoString:
            logger.error('BLNS fail creating SiteString, base 64 encoded string was: {}'.format(self.encoded))
            raise

        ss.delete()

class SiteUserNaughtyStringsTestCase(unittest.TestCase):
    def __init__(self, methodName, naughty_string=''):
        scarf.app.config['TESTING'] = True
        scarf.config.BCRYPT_ROUNDS = 4
        super(SiteUserNaughtyStringsTestCase, self).__init__(methodName)

        self.ns = unicode(base64.b64decode(naughty_string))
        self.encoded = naughty_string

    def runTest(self):
        try:
            uid = scarf.core.new_user(self.ns, self.ns, '{}@{}'.format(self.ns, self.ns), '0.0.0.0')
        except scarf.core.NoUser:
            return

        try:
            siteuser = scarf.core.SiteUser.create(self.ns)
        except scarf.core.NoUser:
            logger.error('BLNS fail creating SiteUser, base 64 encoded string was: {}'.format(self.encoded))
            raise

        siteuser.delete()

class SiteItemNaughtyStringsTestCase(unittest.TestCase):
    def __init__(self, methodName, naughty_string=''):
        scarf.app.config['TESTING'] = True
        self.username = generator(12)
        self.domain = generator(12)
        self.password = generator(12)

        super(SiteItemNaughtyStringsTestCase, self).__init__(methodName)

        self.ns = unicode(base64.b64decode(naughty_string))
        self.encoded = naughty_string

    def runTest(self):
        uid = scarf.core.new_user(self.username, self.password, '{}@{}'.format(self.username, self.domain), '0.0.0.0')

        assert uid is not False 
        assert isinstance(uid, (int, long)) is True

        siteuser = scarf.core.SiteUser.create(self.username)
        try:
            itemid = scarf.core.new_item(self.ns, self.ns, siteuser.uid, '0.0.0.0')
            item = scarf.core.SiteItem.create(itemid)
            item.delete()
        except scarf.core.NoItem:
            pass
        siteuser.delete()

def load_tests(loader, tests, pattern):
    test_cases = unittest.TestSuite()

    """
    this_dir = os.path.dirname(__file__)
    package_tests = loader.discover(start_dir=this_dir, pattern=pattern)
    test_cases.addTests(package_tests)
    """

    with open('blns.base64.json', 'r') as f:
        test_cases.addTest(SiteUserNaughtyStringsTestCase('runTest', 'bm9ybWFsIHN0cmluZw==')) # 'normal string'
        for naughty_string in json.load(f):
            with app.test_request_context(''):
                test_cases.addTest(SiteUserNaughtyStringsTestCase('runTest', naughty_string))
                test_cases.addTest(SiteStringsNaughtyStringsTestCase('runTest', naughty_string))
                test_cases.addTest(SiteItemNaughtyStringsTestCase('runTest', naughty_string))

    return test_cases

if __name__ == '__main__':
    unittest.main()
