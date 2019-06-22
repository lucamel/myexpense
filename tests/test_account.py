# tests/test_account.py

import os
import unittest
import json
import datetime
import copy

from myexpense.project._config import basedir
from myexpense.project.models.account import Account
from myexpense.project.exceptions import InvalidRequest
from myexpense.tests.test_main import MainTests
from sqlalchemy.exc import DatabaseError

class AccountTests(MainTests, unittest.TestCase):

    # Helpers
    new_account_data = dict(
        plafond = None,
        has_plafond = 0,
        name = 'Conto',
        user_id = 1,
    )

    def create_account(self, plafond = 150000, has_plafond = 1, name = 'Carta', user_id = 2):
        new_account = Account(plafond = plafond, has_plafond = has_plafond, name = name, user_id = user_id)
        self.db.session.add(new_account)
        self.db.session.commit()
        return new_account

    # Tests
    def test_account_can_be_added_to_db(self):
        self.create_account()
        accounts = self.db.session.query(Account).all()
        self.assertEquals(accounts[0].name, 'Carta')

    def test_an_account_can_be_deleted(self):
        new_account = self.create_account()
        accounts = self.db.session.query(Account).all()
        self.assertEquals(len(accounts), 1)
        self.db.session.delete(new_account)
        self.db.session.commit()
        accounts = self.db.session.query(Account).all()
        self.assertEquals(len(accounts), 0)

    def test_accounts_can_be_retrieved_via_api(self):
        new_account = self.create_account()
        response = self.app.get('/api/v1/accounts')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(new_account.name, response.get_json()[0]['name'])

    def test_filtered_accounts_can_be_retrieved_via_api(self):
        self.create_account(user_id = 1, name ='Carta')
        self.create_account(user_id = 2, name = 'Carta')
        response = self.app.get('/api/v1/accounts?user_id=1')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(response.get_json()), 1)
        response = self.app.get('/api/v1/accounts?name=Carta')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(response.get_json()), 2)
        response = self.app.get('/api/v1/accounts?user_id=1&name=Carta')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(response.get_json()), 1)

    def test_an_account_can_be_retrieved_via_api(self):
        new_account = self.create_account()
        response = self.app.get('/api/v1/accounts/' + str(new_account.account_id))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(new_account.name, response.get_json()['name'])

    def test_a_new_account_can_be_posted_via_api(self):
        self.create_account()
        response = self.app.post('/api/v1/accounts', data = json.dumps(self.new_account_data), content_type='application/json')
        self.assertEquals(response.status_code, 201)
        response = self.app.get('/api/v1/accounts')
        self.assertEquals(self.new_account_data['name'], response.get_json()[1]['name'])

    def test_a_new_account_cannot_be_posted_with_invalid_data_and_receive_an_error_via_api(self):
        self.create_account()
        data = copy.deepcopy(self.new_account_data)
        del data['name']
        response = self.app.post('/api/v1/accounts', data = json.dumps(data), content_type='application/json')
        self.assertEquals(response.status_code, 422)
        self.assertIn('error', response.get_json())
        response = self.app.get('/api/v1/accounts')
        self.assertNotIn(self.new_account_data['plafond'], response.get_json())

    def test_an_account_can_be_deleted_via_api(self):
        new_account = self.create_account()
        response = self.app.delete('/api/v1/accounts/' + str(new_account.account_id), content_type='application/json')
        self.assertEquals(response.status_code, 204)
        account = Account.query.get(new_account.account_id)
        self.assertEquals(account, None)

    def test_an_expense_can_be_updated_via_api(self):
        new_account = self.create_account()
        data = self.new_account_data
        response = self.app.put('/api/v1/accounts/' + str(new_account.account_id), data = json.dumps(data), content_type='application/json')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(data['name'], response.get_json()['name'])