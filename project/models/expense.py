from .. import db
from .. import ma
from ..helpers.mixins import ModelMixin

import datetime

class Expense(ModelMixin, db.Model):

    filters = ['category', 'user_id', 'account_id','date', 'dateBetween']

    __tablename__ = 'expenses'
    
    expense_id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(40), nullable = False)
    date = db.Column(db.Date, nullable = False)
    note = db.Column(db.String(200), nullable = True)
    user_id = db.Column(db.Integer, nullable=False)
    account_id = db.Column(db.Integer, nullable=False)

    def __init__(self, amount, category, date, user_id, account_id, note=None):
        if type(date) is str:
            date = datetime.datetime.strptime(date, "%Y-%m-%d")
        self.amount = amount
        self.category = category
        self.date = date
        self.user_id = user_id
        self.account_id = account_id
        self.note = note

    @classmethod
    def filter(self, args):
        args = args.copy()
        query = self.query
        if(args.get('dateBetween') is not None): 
            dates = [datetime.datetime.strptime(x, "%Y-%m-%d") for x in args.get('dateBetween').split(',')]
            query = query.filter(Expense.date >= min(dates), Expense.date <= max(dates))
            del args['dateBetween']
        query = super().filter(args, query)
        return query

class ExpenseSchema(ma.ModelSchema):
    class Meta:
        model = Expense