# init MyExpense API
import datetime

from flask import Flask, make_response, request, jsonify, redirect, flash
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_login import LoginManager
from flask_jwt import JWT
from sqlalchemy.exc import DatabaseError

from .models.models import db
from .exceptions import InvalidRequest
from .helpers import error_log

app = Flask(__name__)
app.config.from_pyfile('_config.py')

bcrypt = Bcrypt(app)
mail = Mail(app)
db.init_app(app)
ma = Marshmallow(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)

from .models import *
from .models.user import User

# import Blueprint
from .api.api import api_blueprint
from .users.views import user_blueprint
from .users.auth import authenticate, identity

jwt = JWT(app, authenticate, identity)

@jwt.jwt_payload_handler
def make_payload(identity):
    iat = datetime.datetime.utcnow()
    exp = iat + app.config.get('JWT_EXPIRATION_DELTA')
    nbf = iat + app.config.get('JWT_NOT_BEFORE_DELTA')
    identity = getattr(identity, 'user_id') or identity['user_id']
    return {'exp': exp, 'iat': iat, 'nbf': nbf, 'identity': identity}

@jwt.auth_response_handler
def auth_response(access_token, identity):
    return jsonify({'access_token': access_token.decode('utf-8'), 'expires_in': int(app.config.get('JWT_EXPIRATION_DELTA').total_seconds())})

login_manager.login_view = "users.user_login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.user_id==user_id).first()

app.register_blueprint(api_blueprint)
app.register_blueprint(user_blueprint)

@app.errorhandler(404)
def not_found(err):
    if app.debug is True:
        error_log.write_log('{} {}: {}'.format(404, err.__class__.__name__, request.url))
    error = {
        "error": {
            "message" : str(err),
            "type" : err.__class__.__name__,
            }
        }
    return jsonify(error), 404

@app.errorhandler(DatabaseError)
def database_error(err):
    if app.debug is True:
        error_log.write_log('{} {}: {}'.format(500, err.__class__.__name__, request.url))
    error = {
        "error": {
            "message" : 'Error occurred during database activity',
            "type" : err.__class__.__name__,
            }
        }
    return jsonify(error), 500

@app.errorhandler(InvalidRequest)
def bad_request(err):
    if app.debug is True:
        error_log.write_log('{} {}: {}'.format(err.status_code, err.__class__.__name__, request.url))
    error = {
        "error": {
            "message" : err.message,
            "type" : err.type,
            }
        }
    if err.payload is not None:
        error['error'].update(err.payload)
    return jsonify(error), err.status_code

@app.errorhandler(500)
def internal_error(err):
    if app.debug is True:
        error_log.write_log('{} {}: {}'.format(500, err.__class__.__name__, request.url))
    error = {
        "error": {
            "message" : str(err),
            "type" : err.__class__.__name__ ,
            }
        }
    return jsonify(error), 500

if __name__ == "__main__":
    app.run()