# forms.py, forms for the Flask application

from wtforms import PasswordField
from wtforms.validators import Length, EqualTo
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, ValidationError
from .models import User
from flask_wtf import FlaskForm

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
