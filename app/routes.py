# routes.py, routes for the Flask application
# 2024


#         CONTENTS OF THIS FILE
#    *Imports                     | ~Line 12-17
#    Blueprint                      | ~Line 22-30   -Dominic Minnich
#    LoginManager Instance          | ~Line 35-38   -Dominic Minnich
#    ValueSet                       | ~Line 35-38   -Dominic Minnich
#   get_user_projects                | ~Line 35-38   -Dominic Minnich
#   get_project_by_id                | ~Line 35-38   -Dominic Minnich
#   get_shared_projects              | ~Line 35-38   -Dominic Minnich

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
#    /adminPanel            | ~Line 246-298   -Sulaiman Hussain
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
from .forms import (
    RegistrationForm,
    LoginForm,
    CreateProjectForm,
    EditAccountTypeForm,
    DeleteUserForm,
    DeleteProjectForm,
)  # Import the form
import json  # Import json module
import logging  # Import logging module
from datetime import datetime, timedelta  # Import datetime and timedelta

# Blueprint
main = Blueprint("main", __name__)
# LoginManager instance
login_manager = LoginManager()


# VALUESET (for ease of value changing)  --Notice how these values are called in home.html route (mimic this)

# Max number of submissions per privilaged project
MAX_SUBMISSIONS_PER_USER_PRIVILAGED = 100
# Max number of submissions per unprivilaged project
MAX_SUBMISSIONS_PER_USER_UNPRIVILAGED = 10
# Max number of projects per Project Manager/Admin
MAX_PROJECTS_PER_USER_PRILVILAGED = 100
# Max number of projects per student
MAX_PROJECTS_PER_USER_UNPRIVILAGED = 4
# End of life time for a privilaged project
EOL_TIME_PRIVILAGED = 300
# End of life time for a unprivilaged project
EOL_TIME_UNPRIVILAGED = 10


