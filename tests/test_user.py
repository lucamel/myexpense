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

class UserTests(MainTests, unittest.TestCase):

    # Helpers
    new_user_data = dict(
        email = "johndoe@example.com",
        password = "Secret12",
        name = "John Doe"
    )

    def create_user(self, email = "janedoe@example.com", name = "Jane Doe", password = 'Secret12'):
        new_user = User(email = email, name = name, password = password)
        self.db.session.add(new_user)
        self.db.session.commit()
        return new_user

    # Tests
    def test_user_can_be_added_to_db(self):
        self.create_user()
        user = self.db.session.query(User).all()
        self.assertEquals(user[0].email, "janedoe@example.com")

    def test_a_user_can_be_deleted(self):
        new_user = self.create_user()
        users = self.db.session.query(User).all()
        self.assertEquals(len(users), 1)
        self.db.session.delete(new_user)
        self.db.session.commit()
        users = self.db.session.query(User).all()
        self.assertEquals(len(users), 0)

    def test_a_user_can_be_retrieved_via_api(self):
        new_user = self.create_user()
        response = self.app.get('/api/v1/user/'+ str(new_user.user_id))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(new_user.name, response.get_json()['name'])

    def test_a_user_can_register_via_api(self):
        response = self.app.post('/api/v1/register', data = json.dumps(self.new_user_data), content_type='application/json')
        self.assertEquals(response.status_code, 201)
        response = self.app.get('/api/v1/user/1')
        self.assertEquals(self.new_user_data['email'], response.get_json()['email'])

    def test_a_user_cannot_register_with_invalid_data_via_api(self):
        data = copy.deepcopy(self.new_user_data)
        del data["email"]
        response = self.app.post('/api/v1/register', data = json.dumps(data), content_type='application/json')
        self.assertEquals(response.status_code, 422)
        self.assertIn('error', response.get_json())
        response = self.app.get('/api/v1/user/1')
        self.assertNotIn(self.new_user_data['email'], response.get_json())

    def test_a_user_cannot_register_with_an_existing_email_via_api(self):
        new_user = self.create_user()
        data = copy.deepcopy(self.new_user_data)
        data["email"] = "janedoe@example.com"
        response = self.app.post('/api/v1/register', data = json.dumps(data), content_type='application/json')
        self.assertEquals(response.status_code, 422)
        self.assertIn('error', response.get_json())
        response = self.app.get('/api/v1/user/2')
        self.assertNotIn(self.new_user_data['email'], response.get_json())

    def test_a_user_cannot_register_with_a_not_compliant_password_via_api(self):
        new_user = self.create_user()
        data = copy.deepcopy(self.new_user_data)
        data["password"] = "secret"
        response = self.app.post('/api/v1/register', data = json.dumps(data), content_type='application/json')
        self.assertEquals(response.status_code, 422)
        self.assertIn('error', response.get_json())
        response = self.app.get('/api/v1/user/2')
        self.assertNotIn(self.new_user_data['email'], response.get_json())