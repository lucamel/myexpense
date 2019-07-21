import json, datetime

from flask import Blueprint, make_response, jsonify, request, abort, render_template, url_for
from flask_jwt import jwt_required, current_identity
from marshmallow.exceptions import ValidationError
from sqlalchemy import exc
from sqlalchemy.orm import lazyload, joinedload, selectinload, raiseload

from .. import db, email
from ..exceptions import InvalidRequest, ValidationApiError
from ..helpers.pagination import Pagination
from ..models.user import User, UserSchema
from ..models.expense import Expense, ExpenseSchema
from ..models.account import  Account, AccountSchema
from ..models.balance import Balance, BalanceSchema
from ..token import generate_confirmation_token, confirm_token


# Config
api_blueprint = Blueprint('api', __name__)

# Users routes
@api_blueprint.route('/api/v1/user/<int:user_id>/', methods=['GET'])
@api_blueprint.route('/api/v1/user/<int:user_id>', methods=['GET'])
def api_user_get_item(user_id):
    user = User.query.filter_by(user_id=user_id).first_or_404()
    return make_response(UserSchema().jsonify(user), 200)

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
    subject = 'Welcome to MyExpense, please confirm your email.'
    email.AsyncEmail(new_user.email, subject, html).start()
    return response

# Expenses routes
@api_blueprint.route('/api/v1/expenses/', methods=['GET'])
@api_blueprint.route('/api/v1/expenses', methods=['GET'])
@jwt_required()
def api_expenses_get_items():
    try:
        query = Expense.filter(request.args).filter_by(user_id=current_identity.user_id)
    except Exception as err:
        raise InvalidRequest('Invalid query params!', 400, type = err.__class__.__name__)
    expenses = Pagination(query, request, 'expenses')
    paginated = expenses.paginated_json(ExpenseSchema(many=True).dump(expenses.data).data)
    return make_response(jsonify(paginated), 200)

@api_blueprint.route('/api/v1/expenses/<int:expense_id>/', methods=['GET'])
@api_blueprint.route('/api/v1/expenses/<int:expense_id>', methods=['GET'])
@jwt_required()
def api_expenses_get_item(expense_id):
    expense = Expense.query.filter_by(expense_id=expense_id).first_or_404()
    if expense.user_id != current_identity.user_id:
        abort(403)
    return make_response(ExpenseSchema().jsonify(expense), 200)

@api_blueprint.route('/api/v1/expenses', methods=['POST'])
@jwt_required()
def api_expenses_post():
    if not request.json:
        abort(400)
    data = request.get_json()
    data['user_id'] = current_identity.user_id
    new_expense = Expense.save(data, ExpenseSchema)
    response = make_response('', 201)
    response.headers['Location'] = '/api/v1/expenses/' + str(new_expense.expense_id)
    return response

@api_blueprint.route('/api/v1/expenses/<int:expense_id>', methods=['DELETE'])
@jwt_required()
def api_expenses_delete_item(expense_id):
    expense = Expense.query.filter_by(expense_id=expense_id).first()
    if expense.user_id != current_identity.user_id:
        abort(403)
    if expense is not None:
        Expense.delete(expense)
    return make_response(jsonify('Deleted'), 204)


@api_blueprint.route('/api/v1/expenses/<int:expense_id>', methods=['PUT'])
@jwt_required()
def api_expenses_update_item(expense_id):
    if not request.json:
        abort(400)
    data = request.get_json()
    data['user_id'] = current_identity.user_id
    expense = Expense.query.filter_by(expense_id=expense_id).first_or_404()
    if expense is None:
        abort(404)
    if expense.user_id != current_identity.user_id:
        abort(403)
    if 'date' in data and type(data['date']) is str:
        data['date'] = datetime.datetime.strptime(data['date'], '%Y-%m-%d')
    expense.update(data)
    return make_response(ExpenseSchema().jsonify(expense), 200)

