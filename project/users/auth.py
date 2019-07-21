from .. import db, email, bcrypt
from ..models.user import User, UserSchema

def authenticate(username, password):
    user = User.query.filter_by(email=username).first()
    if user and user.confirmed and bcrypt.check_password_hash(user.password, password):
        return user

def identity(payload):
    user_id = payload['identity']
    return User.query.filter_by(user_id=user_id).first()


