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
    def test_global_balance_can_be_retrieved_by_owner_via_api(self):
        access_token = self.get_access_token()
        new_account = self.create_account(user_id=1, has_plafond=0, plafond=None)
        new_expense = self.create_expense(user_id=1, account_id=new_account.account_id)
        amount = new_expense.amount
        response = self.app.get('/api/v1/balance', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(amount, response.get_json()['current_balance'])

    def test_account_balance_can_be_retrieved_by_owner_via_api(self):
        access_token = self.get_access_token()
        new_account = self.create_account(user_id=1, has_plafond=0, plafond=None)
        new_expense = self.create_expense(user_id=1, account_id=new_account.account_id)
        amount = new_expense.amount
        response = self.app.get('/api/v1/accounts/'+ str(new_account.account_id) +'/balance', headers={'Authorization':'JWT '+ access_token})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(amount, response.get_json()['current_balance'])