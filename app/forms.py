# forms.py, forms for the Flask application
# 2024


#         CONTENTS OF THIS FILE A-Z
#    *Imports                     | ~Line 12-17
#    Login                      | ~Line 22-30   -Dominic Minnich
#    Registration               | ~Line 35-38   -Dominic Minnich
#    .?.?.                      | ~Line ??


from wtforms import PasswordField
from wtforms.validators import Length, EqualTo
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, ValidationError
from .models import User
from flask_wtf import FlaskForm


# RegistrationForm class, inherits from FlaskForm
# User contains username and password fields
class RegistrationForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=4, max=25)]
    )
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Register")


# LoginForm class, inherits from FlaskForm
# User requires correct username and password fields to be authorized
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")
