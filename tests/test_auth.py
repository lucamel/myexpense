# tests/test_user.py

import os
import unittest
import json
import datetime
import copy

from myexpense import project
from myexpense.project import bcrypt
from myexpense.project._config import basedir
from myexpense.tests.test_main import MainTests
from myexpense.project.models.user import User
from myexpense.project.exceptions import InvalidRequest
from sqlalchemy.exc import DatabaseError

class AuthTests(MainTests, unittest.TestCase):

    # Tests
    def test_get_user_access_token(self):
        new_user = self.create_user(confirmed=True)
        response = self.app.post('/auth', data=json.dumps({'username':new_user.email, 'password':'Secret12'}), content_type='application/json')
        self.get_access_token()
        self.assertIn("access_token", response.get_json())
    
    # Tests
    def test_cannot_get_user_access_token_with_invalid_credentials(self):
        new_user = self.create_user(confirmed=True)
        response = self.app.post('/auth', data=json.dumps({'username':new_user.email, 'password':'Pippo'}), content_type='application/json')
        self.assertNotIn("access_token", response.get_json())