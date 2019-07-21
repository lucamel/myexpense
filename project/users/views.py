# project/users/views.py
import datetime
from flask import Blueprint, make_response, jsonify, request, abort, render_template, redirect, url_for, session, flash
from flask_login import login_user, logout_user, login_required, current_user

from .. import db, email, bcrypt
from ..models.user import User, UserSchema
from ..token import generate_confirmation_token, confirm_token
from .forms import RegisterForm, LoginForm

# Config
user_blueprint = Blueprint('users', __name__)

@user_blueprint.route('/register', methods=['GET', 'POST'])
def user_register():
    error = None
    form = RegisterForm(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            new_user = User.save({"name":form.name.data, "email":form.email.data, "password":form.password.data}, UserSchema)
            _send_confirmation_email(new_user)
            flash('You are successful registered. Click on the link we send you to your email to confirm your address', 'success')
            return redirect(url_for('users.user_login'))
    return render_template('users/register.html', form=form, error=error)

@user_blueprint.route('/login', methods=['GET', 'POST'])
def user_login():
    error = None
    form = LoginForm(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            user = User.query.filter_by(email = form.email.data).first()
            if user is not None and bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('users.home'))
            flash('Invalid credentials.', 'danger')
    return render_template('users/login.html', form=form, error=error)

@user_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('users.user_login'))

@user_blueprint.route('/confirm/<token>', methods=['GET'])
def user_confirm(token):
    email = confirm_token(token)
    if (email):
        user = User.query.filter_by(email=email).first_or_404()
        if user.confirmed:
            flash('Account already confirmed. Please login.', 'success')
        else:
            flash('Congratulations, your account is now active. You can login.', 'success')
            user.update({"confirmed":True})
    else:
        token_expired(token)
    return redirect(url_for('users.user_login'))

def token_expired(token):
    email = confirm_token(token, None)
    user = User.query.filter_by(email=email).first_or_404()
    _send_confirmation_email(user)
    flash('The confirmation link is invalid or has expired. A new one has been sent to your email.', 'danger')
    return redirect(url_for('users.user_login'))

@user_blueprint.route('/', methods=['GET'])
@login_required
def home():
    return "Welcome " + current_user.email

def _send_confirmation_email(user):
    token = generate_confirmation_token(user.email)
    confirm_url = url_for('users.user_confirm', token=token, _external=True)
    expiration_date = '{:%d-%m-%Y %H:%M}'.format(datetime.datetime.utcnow() + datetime.timedelta(hours=1))
    html = render_template('users/email/confirm.html', confirm_url=confirm_url, user=user, expiration_date=expiration_date)
    subject = "Welcome to MyExpense, please confirm your email."
    email.AsyncEmail(user.email, subject, html).start()
