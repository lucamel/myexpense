import datetime

from marshmallow import fields

from .. import db
from .. import ma
from ..helpers.mixins import ModelMixin

class Account(ModelMixin, db.Model):

    filters = ['name', 'user_id', 'account_id']

    __tablename__ = 'accounts'

    account_id = db.Column(db.Integer, primary_key=True)
    plafond = db.Column(db.Integer, nullable=True)
    name = db.Column(db.String(40), nullable=False)
    has_plafond = db.Column(db.Boolean, nullable=False, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    expenses = db.relationship('Expense', backref="account", lazy='dynamic')

    def __repr__(self):
        return '<Account: {0}>'.format(self.name)

class AccountSchema(ma.ModelSchema):
    expenses = fields.Nested('ExpenseSchema', many=True, exclude=('account', ))
    class Meta:
        model = Account