# Function to get all projects for a user, using projecs.json from user to establish nice filter to projects table ids-Dominic Minnich
def get_user_projects(user_id):
    user = User.query.get(user_id)
    if not user or not user.projects:
        return jsonify({"error": "User not found or no projects available"}), 404

    try:
        project_ids = [project["project_id"] for project in json.loads(user.projects)]
        projects = Project.query.filter(Project.id.in_(project_ids)).all()
        project_data = [
            {
                "id": project.id,
                "link": project.link,
                "tasks": project.tasks,
                "collaborators": project.collaborators,
            }
            for project in projects
        ]
        return jsonify(project_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Function to get shared project for a user, using shared_projects.json from user to establish nice filter to projects table ids-Dominic Minnich
def get_shared_projects(user_id):
    user = User.query.get(user_id)
    if not user or not user.shared_projects:
        return jsonify({"error": "User not found or no shared projects available"}), 404

    try:
        project_ids = [
            project["project_id"] for project in json.loads(user.shared_projects)
        ]
        projects = Project.query.filter(Project.id.in_(project_ids)).all()
        project_data = [
            {
                "id": project.id,
                "link": project.link,
                "tasks": project.tasks,
                "collaborators": project.collaborators,
            }
            for project in projects
        ]
        return jsonify(project_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_project_by_id(project_id):
    # Needs adjusting...
    return {
        "id": project_id,
        "title": "Sample Project",
        "description": "This is a sample project description.",
    }


# Routes
# /
@main.route("/")
@login_required
def home():
    user_projects_response = get_user_projects(current_user.id)
    if user_projects_response[1] == 200:
        projects = user_projects_response[0].json
    else:
        projects = []

    return render_template(
        "home.html",
        user=current_user,
        projects=projects,
        max_projects_per_user_unprivilaged=MAX_PROJECTS_PER_USER_UNPRIVILAGED,
        max_projects_per_user_privilaged=MAX_PROJECTS_PER_USER_PRILVILAGED,
        max_submissions_per_user_privilaged=MAX_SUBMISSIONS_PER_USER_PRIVILAGED,
        max_submissions_per_user_unprivilaged=MAX_SUBMISSIONS_PER_USER_UNPRIVILAGED,
    )


# /aboutUs route
@main.route("/aboutUs")
def aboutUs():
    return render_template("aboutUs.html")


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


@main.route("/editProject")
def editProject():
    project_id = request.args.get("id")
    if project_id:
        # Fetch project details using project_id
        project = get_project_by_id(
            project_id
        )  # Replace with your actual data fetching logic
        return render_template("editProject.html", project=project)
    else:
        return "Project ID not provided", 400


# @main.route("/ViewProjects")
# @login_required
# def ViewProjects():
# return render_template("ViewProjects.html", user=current_user)


@main.route("/viewProjects")
@login_required
def viewProjects():
    if current_user.projects:
        projects_list = json.loads(current_user.projects)
    else:
        projects_list = []

    project_ids = [project["project_id"] for project in projects_list]
    projects = Project.query.filter(Project.id.in_(project_ids)).all()
    return render_template("viewProjects.html", projects=projects)


# Configure logging KB
logging.basicConfig(level=logging.INFO)  # Can be deleted later, just for testing


@main.route("/createProject", methods=["GET", "POST"])
@login_required
def createProject():
    form = CreateProjectForm()
    if form.validate_on_submit():
        default_eol_time = datetime.utcnow() + timedelta(
            weeks=1
        )  # Set default end of life time to 1 week from now
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
            numPauses=0,
        )
        db.session.add(new_project)
        db.session.commit()

        # Add the created project ID to the 'projects' JSON under user table
        if current_user.projects:
            user_projects = json.loads(current_user.projects)
        else:
            user_projects = []

        user_projects.append({"project_id": new_project.id})
        current_user.projects = json.dumps(user_projects)
        db.session.commit()

        flash("Project created successfully!", "success")
        return redirect(url_for("main.viewProjects"))
    else:
        logging.warning("Form validation failed")  # Log when the form validation fails
        for field, errors in form.errors.items():
            for error in errors:
                logging.warning(
                    f"Validation error in {field}: {error}"
                )  # Log validation errors
    return render_template("CreateProject.html", form=form)


@main.route("/adminPanel", methods=["GET", "POST"])
@login_required
def adminPanel():
    if current_user.role != "admin":
        return redirect(url_for("main.home"))  # Only admins can access

    # Instantiate forms
    edit_account_form = EditAccountTypeForm()
    delete_user_form = DeleteUserForm()
    delete_project_form = DeleteProjectForm()

    # Process Edit Account Type form
    if edit_account_form.validate_on_submit() and edit_account_form.submit.data:
        username = edit_account_form.username.data
        role = (
            edit_account_form.role.data.lower()
        )  # This ensures that the role is lowercase.
        user = User.query.filter_by(username=username).first()
        if user:
            user.role = role
            db.session.commit()
            flash(f"User {username}'s role updated to {role}.", "success")
        else:
            flash("User not found.", "danger")

    # Process Delete User form
    elif delete_user_form.validate_on_submit() and delete_user_form.submit.data:
        username = delete_user_form.username.data
        user = User.query.filter_by(username=username).first()
        if user:
            db.session.delete(user)
            db.session.commit()
            flash(f"User {username} deleted successfully.", "success")
        else:
            flash("User not found.", "danger")

    # Process Delete Project form
    elif delete_project_form.validate_on_submit() and delete_project_form.submit.data:
        project_id = delete_project_form.project_id.data
        project = Project.query.filter_by(id=project_id).first()
        if project:
            db.session.delete(project)
            db.session.commit()
            flash(f"Project with ID {project_id} deleted successfully.", "success")
        else:
            flash("Project not found.", "danger")

    return render_template(
        "adminPanel.html",
        user=current_user,
        edit_account_form=edit_account_form,
        delete_user_form=delete_user_form,
        delete_project_form=delete_project_form,
    )


# /viewReviewSpecific
@main.route("/viewReviewSpecific")
@login_required
def viewReviewSpecific():
    return render_template("viewReviewSpecific.html", user=current_user)
