import datetime
from dateutil.relativedelta import *

from marshmallow import fields
from sqlalchemy.sql import func

from .. import db
from .. import ma
from ..exceptions import InvalidRequest
from ..models.account import Account
from ..models.expense import Expense



class Balance:
    current_balance = None
    start_period_balance = None
    end_period_balance = None
    account = None

    def __init__(self, user_id, account=None, from_date=None, to_date=None, m_date=None):
        self.account = account
        query = db.session.query(func.sum(Expense.amount))

        if account is not None:
            query = query.filter(Expense.account_id == account.account_id)
            initial_balance = account.initial_balance
            if account.has_plafond == True:
                initial_balance = account.plafond
        else:
            accounts = db.session.query(Account.account_id, Account.initial_balance).filter(Account.user_id==user_id, Account.has_plafond==False).all()
            query = query.filter(Expense.account_id.in_((x[0] for x in accounts)))
            initial_balance = sum(x[1] for x in accounts)

        if account is not None and account.has_plafond == True:
            current_balance = query.filter(Expense.date <= datetime.date.today(), Expense.date >= datetime.date(datetime.date.today().year, datetime.date.today().month, 1)).scalar()
            start_period_balance = 0
            end_period_balance = query.filter(Expense.date <= m_date + relativedelta(months=1) - relativedelta(days=-1), Expense.date >= m_date).scalar()
        else:
            current_balance = query.filter(Expense.date <= datetime.date.today()).scalar()
            start_period_balance = query.filter(Expense.date < from_date).scalar()
            end_period_balance = query.filter(Expense.date <= to_date).scalar()
        
        initial_balance = initial_balance if initial_balance is not None else 0

        current_balance = current_balance if current_balance is not None else 0
        self.current_balance = current_balance + initial_balance

        start_period_balance = start_period_balance if start_period_balance is not None else 0
        self.start_period_balance = start_period_balance + initial_balance

        end_period_balance = end_period_balance if end_period_balance is not None else 0
        self.end_period_balance = end_period_balance + initial_balance
    
    def __repr__(self):
        return "<Balance: current_balance {0} - start_period_balance {1} - end_period_balance {2}>".format(self.current_balance, self.start_period_balance, self.end_period_balance)

class BalanceSchema(ma.Schema):
    current_balance = fields.Int()
    start_period_balance = fields.Int()
    end_period_balance = fields.Int()
    account = fields.Nested("AccountSchema", exclude=('expenses',))