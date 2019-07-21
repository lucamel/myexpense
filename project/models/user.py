import datetime
import re

from marshmallow import fields, validates, ValidationError

from .. import db
from .. import ma
from .. import bcrypt
from ..helpers.mixins import ModelMixin

class User(ModelMixin, db.Model):

    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    confirmed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable = False)

    def __init__(self, email, name, password, confirmed=False):
        self.email = email
        self.name = name
        self.password = bcrypt.generate_password_hash(password)
        self.confirmed = confirmed

    def __repr__(self):
        return '<User: {0}>'.format(self.name)
        
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return self.confirmed

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.user_id

class UserSchema(ma.ModelSchema):
    password = fields.String(required=True)
    email = fields.Email(required=True)
    class Meta:
        model = User
        load_only = ["password",]

    @validates('email')
    def validate_email(self, value):
        if User.query.filter(User.email == value).first():
            raise ValidationError("User already exists.")

    @validates('password')
    def validate_password(self, value):
        if not(re.match(r'(?=.*[A-Z])(?=.*[0-9])(?=.*[a-z]).{8,}', value)):
            raise ValidationError("Password not compliant.")