# forms.py, forms for the Flask application
# 2024


#         CONTENTS OF THIS FILE A-Z
#    *Imports                     | ~Line 12-17
#    Login                      | ~Line 22-30   -Dominic Minnich
#    Registration               | ~Line 35-38   -Dominic Minnich
#    Create Project             | ~Line 54-60   -Kyle Benich

from wtforms import PasswordField
from wtforms import (
    StringField,
    SelectField,
    SubmitField,
    PasswordField,
    BooleanField,
    IntegerField,
    DateTimeField,
    HiddenField,
)
from wtforms import TextAreaField  # Add this import
from wtforms.validators import DataRequired, Length, EqualTo, Email, URL
from .models import User
from flask_wtf import FlaskForm


# RegistrationForm class, inherits from FlaskForm
# User contains username and password fields
class RegistrationForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=4, max=25)]
    )
    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email(message="Invalid email address."),
            Length(max=120),
        ],
    )
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=50)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=50)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Register")


# LoginForm class, inherits from FlaskForm
# User requires correct username and password fields to be authorized
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Login")


# CreateProjectForm class, inherits from FlaskForm
class CreateProjectForm(FlaskForm):
    link = StringField("Link to Figma Project", validators=[DataRequired()])
    major_tasks = StringField("Major Tasks")
    major_tasks_hidden = HiddenField("Major Tasks Hidden")
    collaborators = StringField("Collaborators")
    collaborators_hidden = HiddenField("Collaborators Hidden")
    submit = SubmitField("Create Project")


# Form to edit the account type of a user
class EditAccountTypeForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    role = SelectField(
        "Role",
        choices=[
            ("Student", "Student"),
            ("Project Manager", "Project Manager"),
            ("Admin", "Admin"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Confirm")


# Form to delete a user
class DeleteUserForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    submit = SubmitField("Delete User")


# Form to delete a project
class DeleteProjectForm(FlaskForm):
    project_id = StringField("Project ID", validators=[DataRequired()])
    submit = SubmitField("Delete Project")
