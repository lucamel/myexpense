import datetime

from marshmallow import fields

from .. import db
from .. import ma
from ..helpers.mixins import ModelMixin

class Expense(ModelMixin, db.Model):

    filters = ['category', 'account_id', 'from', 'to']

    __tablename__ = 'expenses'
    
    expense_id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(40), nullable = False)
    date = db.Column(db.Date, nullable = False)
    note = db.Column(db.String(200), nullable = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.account_id'), nullable=False)

    def __init__(self, amount, category, date, user_id, account_id=None, note=None):
        if type(date) is str:
            date = datetime.datetime.strptime(date, "%Y-%m-%d")
        self.amount = amount
        self.category = category
        self.date = date
        self.user_id = user_id
        self.account_id = account_id
        self.note = note

    def __repr__(self):
        return '<Expense: {0} {1} {2} {3}, {4}>'.format(self.date, self.category, self.amount, self.account_id, self.user_id)

    @classmethod
    def filter(self, args):
        args = args.copy()
        query = self.query
        if(args.get('from') is not None): 
            fromDate = datetime.datetime.strptime(args.get('from'), "%Y-%m-%d")
            query = query.filter(Expense.date >= fromDate)
            del args['from']
        if(args.get('to') is not None):
            toDate = datetime.datetime.strptime(args.get('to'), '%Y-%m-%d')
            query = query.filter(Expense.date <= toDate)
            del args['to']
        query = super().filter(args, query)
        return query

class ExpenseSchema(ma.ModelSchema):
    account = fields.Nested("AccountSchema", only=('account_id','name', '_links'))
    _links = ma.Hyperlinks(
        {"self": ma.URLFor("api.api_expenses_get_item", expense_id="<expense_id>"), 
        "collection": ma.URLFor("api.api_expenses_get_items")
        }
    )

    class Meta:
        model = Expense