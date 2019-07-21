# tests/test_expense.py

import os
import unittest
import json
import datetime
import copy

from myexpense import project
from myexpense.project._config import basedir
from myexpense.tests.test_main import MainTests
from myexpense.project.models.account import Account
from myexpense.project.models.expense import Expense
from myexpense.project.exceptions import InvalidRequest
from sqlalchemy.exc import DatabaseError

class ExpenseTests(MainTests, unittest.TestCase):

    # Helpers
    new_expense_data = dict(
        amount = 5000, 
        category = 'Personal', 
        date = '2018-01-01',
        note = 'Gasoline', 
        user_id = 10,
        account_id = 1
    )

    def create_expense(self, amount = 1000, category = 'abc', date = '2018-01-01', note = 'efg', user_id = 2, account_id = 2):
        new_expense = Expense(amount = amount, category = category, date = date, note = note, user_id = user_id, account_id = account_id)
        self.db.session.add(new_expense)
        self.db.session.commit()
        return new_expense

    def create_account(self, plafond = 150000, has_plafond = 1, name = 'Carta', user_id = 2):
        new_account = Account(plafond = plafond, has_plafond = has_plafond, name = name, user_id = user_id)
        self.db.session.add(new_account)
        self.db.session.commit()
        return new_account

    # Tests
    def test_expense_can_be_added_to_db(self):
        self.create_expense()
        expense = self.db.session.query(Expense).all()
        self.assertEquals(expense[0].amount, 1000)

    def test_an_expense_can_be_deleted(self):
        new_expense = self.create_expense()
        expenses = self.db.session.query(Expense).all()
        self.assertEquals(len(expenses), 1)
        self.db.session.delete(new_expense)
        self.db.session.commit()
        expenses = self.db.session.query(Expense).all()
        self.assertEquals(len(expenses), 0)

    def test_expenses_can_be_retrieved_by_owner_via_api(self):
        access_token = self.get_access_token()
        new_expense = self.create_expense(user_id=1)
        response = self.app.get('/api/v1/expenses', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(new_expense.category, response.get_json()['expenses'][0]['category'])
    
    def test_filtered_expenses_can_be_retrieved_by_owner_via_api(self):
        access_token = self.get_access_token()
        self.create_expense(user_id = 1, category ='Personal')
        self.create_expense(user_id = 1, category = 'Bank')
        self.create_expense(user_id = 2, category = 'Personal')
        response = self.app.get('/api/v1/expenses?user_id=1', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(response.get_json()['expenses']), 2)
        response = self.app.get('/api/v1/expenses?category=Bank', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(response.get_json()['expenses']), 1)

    def test_an_expense_can_be_retrieved_by_owner_via_api(self):
        access_token = self.get_access_token()
        new_expense = self.create_expense(user_id=1)
        response = self.app.get('/api/v1/expenses/' + str(new_expense.expense_id), headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(new_expense.category, response.get_json()['category'])
        new_expense = self.create_expense(user_id=2)
        response = self.app.get('/api/v1/expenses/' + str(new_expense.expense_id), headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 403)
    
    def test_a_new_expense_can_be_posted_by_owner_via_api(self):
        access_token = self.get_access_token()
        new_account = self.create_account()
        self.create_expense(account_id=new_account.account_id, user_id=1)
        response = self.app.post('/api/v1/expenses', data = json.dumps(self.new_expense_data), content_type='application/json', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 201)
        response = self.app.get('/api/v1/expenses', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(self.new_expense_data['category'], response.get_json()['expenses'][1]['category'])

    def test_a_new_expense_can_be_posted_as_account_resource_by_owner_via_api(self):
        access_token = self.get_access_token()
        new_account = self.create_account()
        self.create_expense(account_id=new_account.account_id, user_id=1)
        data = copy.deepcopy(self.new_expense_data)
        del data['account_id']
        response = self.app.post('/api/v1/accounts/'+ str(new_account.account_id) +'/expenses', data = json.dumps(data), content_type='application/json', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 201)
        response = self.app.get('/api/v1/expenses', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(self.new_expense_data['category'], response.get_json()['expenses'][1]['category'])

    def test_a_new_expense_cannot_be_posted_with_invalid_data_and_receive_an_error_by_owner_via_api(self):
        access_token = self.get_access_token()
        self.create_expense()
        data = self.new_expense_data
        del data['amount']
        del data['category']
        response = self.app.post('/api/v1/expenses', data = json.dumps(data), content_type='application/json', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 422)
        self.assertIn('error', response.get_json())
        response = self.app.get('/api/v1/expenses', headers={'Authorization':'JWT '+ access_token})
        self.assertNotIn(self.new_expense_data['note'], response.get_json())

    def test_a_new_expense_cannot_be_posted_as_account_resource_with_invalid_data_and_receive_an_error_by_owner_via_api(self):
        access_token = self.get_access_token()
        new_account = self.create_account()
        data = copy.deepcopy(self.new_expense_data)
        del data['amount']
        del data['category']
        del data['account_id']
        response = self.app.post('/api/v1/accounts/'+ str(new_account.account_id) +'/expenses', data = json.dumps(data), content_type='application/json', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 422)
        self.assertIn('error', response.get_json())
        response = self.app.get('/api/v1/accounts/'+ str(new_account.account_id) +'/expenses', headers={'Authorization':'JWT '+ access_token})
        self.assertNotIn(self.new_expense_data['note'], response.get_json())

    def test_an_expense_can_be_deleted_by_owner_via_api(self):
        access_token = self.get_access_token()
        new_expense = self.create_expense(user_id=1)
        response = self.app.delete('/api/v1/expenses/' + str(new_expense.expense_id), content_type='application/json', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 204)
        expense = Expense.query.get(new_expense.expense_id)
        self.assertEquals(expense, None)
        new_expense = self.create_expense()
        response = self.app.delete('/api/v1/expenses/' + str(new_expense.expense_id), content_type='application/json', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 403)

    def test_an_expense_can_be_deleted_as_account_resource_by_owner_via_api(self):
        access_token = self.get_access_token()
        new_account = self.create_account()
        new_expense = self.create_expense(account_id=new_account.account_id, user_id=1)
        response = self.app.delete('/api/v1/accounts/'+ str(new_expense.account_id) +'/expenses/' + str(new_expense.expense_id), content_type='application/json', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 204)
        expense = Expense.query.get(new_expense.expense_id)
        self.assertEquals(expense, None)
        new_account = self.create_account()
        new_expense = self.create_expense(account_id=new_account.account_id)
        response = self.app.delete('/api/v1/accounts/'+ str(new_expense.account_id) +'/expenses/' + str(new_expense.expense_id), content_type='application/json', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 403)

    def test_an_expense_cannot_be_deleted_as_account_resource_from_wrong_account_by_owner_via_api(self):
        access_token = self.get_access_token()
        new_account = self.create_account()
        new_expense = self.create_expense(account_id=new_account.account_id)
        response = self.app.delete('/api/v1/accounts/'+ str(new_expense.account_id + 1) +'/expenses/' + str(new_expense.expense_id), content_type='application/json', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 404)
        expense = Expense.query.get(new_expense.expense_id)
        self.assertEquals(expense.expense_id, new_expense.expense_id)

    def test_an_expense_can_be_updated_by_owner_via_api(self):
        access_token = self.get_access_token()
        new_expense = self.create_expense(user_id=1)
        data = self.new_expense_data
        response = self.app.put('/api/v1/expenses/' + str(new_expense.expense_id), data = json.dumps(data), content_type='application/json', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(data['note'], response.get_json()['note'])
        new_expense = self.create_expense(user_id=2)
        data = self.new_expense_data
        response = self.app.put('/api/v1/expenses/' + str(new_expense.expense_id), data = json.dumps(data), content_type='application/json', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 403)

    def test_an_expense_can_be_updated_as_account_resource_by_owner_via_api(self):
        access_token = self.get_access_token()
        new_account = self.create_account(user_id=1)
        new_expense = self.create_expense(user_id=1, account_id=new_account.account_id)
        data = self.new_expense_data
        response = self.app.put('/api/v1/accounts/'+ str(new_expense.account_id) +'/expenses/' + str(new_expense.expense_id), data = json.dumps(data), content_type='application/json', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(data['note'], response.get_json()['note'])

    def test_an_expense_cannnot_be_updated_as_account_resource_from_wrong_account_by_owner_via_api(self):
        access_token = self.get_access_token()
        new_account = self.create_account()
        new_expense = self.create_expense(account_id=new_account.account_id)
        data = self.new_expense_data
        response = self.app.put('/api/v1/accounts/'+ str(new_expense.account_id + 1) +'/expenses/' + str(new_expense.expense_id), data = json.dumps(data), content_type='application/json', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 404)

    def test_expenses_can_be_retieved_from_an_account_by_owner_via_api(self):
        access_token = self.get_access_token()
        new_account = self.create_account(user_id=1)
        new_expense = self.create_expense(user_id=1, account_id=new_account.account_id)
        response = self.app.get('/api/v1/accounts/'+ str(new_account.account_id) +'/expenses', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(new_expense.category, response.get_json()['expenses'][0]['category'])

    def test_an_expense_can_be_retrieved_from_an_account_by_owner_via_api(self):
        access_token = self.get_access_token()
        new_account = self.create_account(user_id=1)
        new_expense = self.create_expense(user_id=1, account_id=new_account.account_id)
        response = self.app.get('/api/v1/accounts/'+ str(new_account.account_id) +'/expenses/' + str(new_expense.expense_id), headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(new_expense.category, response.get_json()['category'])