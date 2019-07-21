#  project/users/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length, EqualTo, Email, Regexp, ValidationError

from ..models.user import User

class RegisterForm(FlaskForm):
    name = StringField('Name', validators = [DataRequired(), Length(min = 3, max = 25)])
    email = StringField('Email', validators = [DataRequired(), Email(), Length(min = 6, max = 40)])
    password = PasswordField('Password', validators = [DataRequired(), Regexp('(?=.*[A-Z])(?=.*[0-9])(?=.*[a-z]).{8,}', message='Password not compliant.')])
    confirm = PasswordField('Repeat Password', validators = [DataRequired(), EqualTo('password', message='Passwords must match.')])

    def validate_email(self, field):
        user = User.query.filter(User.email==field.data).first()
        if user is not None:
            raise ValidationError("User already registered.")
        return True
        


class LoginForm(FlaskForm):
    email = StringField('Email', validators = [DataRequired()])
    password = PasswordField('Password', validators = [DataRequired()])
