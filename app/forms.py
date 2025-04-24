# forms.py
from flask_wtf import FlaskForm
from wtforms import (StringField, SelectField, SubmitField, PasswordField,
                     BooleanField, HiddenField, TextAreaField)
from wtforms.validators import DataRequired, Length, EqualTo, Email, URL, Optional, Regexp
# Note: FileField, FileRequired, FileAllowed require: pip install Flask-WTF[email] (or just email separately) and Flask-Uploads (or handle file saving manually)
# For simplicity, we'll handle file saving manually in the route without Flask-Uploads for now. Add FileField manually:
from wtforms import FileField
from flask_wtf.file import FileRequired, FileAllowed

# --- Authentication Forms ---
class RegistrationForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=4, max=80),
            Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                   'Username must start with a letter and have only letters, '
                   'numbers, dots or underscores')
        ]
    )
    email = StringField("Email", validators=[DataRequired(), Email("Invalid email address."), Length(max=120)])
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=50)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=50)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, message='Password must be at least 6 characters long.')])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match.")
        ]
    )
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Login")

# --- Project Forms ---
class CreateProjectForm(FlaskForm):
    name = StringField("Project Name", validators=[DataRequired(), Length(max=150)])
    # Validate Figma link format more strictly
    link = StringField(
        "Link to Figma Project",
        validators=[
            DataRequired(),
            URL(message="Please enter a valid URL."),
            Regexp(r'^https:\/\/www\.figma\.com\/(file|design|proto)\/.+', 0,
                   'Please enter a valid Figma project, design, or prototype link.')
        ]
    )
    # Add the missing field
    major_tasks = HiddenField("Major Tasks")
    # Add collaborators field
    collaborators = HiddenField("Collaborators") 
    submit = SubmitField("Create Project")
class EditProjectForm(FlaskForm):
    name = StringField("Project Name", validators=[DataRequired(), Length(max=150)])
    link = StringField(
        "Figma Link",
        validators=[
            DataRequired(),
            URL(message="Please enter a valid URL."),
            Regexp(r'^https:\/\/www\.figma\.com\/(file|design|proto)\/.+', 0,
                   'Please enter a valid Figma project, design, or prototype link.')
        ]
    )
    submit = SubmitField("Save Changes")

# Simple form for task creation (example, use via AJAX or separate page)
class AddTaskForm(FlaskForm):
    name = StringField("Task Name", validators=[DataRequired(), Length(max=255)])
    # Add order field if manual ordering is needed
    submit = SubmitField("Add Task")

# Simple form for adding collaborators (example)
class AddCollaboratorForm(FlaskForm):
    email = StringField("Collaborator Email", validators=[DataRequired(), Email()])
    role = SelectField("Role", choices=[
        ('viewer', 'Viewer'),
        ('editor', 'Editor'),
        ('co-owner', 'Co-Owner') # Creator role assigned automatically
    ], validators=[DataRequired()])
    submit = SubmitField("Add Collaborator")


# --- Admin Forms ---
class EditAccountTypeForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    role = SelectField("Role", choices=[
            ("student", "Student"),
            ("project_manager", "Project Manager"),
            ("admin", "Admin")
        ], validators=[DataRequired()])
    submit = SubmitField("Update Role")

class DeleteUserForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    submit = SubmitField("Delete User Permanently") # Clarify action

class DeleteProjectForm(FlaskForm):
    project_id = HiddenField() # Use hidden field populated by route
    confirm_text = StringField("Type 'DELETE' to confirm", validators=[DataRequired(), EqualTo('DELETE', message="You must type DELETE exactly.")])
    submit = SubmitField("Delete Project Permanently")

# --- User Settings Forms ---
class UpdateAccountForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=4, max=80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=50)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=50)])
    email_opt_in = BooleanField("Receive email notifications")
    submit = SubmitField("Update Account")

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired(), Length(min=6)])
    confirm_new_password = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(),
            EqualTo("new_password", message="New passwords must match.")
        ]
    )
    submit = SubmitField("Change Password")

class UploadProfilePicForm(FlaskForm):
    picture = FileField('Update Profile Picture', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only!')
    ])
    submit = SubmitField('Upload Picture')
