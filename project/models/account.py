from .. import db
from .. import ma
from ..helpers.mixins import ModelMixin
from marshmallow import fields

class Account(ModelMixin, db.Model):
    filters = ['name', 'user_id', 'account_id']

    __tablename__ = 'accounts'

    account_id = db.Column(db.Integer, primary_key=True)
    plafond = db.Column(db.Integer, nullable=True)
    name = db.Column(db.String(40), nullable=False)
    has_plafond = db.Column(db.Boolean, nullable=False, default=False)
    user_id = db.Column(db.Integer, nullable=False)

    def __init__(self, plafond, name, has_plafond, user_id):
        self.plafond = plafond
        self.name = name
        self.has_plafond = has_plafond
        self.user_id = user_id

    def __repr__(self):
        return '<Account: {0}>'.format(self.name)

class AccountSchema(ma.ModelSchema):
    class Meta:
        model = Account