# tests/test_expense.py

import os
import unittest
import json

from myexpense import project
from myexpense.project._config import basedir
from myexpense.project.models.expense import Expense
from myexpense.project.exceptions import InvalidRequest
from sqlalchemy.exc import DatabaseError
import datetime

TEST_DB = 'test.db'

db = project.db
app = project.app

class ExpenseTests(unittest.TestCase):

    # SetUp and TearDown

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False        
        app.config['DEBUG'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, TEST_DB)

        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    # Helpers
    new_expense_data = dict(
        amount = 5000, 
        category = 'Personal', 
        date = '2018-01-01',
        note = 'Gasoline', 
        user_id = 1,
        account_id = 1
    )

    def create_expense(self, amount = 1000, category = 'abc', date = '2018-01-01', note = 'efg', user_id = 2, account_id = 2):
        new_expense = Expense(amount = amount, category = category, date = date, note = note, user_id = user_id, account_id = account_id)
        db.session.add(new_expense)
        db.session.commit()
        return new_expense

    # Tests
    def test_expense_can_be_added_to_db(self):
        self.create_expense()
        expense = db.session.query(Expense).all()
        self.assertEquals(expense[0].amount, 1000)

    def test_an_expense_can_be_deleted(self):
        new_expense = self.create_expense()
        expenses = db.session.query(Expense).all()
        self.assertEquals(len(expenses), 1)
        db.session.delete(new_expense)
        db.session.commit()
        expenses = db.session.query(Expense).all()
        self.assertEquals(len(expenses), 0)

    def test_expenses_can_be_retrieved_via_api(self):
        new_expense = self.create_expense()
        response = self.app.get('/api/v1/expenses')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(new_expense.category, response.get_json()[0]['category'])
    
    def test_filtered_expenses_can_be_retrieved_via_api(self):
        self.create_expense(user_id = 1, category ='Personal')
        self.create_expense(user_id = 2, category = 'Personal')
        response = self.app.get('/api/v1/expenses?user_id=1')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(response.get_json()), 1)
        response = self.app.get('/api/v1/expenses?category=Personal')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(response.get_json()), 2)
        response = self.app.get('/api/v1/expenses?user_id=1&category=Personal')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(response.get_json()), 1)

    def test_an_expense_can_be_retrieved_via_api(self):
        new_expense = self.create_expense()
        response = self.app.get('/api/v1/expenses/' + str(new_expense.expense_id))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(new_expense.category, response.get_json()['category'])
    
    def test_a_new_expense_can_be_posted_via_api(self):
        self.create_expense()
        response = self.app.post('/api/v1/expenses', data = json.dumps(self.new_expense_data), content_type='application/json')
        self.assertEquals(response.status_code, 201)
        response = self.app.get('/api/v1/expenses')
        self.assertEquals(self.new_expense_data['category'], response.get_json()[1]['category'])

    def test_a_new_expense_cannot_be_posted_with_invalid_data_and_receive_an_error_via_api(self):
        self.create_expense()
        data = self.new_expense_data
        del data['amount']
        del data['category']
        response = self.app.post('/api/v1/expenses', data = json.dumps(data), content_type='application/json')
        self.assertEquals(response.status_code, 422)
        self.assertIn(b'error', response.data)
        response = self.app.get('/api/v1/expenses')
        self.assertNotIn(bytes(self.new_expense_data['note'], 'utf-8'), response.data)

    def test_an_expense_can_be_deleted_via_api(self):
        new_expense = self.create_expense()
        response = self.app.delete('/api/v1/expenses/' + str(new_expense.expense_id), content_type='application/json')
        self.assertEquals(response.status_code, 204)
        expense = Expense.query.get(new_expense.expense_id)
        self.assertEquals(expense, None)

    def test_an_expense_can_be_updated_via_api(self):
        new_expense = self.create_expense()
        data = self.new_expense_data
        response = self.app.put('/api/v1/expenses/' + str(new_expense.expense_id), data = json.dumps(data), content_type='application/json')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(data['note'], response.get_json()['note'])
        