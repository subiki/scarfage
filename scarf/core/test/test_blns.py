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

class SiteUserNaughtyStringsTestCase(unittest.TestCase):
    def __init__(self, methodName, naughty_string=''):
        scarf.app.config['TESTING'] = True
        scarf.config.BCRYPT_ROUNDS = 4
        super(SiteUserNaughtyStringsTestCase, self).__init__(methodName)

        self.ns = naughty_string

    def runTest(self):
        try:
            uid = scarf.core.new_user(self.ns, self.ns, '{}@{}'.format(self.ns, self.ns), '0.0.0.0')
        except scarf.core.NoUser:
            return

        try:
            siteuser = scarf.core.SiteUser.create(self.ns)
            siteuser.delete()
        except scarf.core.NoUser:
            pass

def load_tests(loader, tests, pattern):
    test_cases = unittest.TestSuite()

    """
    this_dir = os.path.dirname(__file__)
    package_tests = loader.discover(start_dir=this_dir, pattern=pattern)
    test_cases.addTests(package_tests)
    """

    with open('blns.base64.json', 'r') as f:
        for naughty_string in json.load(f):
            with app.test_request_context(''):
                test_cases.addTest(SiteUserNaughtyStringsTestCase('runTest', unicode(base64.b64decode(naughty_string))))

    return test_cases

if __name__ == '__main__':
    unittest.main()
