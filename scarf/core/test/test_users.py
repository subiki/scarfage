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

class SiteUserTestCase(unittest.TestCase):
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

    def test_siteuser_nouser(self):
        self.assertRaises(scarf.core.NoUser, scarf.core.SiteUser, 'invalid user')

    def test_siteuser_accesslevel_change(self):
        self.siteuser.newaccesslevel(255)
        self.siteuser.newaccesslevel(1)

    def test_siteuser_seen(self):
        self.siteuser.seen()

    def test_siteuser_authenticate_with_correct_password(self):
        self.siteuser.authenticate(self.password)

    def test_siteuser_authenticate_with_incorrect_password(self):
        self.assertRaises(scarf.core.AuthFail, self.siteuser.authenticate, 'invalid password')

    def test_siteuser_authenticate_with_banned_account(self):
        self.siteuser.newaccesslevel(0)
        self.assertRaises(scarf.core.AuthFail, self.siteuser.authenticate, self.password)

    def test_siteuser_authenticate_with_invalid_username(self):
        self.siteuser.uid = 0
        self.assertRaises(scarf.core.AuthFail, self.siteuser.authenticate, self.password)

    def test_siteuser_password_reset(self):
        newpassword = generator(12)
        self.siteuser.newpassword(newpassword)
        self.password = newpassword
        self.siteuser.authenticate(self.password)

    def test_siteuser_email_reset(self):
        newemail = generator(12)
        self.siteuser.newemail('{}@{}'.format(self.username, newemail))
        self.email = newemail

    def test_siteuser_forgot_pw_reset(self):
        with app.test_request_context(''):
            self.siteuser.forgot_pw_reset('0.0.0.0', admin=True)

    def test_siteuser_check_email(self):
        assert scarf.core.check_email(self.siteuser.email) is not None

    def test_siteuser_check_email(self):
        assert scarf.core.check_email('invalid email') is None

if __name__ == '__main__':
    unittest.main()
