# tests/test_account.py

import os
import unittest
import json
import datetime
import copy

from myexpense.project.models.account import Account
from myexpense.project.models.expense import Expense
from myexpense.tests.test_main import MainTests

class AccountTests(MainTests, unittest.TestCase):

    # Helpers
    new_account_data = dict(
        plafond = None,
        has_plafond = 0,
        name = 'Conto',
        user_id = 1,
        initial_balance = 0
    )

    def create_account(self, plafond = 150000, has_plafond = 1, name = 'Carta', user_id = 2, initial_balance = 0):
        new_account = Account(plafond = plafond, has_plafond = has_plafond, name = name, user_id = user_id, initial_balance = 0)
        self.db.session.add(new_account)
        self.db.session.commit()
        return new_account

    def create_expense(self, amount = 1000, category = 'abc', date = '2018-01-01', note = 'efg', user_id = 2, account_id = 2):
        new_expense = Expense(amount = amount, category = category, date = date, note = note, user_id = user_id, account_id = account_id)
        self.db.session.add(new_expense)
        self.db.session.commit()
        return new_expense

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

    def test_accounts_can_be_retrieved_by_owner_via_api(self):
        access_token = self.get_access_token()
        new_account = self.create_account(name="AccountName", user_id=1)
        response = self.app.get('/api/v1/accounts', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 200)
        self.assertEquals("AccountName", response.get_json()[0]['name'])

    def test_filtered_accounts_can_be_retrieved_by_owner_via_api(self):
        access_token = self.get_access_token()
        self.create_account(user_id = 1, name ='Carta')
        response = self.app.get('/api/v1/accounts?name=Carta', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(response.get_json()), 1)

    def test_an_account_can_be_retrieved_via_by_owner_api(self):
        access_token = self.get_access_token()
        new_account = self.create_account(user_id=1)
        response = self.app.get('/api/v1/accounts/' + str(new_account.account_id), headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(new_account.name, response.get_json()['name'])
        new_account = self.create_account(user_id=2)
        response = self.app.get('/api/v1/accounts/' + str(new_account.account_id), headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 403)

    def test_a_new_account_can_be_posted_by_owner_via_api(self):
        access_token = self.get_access_token()
        self.create_account(user_id=1)
        response = self.app.post('/api/v1/accounts', data = json.dumps(self.new_account_data), content_type='application/json', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 201)
        response = self.app.get('/api/v1/accounts', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(self.new_account_data['name'], response.get_json()[1]['name'])

    def test_a_new_account_cannot_be_posted_with_invalid_data_and_receive_an_error_by_owner_via_api(self):
        access_token = self.get_access_token()
        self.create_account()
        data = copy.deepcopy(self.new_account_data)
        del data['name']
        response = self.app.post('/api/v1/accounts', data = json.dumps(data), content_type='application/json', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 422)
        self.assertIn('error', response.get_json())
        response = self.app.get('/api/v1/accounts', headers={'Authorization':'JWT '+ access_token})
        self.assertNotIn(self.new_account_data['plafond'], response.get_json())

    def test_an_account_can_be_deleted_by_owner_via_api(self):
        access_token = self.get_access_token()
        new_account = self.create_account(user_id=1)
        response = self.app.delete('/api/v1/accounts/' + str(new_account.account_id), content_type='application/json', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 204)
        account = Account.query.get(new_account.account_id)
        self.assertEquals(account, None)
        new_account = self.create_account(user_id=2)
        response = self.app.delete('/api/v1/accounts/' + str(new_account.account_id), content_type='application/json', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 403)

    def test_an_expense_can_be_updated_by_owner_via_api(self):
        access_token = self.get_access_token()
        new_account = self.create_account(user_id=1)
        data = self.new_account_data
        response = self.app.put('/api/v1/accounts/' + str(new_account.account_id), data = json.dumps(data), content_type='application/json', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(data['name'], response.get_json()['name'])
    
    def test_account_balance_can_be_retrieved_by_owner_via_api(self):
        access_token = self.get_access_token()
        new_account = self.create_account(user_id=1, has_plafond=0, plafond=None)
        new_expense = self.create_expense(user_id=1, account_id=new_account.account_id)
        amount = new_expense.amount
        response = self.app.get('/api/v1/accounts/'+ str(new_account.account_id) +'/balance', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(amount, response.get_json()['current_balance'])