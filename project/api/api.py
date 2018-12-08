from flask import Blueprint, make_response, jsonify, request, abort
from ..models.expense import Expense, ExpenseSchema
from ..models.account import Account, AccountSchema
from .. import db
from ..exceptions import InvalidRequest, ValidationApiError
from sqlalchemy import exc
from marshmallow.exceptions import ValidationError
import json, datetime

# Config
api_blueprint = Blueprint('api', __name__)

@api_blueprint.route('/api/v1/expenses', methods=['GET'])
def api_expenses_get_items():
    try:
        query = Expense.filter(request.args)
    except Exception as err:
        raise InvalidRequest('Invalid query params!', 400, type = err.__class__.__name__)
    data = query.all()
    return make_response(ExpenseSchema(many=True).jsonify(data))

@api_blueprint.route('/api/v1/expenses/<int:expense_id>/', methods=['GET'])
@api_blueprint.route('/api/v1/expenses/<int:expense_id>', methods=['GET'])
def api_expenses_get_item(expense_id):
    data = Expense.query.filter_by(expense_id=expense_id).first_or_404()
    return make_response(ExpenseSchema().jsonify(data))

@api_blueprint.route('/api/v1/expenses', methods=['POST'])
def api_expenses_post():
    if not request.json:
        abort(400)
    data = request.get_json()
    new_expense = Expense.save(data, ExpenseSchema)
    response = make_response('', 201)
    response.headers['Location'] = '/api/v1/expenses/' + str(new_expense.expense_id)
    return response

@api_blueprint.route('/api/v1/expenses/<int:expense_id>', methods=['DELETE'])
def api_expenses_delete_item(expense_id):
    expense = Expense.query.filter_by(expense_id=expense_id).first()
    if expense is not None:
        Expense.delete(expense)
    return make_response(jsonify('Deleted'), 204)

@api_blueprint.route('/api/v1/expenses/<int:expense_id>', methods=['PUT'])
def api_expenses_update_item(expense_id):
    if not request.json:
        abort(400)
    data = request.get_json()
    expense = Expense.query.filter_by(expense_id=expense_id).first_or_404()
    if expense is None:
        abort(404)
    if "date" in data and type(data["date"]) is str:
        data["date"] = datetime.datetime.strptime(data["date"], "%Y-%m-%d")
    expense.update(data)
    return make_response(ExpenseSchema().jsonify(expense), 200)

# Accounts routes
@api_blueprint.route('/api/v1/accounts', methods=['GET'])
def api_accounts_get_items():
    try:
        query = Account.filter(request.args)
    except Exception as err:
        raise InvalidRequest('Invalid query params!', 400, type = err.__class__.__name__)
    data = query.all()
    return make_response(AccountSchema(many=True).jsonify(data))

@api_blueprint.route('/api/v1/accounts/<int:account_id>/', methods=['GET'])
@api_blueprint.route('/api/v1/accounts/<int:account_id>', methods=['GET'])
def api_accounts_get_item(account_id):
    data = Account.query.filter_by(account_id=account_id).first_or_404()
    account = AccountSchema().jsonify(data)
    return make_response(account)

@api_blueprint.route('/api/v1/accounts', methods=['POST'])
def api_accounts_post():
    if not request.json:
        abort(400)
    data = request.get_json()
    new_account = Account.save(data, AccountSchema)
    response = make_response('', 201)
    response.headers['Location'] = '/api/v1/accounts/' + str(new_account.account_id)
    return response

@api_blueprint.route('/api/v1/accounts/<int:account_id>', methods=['DELETE'])
def api_accounts_delete_item(account_id):
    account = Account.query.filter_by(account_id=account_id).first()
    if account is not None:
        Account.delete(account)
    return make_response(jsonify('Deleted'), 204)

@api_blueprint.route('/api/v1/accounts/<int:account_id>', methods=['PUT'])
def api_accounts_update_item(account_id):
    if not request.json:
        abort(400)
    data = request.get_json()
    account = Account.query.filter_by(account_id=account_id).first_or_404()
    if account is None:
        abort(404)
    account.update(data)
    return make_response(AccountSchema().jsonify(account), 200)