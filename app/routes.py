# routes.py, routes for the Flask application
# 2024


#         CONTENTS OF THIS FILE
#    *Imports                     | ~Line 12-17
#    Blueprint                      | ~Line 22-30   -Dominic Minnich
#    LoginManager Instance          | ~Line 35-38   -Dominic Minnich
#               ROUTES A->Z
#    /                      | ~Line 35-38   -Dominic Minnich
#    /clear-login-sucess    | ~Line 35-38   -Dominic Minnich
#    /logout                | ~Line 35-38   -Dominic Minnich
#    /login                 | ~Line 35-38   -Dominic Minnich
#    /register              | ~Line 35-38   -Dominic Minnich
#    User_loader            | ~Line 35-38   -Dominic Minnich
#    /profile               | ~Line 96-100   -Kyle Benich
#    /settings              | ~Line 102-106   -Kyle Benich
#    /viewProjects          | ~Line 108-111   -Sulaiman Hussain
#    /aboutUs               | ~Line 35-38   -Dominic Minnich
#    /createProject         | ~Line 194-212   -Kyle Benich

# Imports
from flask import (
    Blueprint,
    render_template,
    redirect,
    session,
    url_for,
    flash,
    request,
    jsonify,
)
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
    LoginManager,
)

from .models import db, User, Project
from .forms import RegistrationForm, LoginForm, CreateProjectForm  # Import the form
import json  # Import json module
import logging  # Import logging module
from datetime import datetime, timedelta  # Import datetime and timedelta

# Blueprint
main = Blueprint("main", __name__)
# LoginManager instance
login_manager = LoginManager()


# Routes
# /
@main.route("/")
@login_required
def home():
    return render_template("home.html", user=current_user)


# /aboutUs route
@main.route('/aboutUs')
def aboutUs():
    return render_template('aboutUs.html')


# /clear-login-success
@main.route("/clear-login-success", methods=["POST"])
def clear_login_success():
    session.pop("login_success", None)
    return "", 204  # Return 'No Content' response


# /logout
@main.route("/logout")
def logout():
    logout_user()
    flash("Logged Out Successfully!", "success")
    return redirect(url_for("main.login"))


# /login
@main.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None:
            flash("- Username Not Found -", "danger")
        elif not user.check_password(form.password.data):
            flash("- Incorrect Password -", "danger")
        else:
            login_user(user)
            flash("Logged In Successfully!", "success")  # Only success message
            return render_template("login.html", form=form)

    return render_template("login.html", form=form)


# routes.py
@main.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if the email already exists
        existing_user_email = User.query.filter_by(email=form.email.data).first()
        if existing_user_email:
            flash(
                "Email already exists. Please use a different email address.", "danger"
            )
            return render_template("register.html", form=form)

        # Check if the username already exists
        existing_user_username = User.query.filter_by(
            username=form.username.data
        ).first()
        if existing_user_username:
            flash(
                "Username already exists. Please choose a different username.", "danger"
            )
            return render_template("register.html", form=form)

        # Create and add the new user if validations pass
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role="student",
            calibrated=False,
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("main.login"))

    else:
        # Flash validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{form[field].label.text}: {error}", "danger")

    return render_template("register.html", form=form)


# User_loader
@login_manager.user_loader
def load_user(user_id):
    # Since user_id is now a UUID string, I removed the int() conversion
    return User.query.get(user_id)

# /profile
@main.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)


# /settings
@main.route("/settings")
@login_required
def settings():
    return render_template("settings.html", user=current_user)


#@main.route("/ViewProjects")
#@login_required
#def ViewProjects():
 # return render_template("ViewProjects.html", user=current_user)

@main.route("/viewProjects")
@login_required
def viewProjects():
    projects_list = current_user.projects  # Access the projects list (e.g., from a JSON attribute)
    
    if projects_list is None:
        projects_list = []
    
    project_ids = [project['project_id'] for project in projects_list]
    projects = Project.query.filter(Project.id.in_(project_ids)).all()
    return render_template("ViewProjects.html", user=current_user, projects=projects)


@main.route("/adminPanel")
@login_required
def adminPanel():
    if current_user.role == "admin":  # Only admins can access the admin panel
        return render_template("adminPanel.html", user=current_user)
    else:
        return redirect(url_for("main.home"))  # Redirect to home if not an admin

# Configure logging KB
logging.basicConfig(level=logging.INFO) #Can be deleted later, just for testing

@main.route("/createProject", methods=["GET", "POST"])
@login_required
def createProject():
    form = CreateProjectForm()
    if form.validate_on_submit():
        default_eol_time = datetime.utcnow() + timedelta(weeks=1)  # Set default end of life time to 1 week from now
        default_max_submissions = 100  # Set default max submissions

        # Handle tasks and collaborators as JSON arrays
        tasks = json.loads(form.tasks.data)
        collaborators = json.loads(form.collaborators.data)

        new_project = Project(
            link=form.link.data,
            creator=current_user.id,
            priviledged=True,
            tasks=tasks,  # Use tasks JSON
            max_submissions=default_max_submissions,  # Use default max submissions
            eol_time=default_eol_time,  # Use default end of life time
            collaborators=collaborators,  # Use collaborators JSON
            numPauses=0
        )
        db.session.add(new_project)
        db.session.commit()
        flash("Project created successfully!", "success")
        return redirect(url_for("main.viewProjects"))
    else:
        logging.warning("Form validation failed")  # Log when the form validation fails
        for field, errors in form.errors.items():
            for error in errors:
                logging.warning(f"Validation error in {field}: {error}")  # Log validation errors
    return render_template("CreateProject.html", form=form)