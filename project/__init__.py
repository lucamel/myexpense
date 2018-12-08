# init MyExpense API
from flask import Flask, make_response, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from .exceptions import InvalidRequest
from sqlalchemy.exc import DatabaseError
from .helpers import error_log
import datetime

app = Flask(__name__)
app.config.from_pyfile('_config.py')

db = SQLAlchemy(app)
ma = Marshmallow(app)
migrate = Migrate(app, db)

from .models import *

# import Blueprint
from .api.api import api_blueprint

app.register_blueprint(api_blueprint)

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
        now = datetime.datetime.now()
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