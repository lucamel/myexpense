import json, datetime

from flask import Blueprint, make_response, jsonify, request, abort, render_template, url_for
from flask_jwt import jwt_required, current_identity
from marshmallow.exceptions import ValidationError
from sqlalchemy import exc
from sqlalchemy.orm import lazyload, joinedload, selectinload, raiseload

from .. import db, email
from ..exceptions import InvalidRequest, ValidationApiError
from ..models.user import User, UserSchema
from ..models.expense import Expense, ExpenseSchema
from ..models.account import  Account, AccountSchema
from ..token import generate_confirmation_token, confirm_token


# Config
api_blueprint = Blueprint('api', __name__)

# Users routes
@api_blueprint.route('/api/v1/user/<int:user_id>/', methods=['GET'])
@api_blueprint.route('/api/v1/user/<int:user_id>', methods=['GET'])
def api_user_get_item(user_id):
    data = User.query.filter_by(user_id=user_id).first_or_404()
    return make_response(UserSchema().jsonify(data), 200)

@api_blueprint.route('/api/v1/user/', methods=['GET'])
@api_blueprint.route('/api/v1/user', methods=['GET'])
@jwt_required()
def api_user_get_current_user():
    return make_response(UserSchema().jsonify(current_identity), 200)

@api_blueprint.route('/api/v1/register', methods=['POST'])
def api_user_register():
    if not request.json:
        abort(400)
    data = request.get_json()
    new_user = User.save(data, UserSchema)
    response = make_response('', 201)
    response.headers['Location'] = '/api/v1/user/' + str(new_user.user_id)
    token = generate_confirmation_token(data['email'])
    confirm_url = url_for('users.user_confirm', token=token, _external=True)
    html = render_template('users/email/confirm.html', confirm_url=confirm_url, user=new_user)
    subject = "Welcome to MyExpense, please confirm your email."
    email.AsyncEmail(new_user.email, subject, html).start()
    return response

# Expenses routes
@api_blueprint.route('/api/v1/expenses/', methods=['GET'])
@api_blueprint.route('/api/v1/expenses', methods=['GET'])
@jwt_required()
def api_expenses_get_items():
    try:
        query = Expense.filter(request.args)
    except Exception as err:
        raise InvalidRequest('Invalid query params!', 400, type = err.__class__.__name__)
    data = query.filter_by(user_id=current_identity.user_id).all()
    return make_response(ExpenseSchema(many=True).jsonify(data), 200)

@api_blueprint.route('/api/v1/expenses/<int:expense_id>/', methods=['GET'])
@api_blueprint.route('/api/v1/expenses/<int:expense_id>', methods=['GET'])
def api_expenses_get_item(expense_id):
    data = Expense.query.filter_by(expense_id=expense_id).first_or_404()
    return make_response(ExpenseSchema().jsonify(data), 200)

@api_blueprint.route('/api/v1/expenses', methods=['POST'])
@jwt_required()
def api_expenses_post():
    if not request.json:
        abort(400)
    data = request.get_json()
    data["user_id"] = current_identity.user_id
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
@api_blueprint.route('/api/v1/accounts/', methods=['GET'])
@api_blueprint.route('/api/v1/accounts', methods=['GET'])
def api_accounts_get_items():
    try:
        query = Account.filter(request.args)
    except Exception as err:
        raise InvalidRequest('Invalid query params!', 400, type = err.__class__.__name__)
    data = query.options(raiseload('expenses')).all()
    return make_response(AccountSchema(many=True, exclude=('expenses',)).jsonify(data), 200)

@api_blueprint.route('/api/v1/accounts/<int:account_id>/', methods=['GET'])
@api_blueprint.route('/api/v1/accounts/<int:account_id>', methods=['GET'])
def api_accounts_get_item(account_id):
    data = Account.query.options(raiseload('expenses')).filter_by(account_id=account_id).first_or_404()
    account = AccountSchema(exclude=('expenses',)).jsonify(data)
    return make_response(account, 200)

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

@api_blueprint.route('/api/v1/accounts/<int:account_id>/expenses', methods=['GET'])
def api_accounts_get_expenses_items(account_id):
    data = Account.query.filter_by(account_id=account_id).first_or_404().expenses
    expenses = ExpenseSchema(many=True, exclude=("account",)).jsonify(data)
    return make_response(expenses, 200)

@api_blueprint.route('/api/v1/accounts/<int:account_id>/expenses/<int:expense_id>/', methods=['GET'])
@api_blueprint.route('/api/v1/accounts/<int:account_id>/expenses/<int:expense_id>', methods=['GET'])
def api_accounts_get_expenses_item(account_id, expense_id):
    data = Account.query.filter_by(account_id=account_id).first_or_404().expenses.filter(Expense.expense_id == expense_id).first_or_404()
    return make_response(ExpenseSchema(exclude=("account",)).jsonify(data))

@api_blueprint.route('/api/v1/accounts/<int:account_id>/expenses', methods=['POST'])
@jwt_required()
def api_accounts_post_expenses(account_id):
    if not request.json:
        abort(400)
    data = request.get_json()
    data["user_id"] = current_identity.user_id
    data['account_id'] = account_id
    new_expense = Expense.save(data, ExpenseSchema)
    response = make_response('', 201)
    response.headers['Location'] = '/api/v1/expenses/' + str(new_expense.expense_id)
    return response

@api_blueprint.route('/api/v1/accounts/<int:account_id>/expenses/<int:expense_id>', methods=['DELETE'])
def api_accounts_delete_expenses_item(account_id, expense_id):
    expense = Account.query.filter_by(account_id=account_id).first_or_404().expenses.filter(Expense.expense_id == expense_id).first()
    if expense is not None:
        Expense.delete(expense)
    return make_response(jsonify('Deleted'), 204)

@api_blueprint.route('/api/v1/accounts/<int:account_id>/expenses/<int:expense_id>', methods=['PUT'])
def api_accounts_update_expenses_item(account_id, expense_id):
    if not request.json:
        abort(400)
    data = request.get_json()
    data["account_id"] = account_id
    expense = Account.query.filter_by(account_id=account_id).first_or_404().expenses.filter(Expense.expense_id == expense_id).first_or_404()
    if expense is None:
        abort(404)
    if "date" in data and type(data["date"]) is str:
        data["date"] = datetime.datetime.strptime(data["date"], "%Y-%m-%d")
    expense.update(data)
    return make_response(ExpenseSchema().jsonify(expense), 200)