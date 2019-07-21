import datetime

from marshmallow import fields

from .. import db
from .. import ma
from ..helpers.mixins import ModelMixin

class Account(ModelMixin, db.Model):

    filters = ['name', 'account_id']

    __tablename__ = 'accounts'

    account_id = db.Column(db.Integer, primary_key=True)
    plafond = db.Column(db.Integer, nullable=True)
    name = db.Column(db.String(40), nullable=False)
    has_plafond = db.Column(db.Boolean, nullable=False, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    initial_balance = db.Column(db.Integer, nullable=True)
    expenses = db.relationship('Expense', backref="account", lazy='dynamic')

    def __repr__(self):
        return '<Account: {0}>'.format(self.name)

class AccountSchema(ma.ModelSchema):
    expenses = fields.Nested('ExpenseSchema', many=True, exclude=('account', ))
    _links = ma.Hyperlinks(
        {"self": ma.URLFor("api.api_accounts_get_item", account_id="<account_id>"), 
        "collection": ma.URLFor("api.api_accounts_get_items")
        }
    )

    class Meta:
        model = Account