# Accounts routes
@api_blueprint.route('/api/v1/accounts/', methods=['GET'])
@api_blueprint.route('/api/v1/accounts', methods=['GET'])
@jwt_required()
def api_accounts_get_items():
    try:
        query = Account.filter(request.args)
    except Exception as err:
        raise InvalidRequest('Invalid query params!', 400, type = err.__class__.__name__)
    account = query.options(raiseload('expenses')).filter_by(user_id=current_identity.user_id).all()
    return make_response(AccountSchema(many=True, exclude=('expenses', )).jsonify(account), 200)

@api_blueprint.route('/api/v1/accounts/<int:account_id>/', methods=['GET'])
@api_blueprint.route('/api/v1/accounts/<int:account_id>', methods=['GET'])
@jwt_required()
def api_accounts_get_item(account_id):
    account = Account.query.options(raiseload('expenses')).filter_by(account_id=account_id).first_or_404()
    if account.user_id != current_identity.user_id:
        abort(403)
    return make_response(AccountSchema(many=False, exclude=('expenses', )).jsonify(account), 200)

@api_blueprint.route('/api/v1/accounts', methods=['POST'])
@jwt_required()
def api_accounts_post():
    if not request.json:
        abort(400)
    data = request.get_json()
    data['user_id'] = current_identity.user_id
    new_account = Account.save(data, AccountSchema)
    response = make_response('', 201)
    response.headers['Location'] = '/api/v1/accounts/' + str(new_account.account_id)
    return response

@api_blueprint.route('/api/v1/accounts/<int:account_id>', methods=['DELETE'])
@jwt_required()
def api_accounts_delete_item(account_id):
    account = Account.query.filter_by(account_id=account_id).first()
    if account.user_id != current_identity.user_id:
        abort(403)
    if account is not None:
        Account.delete(account)
    return make_response(jsonify('Deleted'), 204)

@api_blueprint.route('/api/v1/accounts/<int:account_id>', methods=['PUT'])
@jwt_required()
def api_accounts_update_item(account_id):
    if not request.json:
        abort(400)
    data = request.get_json()
    data['user_id'] = current_identity.user_id
    account = Account.query.filter_by(account_id=account_id).first_or_404()
    if account is None:
        abort(404)
    if account.user_id != current_identity.user_id:
        abort(403)
    account.update(data)
    return make_response(AccountSchema().jsonify(account), 200)

@api_blueprint.route('/api/v1/accounts/<int:account_id>/expenses', methods=['GET'])
@jwt_required()
def api_accounts_get_expenses_items(account_id):
    try:
        query = Expense.filter(request.args).filter_by(user_id=current_identity.user_id, account_id=account_id)
    except Exception as err:
        raise InvalidRequest('Invalid query params!', 400, type = err.__class__.__name__)
    expenses = Pagination(query, request, 'expenses')
    paginated = expenses.paginated_json(ExpenseSchema(many=True, exclude=('account',)).dump(expenses.data).data)
    return make_response(jsonify(paginated), 200)

@api_blueprint.route('/api/v1/accounts/<int:account_id>/expenses/<int:expense_id>/', methods=['GET'])
@api_blueprint.route('/api/v1/accounts/<int:account_id>/expenses/<int:expense_id>', methods=['GET'])
@jwt_required()
def api_accounts_get_expenses_item(account_id, expense_id):
    expense = Expense.query.filter_by(expense_id=expense_id, account_id=account_id).first_or_404()
    if expense.user_id != current_identity.user_id:
        abort(403)
    return make_response(ExpenseSchema(exclude=('account',)).jsonify(expense))

@api_blueprint.route('/api/v1/accounts/<int:account_id>/expenses', methods=['POST'])
@jwt_required()
def api_accounts_post_expenses(account_id):
    if not request.json:
        abort(400)
    account = Account.query.filter_by(account_id=account_id).first_or_404()
    if account_id != current_identity.user_id:
        abort(403)
    data = request.get_json()
    data['user_id'] = current_identity.user_id
    data['account_id'] = account_id
    new_expense = Expense.save(data, ExpenseSchema)
    response = make_response('', 201)
    response.headers['Location'] = '/api/v1/expenses/' + str(new_expense.expense_id)
    return response

@api_blueprint.route('/api/v1/accounts/<int:account_id>/expenses/<int:expense_id>', methods=['DELETE'])
@jwt_required()
def api_accounts_delete_expenses_item(account_id, expense_id):
    expense = Expense.query.filter_by(expense_id=expense_id, account_id=account_id).first_or_404()
    if expense.user_id != current_identity.user_id:
        abort(403)
    if expense is not None:
        Expense.delete(expense)
    return make_response(jsonify('Deleted'), 204)

@api_blueprint.route('/api/v1/accounts/<int:account_id>/expenses/<int:expense_id>', methods=['PUT'])
@jwt_required()
def api_accounts_update_expenses_item(account_id, expense_id):
    if not request.json:
        abort(400)
    data = request.get_json()
    data['user_id'] = current_identity.user_id
    data['account_id'] = account_id
    expense = Expense.query.filter_by(expense_id=expense_id, account_id=account_id).first_or_404()
    if expense is None:
        abort(404)
    if expense.user_id != current_identity.user_id:
        abort(403)    
    if 'date' in data and type(data['date']) is str:
        data['date'] = datetime.datetime.strptime(data['date'], '%Y-%m-%d')
    expense.update(data)
    return make_response(ExpenseSchema().jsonify(expense), 200)

@api_blueprint.route('/api/v1/accounts/<int:account_id>/balance/', methods=['GET'])
@api_blueprint.route('/api/v1/accounts/<int:account_id>/balance', methods=['GET'])
@jwt_required()
def api_accounts_get_balance(account_id):
    account = Account.query.options(raiseload('expenses')).filter_by(account_id=account_id).first_or_404()
    if account.user_id != current_identity.user_id:
        abort(403)
    try:
        from_date = datetime.datetime.strptime(request.args.get('from'), "%Y-%m-%d") if request.args.get('from') is not None else datetime.date.min
        to_date = datetime.datetime.strptime(request.args.get('to'), "%Y-%m-%d") if request.args.get('to') is not None else datetime.date.today()
        if from_date > to_date:
            raise InvalidRequest('Invalid query params: to should be greater than from', 400, type = "DateFilterError")
        year = request.args.get('year') if request.args.get('year') is not None else datetime.date.today().year
        month = request.args.get('month') if request.args.get('month') is not None else datetime.date.today().month
        m_date = datetime.date(int(year), int(month), 1)
    except ValueError as err:
        raise InvalidRequest('Invalid query params!', 400, type = err.__class__.__name__)
    balance = Balance(current_identity.user_id, account, from_date, to_date, m_date)
    return make_response(BalanceSchema().jsonify(balance), 200)

@api_blueprint.route('/api/v1/balance/', methods=['GET'])
@api_blueprint.route('/api/v1/balance', methods=['GET'])
@jwt_required()
def api_get_balance():
    try:
        from_date = datetime.datetime.strptime(request.args.get('from'), "%Y-%m-%d") if request.args.get('from') is not None else datetime.date.min
        to_date = datetime.datetime.strptime(request.args.get('to'), "%Y-%m-%d") if request.args.get('to') is not None else datetime.date.today()
        if from_date > to_date:
            raise InvalidRequest('Invalid query params: to should be greater than from', 400, type = "DateFilterError")
    except ValueError as err:
        raise InvalidRequest('Invalid query params!', 400, type = err.__class__.__name__)
    balance = Balance(current_identity.user_id, from_date=from_date, to_date=to_date)
    return make_response(BalanceSchema(exclude=('account',)).jsonify(balance), 200)