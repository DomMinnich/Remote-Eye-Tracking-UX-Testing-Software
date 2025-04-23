# routes.py - Single file for all application routes

import os
import uuid
import json
import shutil
from datetime import datetime, timedelta
from io import BytesIO
import base64
import random
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

from flask_wtf import FlaskForm
import matplotlib

matplotlib.use("Agg")  # Use non-GUI backend for Matplotlib
import matplotlib.pyplot as plt
import numpy as np
import requests  # For Figma proxy only if kept

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify,
    current_app,
    Response,
    session,
)
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
    fresh_login_required,
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from itsdangerous import URLSafeTimedSerializer

from .models import db, mail, User, Project, Collaborator, Task, TaskTime, GazeData
from .forms import (
    LoginForm,
    RegistrationForm,
    CreateProjectForm,
    EditProjectForm,
    DeleteProjectForm,
    EditAccountTypeForm,
    DeleteUserForm,
    UpdateAccountForm,
    ChangePasswordForm,
    UploadProfilePicForm,
)  # AddTaskForm, AddCollaboratorForm removed for now

# Import Message for mail sending inside routes
from flask_mail import Message

# Define the single main blueprint
main_bp = Blueprint("main", __name__)

# === Helper Functions ===


def allowed_file(filename):
    """Checks if the filename has an allowed extension."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


def generate_reset_token(user_email, salt="password-reset-salt"):
    """Generates a timed token for password reset."""
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(user_email, salt=salt)


def verify_reset_token(token, salt="password-reset-salt", max_age=3600):
    """Verifies a timed token. Returns email on success, None on failure/expiration."""
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = serializer.loads(token, salt=salt, max_age=max_age)  # 1 hour expiration
        return email
    except Exception as e:
        current_app.logger.warning(f"Password reset token verification failed: {e}")
        return None


def send_email(subject, recipients, text_body, html_body=None):
    """Sends an email."""
    try:
        msg = Message(
            subject,
            sender=current_app.config["MAIL_DEFAULT_SENDER"],
            recipients=recipients,
        )
        msg.body = text_body
        msg.html = html_body
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(
            f"Failed to send email to {recipients}: {e}", exc_info=True
        )
        return False


def get_project_or_404(project_id):
    """Gets a project by ID or returns 404."""
    return Project.query.get_or_404(project_id)


def check_project_permission(
    project, required_roles=["creator", "co-owner", "editor", "viewer"]
):
    """Checks if the current user has permission for a project."""
    if not current_user.is_authenticated:
        return False
    if current_user.role == "admin":
        return True  # Admins can access everything
    collab = Collaborator.query.filter_by(
        user_id=current_user.id, project_id=project.id
    ).first()
    return collab and collab.role in required_roles


# === Core Routes ===


@main_bp.route("/")
@login_required
def home():
    # Fetch data using new relationships/properties
    owned_projects = current_user.owned_projects
    shared_projects_list = current_user.shared_with_me_projects

    # Pass necessary config/constants to template
    max_projects_config = (
        current_app.config["MAX_PROJECTS_PRIVILEGED"]
        if current_user.role in ["admin", "project_manager"]
        else current_app.config["MAX_PROJECTS_STUDENT"]
    )

    # Example calculation for dashboard (can be more complex)
    total_tasks = (
        db.session.query(db.func.count(Task.id))
        .join(Project)
        .join(Collaborator)
        .filter(
            Collaborator.user_id == current_user.id,
            Collaborator.role
            == "creator",  # Count tasks only in owned projects? Or all accessible?
        )
        .scalar()
        or 0
    )

    return render_template(
        "home.html",
        user=current_user,
        projects=owned_projects,  # Pass owned projects
        shared_projects=shared_projects_list,  # Pass shared projects
        max_projects_per_user_privilaged=current_app.config[
            "MAX_PROJECTS_PRIVILEGED"
        ],  # Pass config values
        max_projects_per_user_unprivilaged=current_app.config["MAX_PROJECTS_STUDENT"],
        max_projects_total=max_projects_config,  # Pass the calculated max for the user
        total_tasks=total_tasks,
        notifications=[],  # Placeholder for notifications
    )


@main_bp.route("/aboutUs")
def aboutUs():
    return render_template("aboutUs.html")


# === Authentication Routes ===


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = LoginForm()
    if form.validate_on_submit():
        # Case-insensitive username/email login allowed? Let's allow username only for now.
        user = User.query.filter(User.username.ilike(form.username.data)).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash(f"Welcome back, {user.first_name}!", "success")
            next_page = request.args.get("next")
            # Simple validation to prevent open redirect vulnerability
            if next_page and not next_page.startswith("/"):
                next_page = None
            return redirect(next_page or url_for("main.home"))
        else:
            flash("Invalid username or password. Please try again.", "danger")
    return render_template("login.html", form=form)


@main_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("main.login"))


@main_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user_email = User.query.filter(
            User.email.ilike(form.email.data)
        ).first()
        existing_user_username = User.query.filter(
            User.username.ilike(form.username.data)
        ).first()
        error = False
        if existing_user_email:
            flash("An account with that email address already exists.", "danger")
            error = True
        if existing_user_username:
            flash("That username is already taken. Please choose another.", "danger")
            error = True

        if not error:
            new_user = User(
                username=form.username.data,
                email=form.email.data.lower(),
                first_name=form.first_name.data.strip(),
                last_name=form.last_name.data.strip(),
                role="student",
            )
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            try:
                db.session.commit()
                flash("Registration successful! Please log in.", "success")
                return redirect(url_for("main.login"))
            except IntegrityError as e:
                db.session.rollback()
                current_app.logger.error(f"Registration IntegrityError: {e}")
                flash(
                    "An error occurred (username or email might already exist). Please try again.",
                    "danger",
                )
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Registration failed: {e}", exc_info=True)
                flash("An unexpected error occurred during registration.", "danger")

    # Flash WTForms validation errors if POST request failed validation
    if request.method == "POST":
        for field, errors in form.errors.items():
            for error in errors:
                # Make messages more user-friendly
                friendly_name = (
                    form[field].label.text
                    if form[field].label
                    else field.replace("_", " ").title()
                )
                flash(f"{friendly_name}: {error}", "danger")

    return render_template("register.html", form=form)


@main_bp.route("/forgot-password", methods=["GET", "POST"])
def forgotPassword():
    if request.method == "POST":
        email = request.form.get("email", "").lower()
        if not email:
            flash("Please enter your email address.", "warning")
            return redirect(url_for("main.forgotPassword"))

        user = User.query.filter(User.email == email).first()
        if user:
            token = generate_reset_token(user.email)
            reset_url = url_for(
                "main.reset_password_with_token", token=token, _external=True
            )
            subject = "Password Reset Request - EyeC.Design"
            # Consider using render_template for email bodies
            text_body = f"""Hi {user.first_name},

Someone requested a password reset for your EyeC.Design account.
If this was you, click the link below to set a new password:
{reset_url}

This link is valid for 1 hour.

If you didn't request this, you can safely ignore this email.

Thanks,
The EyeC.Design Team"""
            # html_body = render_template('email/password_reset.html', user=user, reset_url=reset_url) # Example

            if send_email(subject, [user.email], text_body):  # , html_body):
                flash(
                    "Password reset instructions have been sent to your email.", "info"
                )
            else:
                flash(
                    "There was an issue sending the reset email. Please try again later.",
                    "danger",
                )
            # Redirect to login even if email fails, to avoid confirming email existence
            return redirect(url_for("main.login"))
        else:
            # Don't reveal if email exists - show the same message
            flash(
                "If an account with that email exists, reset instructions have been sent.",
                "info",
            )
            return redirect(url_for("main.login"))

    return render_template("ForgotPassword.html")


@main_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password_with_token(token):
    email = verify_reset_token(token)
    if not email:
        flash("The password reset link is invalid or has expired.", "danger")
        return redirect(url_for("main.forgotPassword"))

    user = User.query.filter(User.email == email).first()
    if not user:
        # Should not happen if token verified, but check anyway
        flash("User not found. Please try the forgot password process again.", "danger")
        return redirect(url_for("main.login"))

    if request.method == "POST":
        new_password = request.form.get("password")
        # Add server-side length validation
        if not new_password or len(new_password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("reset_password.html", token=token)  # Re-render form

        user.set_password(new_password)
        try:
            db.session.commit()
            flash(
                "Your password has been reset successfully. Please log in.", "success"
            )
            return redirect(url_for("main.login"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Error resetting password for {user.email}: {e}", exc_info=True
            )
            flash(
                "An error occurred while resetting your password. Please try again.",
                "danger",
            )

    # GET request: show the form
    return render_template("reset_password.html", token=token)


# === User Routes ===


@main_bp.route("/profile")
@login_required
def profile():
    # Pass calibration status to template
    return render_template("profile.html", user=current_user)


@main_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    account_form = UpdateAccountForm(obj=current_user)  # Pre-populate form
    password_form = ChangePasswordForm()

    # <<< FIX 3: Check which button was pressed >>>
    if "update_account" in request.form:
        if account_form.validate_on_submit():
            # Check if username or email is being changed to one that already exists
            username_taken = User.query.filter(
                User.username.ilike(account_form.username.data),
                User.id != current_user.id,
            ).first()
            email_taken = User.query.filter(
                User.email.ilike(account_form.email.data), User.id != current_user.id
            ).first()
            error = False
            if username_taken:
                account_form.username.errors.append(
                    "That username is already taken."
                )  # Attach error to form field
                error = True
            if email_taken:
                account_form.email.errors.append(
                    "That email address is already in use."
                )  # Attach error to form field
                error = True

            if not error:
                current_user.username = account_form.username.data
                current_user.email = account_form.email.data.lower()
                current_user.first_name = account_form.first_name.data.strip()
                current_user.last_name = account_form.last_name.data.strip()
                current_user.email_opt_in = account_form.email_opt_in.data
                try:
                    db.session.commit()
                    flash("Account details updated successfully!", "success")
                    return redirect(
                        url_for("main.settings")
                    )  # Redirect to refresh page
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(
                        f"Error updating settings for {current_user.username}: {e}",
                        exc_info=True,
                    )
                    flash("An error occurred while updating account details.", "danger")
        else:
            # Flash WTForms validation errors specifically for the account form
            for field, errors in account_form.errors.items():
                for error in errors:
                    friendly_name = (
                        account_form[field].label.text
                        if account_form[field].label
                        else field.replace("_", " ").title()
                    )
                    flash(f"{friendly_name}: {error}", "danger")

    elif "change_password" in request.form:
        if password_form.validate_on_submit():
            if current_user.check_password(password_form.old_password.data):
                current_user.set_password(password_form.new_password.data)
                try:
                    db.session.commit()
                    flash("Password changed successfully!", "success")
                    # Consider logging out user here for security
                    return redirect(url_for("main.settings"))
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(
                        f"Error changing password for {current_user.username}: {e}",
                        exc_info=True,
                    )
                    flash("An error occurred while changing your password.", "danger")
            else:
                password_form.old_password.errors.append(
                    "Incorrect current password."
                )  # Attach error to form field
                flash(
                    "Incorrect current password.", "danger"
                )  # Also flash for visibility
        else:
            # Flash WTForms validation errors specifically for the password form
            for field, errors in password_form.errors.items():
                for error in errors:
                    friendly_name = (
                        password_form[field].label.text
                        if password_form[field].label
                        else field.replace("_", " ").title()
                    )
                    flash(f"{friendly_name}: {error}", "danger")

    # Render the template with both forms
    return render_template(
        "settings.html",
        user=current_user,
        account_form=account_form,
        password_form=password_form,
    )
    account_form = UpdateAccountForm(obj=current_user)  # Pre-populate form
    password_form = ChangePasswordForm()

    # Check which button was pressed using the 'name' attribute we will add in the template
    if "update_account" in request.form and account_form.validate_on_submit():
        # Check if username or email is being changed to one that already exists
        username_taken = User.query.filter(
            User.username.ilike(account_form.username.data), User.id != current_user.id
        ).first()
        email_taken = User.query.filter(
            User.email.ilike(account_form.email.data), User.id != current_user.id
        ).first()
        error = False
        if username_taken:
            flash("That username is already taken.", "danger")
            error = True
        if email_taken:
            flash("That email address is already in use.", "danger")
            error = True

        if not error:
            current_user.username = account_form.username.data
            current_user.email = account_form.email.data.lower()
            current_user.first_name = account_form.first_name.data.strip()
            current_user.last_name = account_form.last_name.data.strip()
            current_user.email_opt_in = account_form.email_opt_in.data
            try:
                db.session.commit()
                flash("Account details updated successfully!", "success")
                return redirect(url_for("main.settings"))  # Redirect to refresh page
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(
                    f"Error updating settings for {current_user.username}: {e}",
                    exc_info=True,
                )
                flash("An error occurred while updating account details.", "danger")

    elif "change_password" in request.form and password_form.validate_on_submit():
        if current_user.check_password(password_form.old_password.data):
            current_user.set_password(password_form.new_password.data)
            try:
                db.session.commit()
                flash("Password changed successfully!", "success")
                # Log user out after password change for security? Optional.
                # logout_user()
                # flash("Please log in again with your new password.", "info")
                # return redirect(url_for('main.login'))
                return redirect(url_for("main.settings"))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(
                    f"Error changing password for {current_user.username}: {e}",
                    exc_info=True,
                )
                flash("An error occurred while changing your password.", "danger")
        else:
            flash("Incorrect current password.", "danger")

    # Flash validation errors if forms didn't validate
    if request.method == "POST":
        active_form = (
            account_form if "update_account" in request.form else password_form
        )
        # Only flash errors for the submitted form
        if ("update_account" in request.form and not account_form.validate()) or (
            "change_password" in request.form and not password_form.validate()
        ):
            for field, errors in active_form.errors.items():
                for error in errors:
                    friendly_name = (
                        active_form[field].label.text
                        if active_form[field].label
                        else field.replace("_", " ").title()
                    )
                    flash(f"{friendly_name}: {error}", "danger")

    return render_template(
        "settings.html",
        user=current_user,
        account_form=account_form,
        password_form=password_form,
    )


@main_bp.route("/upload_profile_picture", methods=["POST"])
@login_required
def upload_profile_picture():
    # Simple manual file handling (consider Flask-Uploads for more features)
    if "profile_picture" not in request.files:
        flash("No file part in the request.", "warning")
        return redirect(url_for("main.profile"))
    file = request.files["profile_picture"]
    if file.filename == "":
        flash("No file selected.", "warning")
        return redirect(url_for("main.profile"))

    if file and allowed_file(file.filename):
        # Create a secure, unique filename (e.g., using user ID and extension)
        _, f_ext = os.path.splitext(file.filename)
        # Ensure only allowed extensions (case-insensitive)
        allowed_ext_set = {
            "." + ext for ext in current_app.config["ALLOWED_EXTENSIONS"]
        }
        if f_ext.lower() not in allowed_ext_set:
            flash(
                f'Invalid file type. Allowed: {", ".join(current_app.config["ALLOWED_EXTENSIONS"])}',
                "danger",
            )
            return redirect(url_for("main.profile"))

        # Use user ID for filename to prevent conflicts and overwrite old picture
        filename = f"{current_user.id}{f_ext.lower()}"
        upload_path = os.path.join(
            current_app.config["USER_PROFILE_UPLOAD_FOLDER"], filename
        )

        try:
            # Optional: Resize image before saving using Pillow (pip install Pillow)
            # from PIL import Image
            # img = Image.open(file.stream)
            # img.thumbnail((200, 200)) # Example resize to max 200x200
            # img.save(upload_path)
            # For now, just save directly:
            file.save(upload_path)

            # Update user model
            current_user.picture = filename
            db.session.commit()
            flash("Profile picture updated successfully!", "success")
        except Exception as e:
            current_app.logger.error(
                f"Failed to upload profile picture for user {current_user.id}: {e}",
                exc_info=True,
            )
            flash("An error occurred while uploading the picture.", "danger")
            # Optional: db.session.rollback() if commit failed during user update
    else:
        # This case is already handled by the extension check above, but keep as fallback
        flash(
            f'Invalid file type or file not allowed. Allowed: {", ".join(current_app.config["ALLOWED_EXTENSIONS"])}',
            "danger",
        )

    return redirect(url_for("main.profile"))


# === Project Routes ===


@main_bp.route("/projects/<uuid:project_id>/analysis")
@login_required
def project_analysis(project_id):
    project_id_str = str(project_id)
    project = get_project_or_404(project_id_str)

    # Authorization check
    if not check_project_permission(project):
        flash("You do not have permission to view this project's analysis.", "danger")
        return redirect(url_for("main.home"))

    # --- Fetch Data ---
    task_times_query = (
        TaskTime.query.filter_by(project_id=project_id_str)
        .order_by(TaskTime.timestamp)
        .all()
    )
    gaze_data_query = (
        GazeData.query.join(TaskTime)
        .filter(
            TaskTime.project_id == project_id_str,
            GazeData.x.isnot(None),
            GazeData.y.isnot(None),
        )
        .all()
    )

    if not task_times_query:
        flash("No submission data found for analysis.", "info")
        return render_template(
            "analysis.html", project=project, plots={}, analysis_results={}, sessions=[]
        )

    # --- Process Data with Pandas ---
    task_times_data = [
        {
            "session_id": tt.session_id,
            "task_name": tt.task_name,
            "time_spent": tt.time_spent,
            "is_benchmark": tt.is_benchmark,
            "user_id": tt.user_id,
            "timestamp": tt.timestamp,
            "task_time_id": tt.id,  
        }
        for tt in task_times_query
    ]
    df_times = pd.DataFrame(task_times_data)

    gaze_data = [
        {
            "x": gd.x,
            "y": gd.y,
            "timestamp_ms": gd.timestamp_ms,
            "task_time_id": gd.task_time_id,
  
        }
        for gd in gaze_data_query
    ]
    df_gaze = pd.DataFrame(gaze_data)

    # Find TaskTime details associated with gaze points
    # Note: Ensure task_time_id in df_gaze correctly links to df_times
    gaze_task_details = df_times[
        ["task_time_id", "session_id", "is_benchmark"]
    ].drop_duplicates()
    if not df_gaze.empty and not gaze_task_details.empty:
        df_gaze = pd.merge(df_gaze, gaze_task_details, on="task_time_id", how="left")

    # Separate benchmark and submissions
    df_benchmark = df_times[df_times["is_benchmark"] == True]
    df_submissions = df_times[df_times["is_benchmark"] == False]

    # --- Generate Plots ---
    plots = {}

    # 1. Benchmark vs. Average Submission Time (Bar Chart)
    if not df_benchmark.empty and not df_submissions.empty:
        avg_submission_times = (
            df_submissions.groupby("task_name")["time_spent"].mean().reset_index()
        )
        avg_submission_times.rename(
            columns={"time_spent": "average_submission_time"}, inplace=True
        )

        comparison_df = pd.merge(
            df_benchmark[["task_name", "time_spent"]],
            avg_submission_times,
            on="task_name",
            how="outer",
        )
        comparison_df.rename(columns={"time_spent": "benchmark_time"}, inplace=True)
        comparison_df.fillna(
            0, inplace=True
        )  # Fill NA if a task exists in one but not the other

        fig_bar = px.bar(
            comparison_df,
            x="task_name",
            y=["benchmark_time", "average_submission_time"],
            title="Benchmark Time vs. Average Submission Time per Task",
            labels={
                "value": "Time (seconds)",
                "task_name": "Task",
                "variable": "Metric",
            },
            barmode="group",  # Group bars side-by-side
            template="plotly_white",
        )  # Use a clean template
        fig_bar.update_layout(yaxis_title="Time (seconds)")
        plots["benchmark_comparison"] = fig_bar.to_html(
            full_html=False, include_plotlyjs="cdn"
        )
    elif not df_benchmark.empty:
        fig_bar = px.bar(
            df_benchmark,
            x="task_name",
            y="time_spent",
            title="Benchmark Time per Task",
            labels={"time_spent": "Time (seconds)", "task_name": "Task"},
            template="plotly_white",
        )
        fig_bar.update_layout(yaxis_title="Time (seconds)")
        plots["benchmark_only"] = fig_bar.to_html(
            full_html=False, include_plotlyjs="cdn"
        )
    elif not df_submissions.empty:
        avg_submission_times = (
            df_submissions.groupby("task_name")["time_spent"].mean().reset_index()
        )
        fig_bar = px.bar(
            avg_submission_times,
            x="task_name",
            y="time_spent",
            title="Average Submission Time per Task",
            labels={"time_spent": "Time (seconds)", "task_name": "Task"},
            template="plotly_white",
        )
        fig_bar.update_layout(yaxis_title="Time (seconds)")
        plots["average_only"] = fig_bar.to_html(full_html=False, include_plotlyjs="cdn")

    # 2. Distribution of Submission Times (Box Plot)
    if not df_submissions.empty:
        fig_box = px.box(
            df_submissions,
            x="task_name",
            y="time_spent",
            title="Distribution of Submission Times per Task",
            labels={"time_spent": "Time (seconds)", "task_name": "Task"},
            points="all",  # Show individual points
            template="plotly_white",
            hover_data=["session_id"],
        )  # Show session ID on hover
        plots["time_distribution"] = fig_box.to_html(
            full_html=False, include_plotlyjs="cdn"
        )

    # 3. All Submission Times (Table or Scatter) - Let's prepare data for a table
    submission_summary = {}
    if not df_submissions.empty:
        # Pivot table for easy display
        try:
            submission_pivot = df_submissions.pivot_table(
                index="session_id", columns="task_name", values="time_spent"
            )
            submission_summary = submission_pivot.round(2).to_dict(
                "index"
            )  # Convert to dict for easier template iteration
        except Exception as e:
            current_app.logger.error(f"Error creating submission pivot table: {e}")
            # Fallback: simple list grouped by session
            submission_summary = (
                df_submissions.groupby("session_id")
                .apply(
                    lambda x: x[["task_name", "time_spent"]].round(2).to_dict("records")
                )
                .to_dict()
            )

    # 4. Aggregate Heatmap (All Submissions) - Using Plotly
    if not df_gaze.empty:
        df_gaze_submissions = df_gaze[df_gaze["is_benchmark"] == False]
        if not df_gaze_submissions.empty:
            # Determine sensible ranges, handle potential outliers affecting range
            q_low = df_gaze_submissions["x"].quantile(0.01)
            q_hi = df_gaze_submissions["x"].quantile(0.99)
            x_range = [max(0, q_low), q_hi]  # Assuming screen coordinates start at 0

            q_low = df_gaze_submissions["y"].quantile(0.01)
            q_hi = df_gaze_submissions["y"].quantile(0.99)
            y_range = [max(0, q_low), q_hi]

            # Check for valid ranges
            if x_range[1] <= x_range[0]:
                x_range = [0, 1920]  # Fallback X
            if y_range[1] <= y_range[0]:
                y_range = [0, 1080]  # Fallback Y

            fig_heatmap = px.density_heatmap(
                df_gaze_submissions,
                x="x",
                y="y",
                nbinsx=50,
                nbinsy=(
                    int(50 * (y_range[1] - y_range[0]) / (x_range[1] - x_range[0]))
                    if x_range[1] > x_range[0]
                    else 30
                ),  # Adjust bins based on aspect ratio
                range_x=x_range,
                range_y=y_range,
                title="Aggregate Gaze Heatmap (All Submissions)",
                color_continuous_scale="inferno",  # Or 'hot', 'viridis' etc.
                template="plotly_white",
            )

            fig_heatmap.update_layout(
                xaxis_title="Screen X",
                yaxis_title="Screen Y",
                coloraxis_colorbar=dict(title="Density"),
            )
            plots["aggregate_heatmap"] = fig_heatmap.to_html(
                full_html=False, include_plotlyjs="cdn"
            )

    # --- Outlier Detection (Simple IQR method) ---
    outliers = []
    if not df_submissions.empty:
        for task_name, group in df_submissions.groupby("task_name"):
            q1 = group["time_spent"].quantile(0.25)
            q3 = group["time_spent"].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            task_outliers = group[
                (group["time_spent"] < lower_bound)
                | (group["time_spent"] > upper_bound)
            ]
            for index, row in task_outliers.iterrows():
                outliers.append(
                    {
                        "session_id": row["session_id"],
                        "task_name": task_name,
                        "time_spent": round(row["time_spent"], 2),
                        "user_id": row[
                            "user_id"
                        ],  # Optional: add user info if available
                    }
                )

    # --- Prepare analysis results ---
    analysis_results = {
        "total_submissions": df_submissions["session_id"].nunique(),
        "has_benchmark": not df_benchmark.empty,
        "outliers": outliers,
        "submission_summary": submission_summary,  # Data for the table
    }

    # List of unique session IDs (excluding benchmark) for linking to individual heatmaps
    sessions = df_submissions["session_id"].unique().tolist()

    return render_template(
        "analysis.html",
        project=project,
        plots=plots,
        analysis_results=analysis_results,
        sessions=sessions,
    )


@main_bp.route("/generate_heatmap/<uuid:project_id>/<string:session_id>")
@login_required
def generate_session_heatmap(project_id, session_id):
    project_id_str = str(project_id)
    project = get_project_or_404(project_id_str)

    # Authorization
    if not check_project_permission(project):
        flash("You do not have permission to view this project's heatmap.", "danger")
        return redirect(url_for("main.home"))

    # Fetch TaskTime ID(s) for this specific session_id
    task_time_entries = TaskTime.query.filter_by(
        project_id=project_id_str, session_id=session_id
    ).all()
    if not task_time_entries:
        flash(f"No data found for session {session_id}.", "warning")
        # Redirect back or show an error page? Redirecting for now.
        return redirect(
            request.referrer or url_for("main.project_analysis", project_id=project_id)
        )

    task_time_ids = [tt.id for tt in task_time_entries]
    is_benchmark_session = any(tt.is_benchmark for tt in task_time_entries)
    session_label = (
        "Benchmark" if is_benchmark_session else f"Session {session_id[:8]}..."
    )

    # Fetch GazeData points for these TaskTime IDs
    gaze_points = GazeData.query.filter(
        GazeData.task_time_id.in_(task_time_ids),
        GazeData.x.isnot(None),
        GazeData.y.isnot(None),
    ).all()

    if not gaze_points:
        flash(f"No gaze data points found for {session_label}.", "info")
        return redirect(
            request.referrer or url_for("main.project_analysis", project_id=project_id)
        )

    # --- Generate Heatmap using Plotly ---
    df_gaze_session = pd.DataFrame([{"x": p.x, "y": p.y} for p in gaze_points])

    try:
        # Determine sensible ranges
        q_low_x = df_gaze_session["x"].quantile(0.01)
        q_hi_x = df_gaze_session["x"].quantile(0.99)
        x_range = [max(0, q_low_x), q_hi_x]

        q_low_y = df_gaze_session["y"].quantile(0.01)
        q_hi_y = df_gaze_session["y"].quantile(0.99)
        y_range = [max(0, q_low_y), q_hi_y]

        if x_range[1] <= x_range[0]:
            x_range = [0, 1920]  # Fallback X
        if y_range[1] <= y_range[0]:
            y_range = [0, 1080]  # Fallback Y

        fig_heatmap = px.density_heatmap(
            df_gaze_session,
            x="x",
            y="y",
            nbinsx=50,
            nbinsy=(
                int(50 * (y_range[1] - y_range[0]) / (x_range[1] - x_range[0]))
                if x_range[1] > x_range[0]
                else 30
            ),
            range_x=x_range,
            range_y=y_range,
            title=f"Gaze Heatmap for {session_label}",
            color_continuous_scale="inferno",
            template="plotly_white",
        )
    
        fig_heatmap.update_layout(
            xaxis_title="Screen X",
            yaxis_title="Screen Y",
            coloraxis_colorbar=dict(title="Density"),
        )

        # Render heatmap directly in a simple template or return image? Let's use a template.
        heatmap_html = fig_heatmap.to_html(
            full_html=True, include_plotlyjs="cdn"
        )  # Full HTML for standalone display
        # Or return an image response like the original /generate_heatmap
        # For simplicity returning full HTML page now.

        # Could create a simple heatmap_display.html template
        # return render_template("heatmap_display.html", heatmap_html=heatmap_html)
        return Response(heatmap_html, mimetype="text/html")

    except Exception as e:
        current_app.logger.error(
            f"Error generating session heatmap for project {project_id_str}, session {session_id}: {e}",
            exc_info=True,
        )
        flash("Could not generate heatmap due to an error.", "danger")
        return redirect(
            request.referrer or url_for("main.project_analysis", project_id=project_id)
        )


@main_bp.route("/projects/create", methods=["GET", "POST"])
@login_required
def createProject():
    form = CreateProjectForm()
    # Check project limit
    owned_count = Collaborator.query.filter_by(
        user_id=current_user.id, role="creator"
    ).count()
    max_projects = (
        current_app.config["MAX_PROJECTS_PRIVILEGED"]
        if current_user.role in ["admin", "project_manager"]
        else current_app.config["MAX_PROJECTS_STUDENT"]
    )
    if owned_count >= max_projects:
        flash(
            f"You have reached your project limit ({max_projects}). You own {owned_count} projects.",
            "warning",
        )
        return redirect(url_for("main.viewProjects"))  # Redirect if limit reached

    if form.validate_on_submit():
        # Check if link already exists
        existing_project = Project.query.filter(Project.link == form.link.data).first()
        if existing_project:
            flash("A project with this Figma link already exists.", "danger")
            return render_template("CreateProject.html", form=form, user=current_user)

        # Determine EoL and max submissions
        is_privileged_user = current_user.role in ["project_manager", "admin"]
        eol_delta = (
            current_app.config["EOL_DAYS_PRIVILEGED"]
            if is_privileged_user
            else current_app.config["EOL_DAYS_STUDENT"]
        )
        eol_time = datetime.utcnow() + eol_delta
        max_subs = current_app.config["MAX_SUBMISSIONS_DEFAULT"]

        # Create the project object
        new_project = Project(
            name=form.name.data or "Untitled Project",
            link=form.link.data,
            eol_time=eol_time,
            max_submissions=max_subs,
            # benchmarked default is False
        )
        db.session.add(new_project)  # Add project to session first

        # Add the creator as the first collaborator
        creator_collab = Collaborator(
            user=current_user, project=new_project, role="creator"
        )
        db.session.add(creator_collab)

        # <<< REVISED TASK PROCESSING START >>>
        tasks_json_string = request.form.get("major_tasks_hidden", "[]")
        tasks_added_count = 0
        minor_tasks_added_count = 0  # Track minor tasks
        tasks_data_valid = True  # Flag to track validity

        try:
            major_tasks_data = json.loads(tasks_json_string)
            if not isinstance(major_tasks_data, list):
                current_app.logger.warning(
                    f"Invalid structure for major_tasks_hidden (not a list) for user {current_user.id}: {tasks_json_string}"
                )
                flash(
                    "Warning: Could not process tasks due to invalid data structure.",
                    "warning",
                )
                tasks_data_valid = False
            elif not major_tasks_data:
                current_app.logger.info(
                    f"No tasks provided for new project by user {current_user.id}"
                )
                # No error, just no tasks added
            else:
                major_task_objects = (
                    []
                )  # Keep track of major tasks created in this session

                # --- First Pass: Create Major Tasks ---
                for index, task_data in enumerate(major_tasks_data):
                    if isinstance(task_data, dict) and task_data.get("name"):
                        major_task_name = task_data["name"].strip()
                        if not major_task_name:
                            current_app.logger.warning(
                                f"Skipping major task with empty name at index {index} for user {current_user.id}"
                            )
                            continue

                        # Create the major task (parent_id is None by default)
                        new_major_task = Task(
                            project=new_project,  # Link to project
                            name=major_task_name,
                            order=index,  # Use list index for major task order
                        )
                        db.session.add(new_major_task)
                        tasks_added_count += 1
                        # Store the newly created SQLAlchemy object and its raw minor task list for the next pass
                        major_task_objects.append(
                            (new_major_task, task_data.get("minor_tasks", []))
                        )
                    else:
                        # Log invalid task item structure
                        current_app.logger.warning(
                            f"Invalid major task item structure at index {index} for user {current_user.id}: {task_data}"
                        )
                        flash(
                            f"Warning: Invalid task data format for major task {index + 1}. Skipping.",
                            "warning",
                        )
                        # Decide if this should be a hard error? For now, just warn and skip.
                        # tasks_data_valid = False # Optionally make it an error

                # --- Flush to get IDs for Major Tasks ---
                # This assigns IDs without committing the transaction yet, crucial for setting parent_id
                if tasks_added_count > 0:
                    try:
                        current_app.logger.info(
                            f"Flushing session to get IDs for {tasks_added_count} major tasks before adding minors."
                        )
                        db.session.flush()
                        current_app.logger.info(f"Flush successful.")
                    except Exception as e:
                        # If flush fails, something is fundamentally wrong, rollback and report
                        db.session.rollback()
                        current_app.logger.error(
                            f"CRITICAL: Error flushing session during task creation for user {current_user.id}: {e}",
                            exc_info=True,
                        )
                        flash(
                            "A critical error occurred while preparing tasks. Project not created.",
                            "danger",
                        )
                        # Re-render form
                        return render_template(
                            "CreateProject.html", form=form, user=current_user
                        )

                # --- Second Pass: Create Minor Tasks ---
                current_app.logger.info(
                    f"Processing minor tasks for {len(major_task_objects)} major tasks..."
                )
                for major_task_obj, minor_tasks_list in major_task_objects:
                    if not major_task_obj.id:
                        # This really shouldn't happen after a successful flush, but safety first
                        current_app.logger.error(
                            f"FATAL: Major task '{major_task_obj.name}' missing ID after flush. Cannot add minor tasks. Rolling back."
                        )
                        tasks_data_valid = False  # Treat this as a failure
                        break  # Stop processing further tasks

                    current_app.logger.debug(
                        f"Processing minors for Major Task ID: {major_task_obj.id}, Name: '{major_task_obj.name}'"
                    )
                    if isinstance(minor_tasks_list, list):
                        for minor_index, minor_task_name_raw in enumerate(
                            minor_tasks_list
                        ):
                            # Ensure minor_task_name is a string and cleanup
                            minor_task_name = str(minor_task_name_raw).strip()
                            if not minor_task_name:
                                current_app.logger.warning(
                                    f"Skipping empty minor task name for major task ID {major_task_obj.id} at index {minor_index}"
                                )
                                continue

                            new_minor_task = Task(
                                project_id=new_project.id,  # Also link directly to project
                                name=minor_task_name,
                                order=minor_index,  # Order of minor tasks within the major task
                                parent_id=major_task_obj.id,  # <<< LINK TO PARENT MAJOR TASK >>>
                            )
                            db.session.add(new_minor_task)
                            minor_tasks_added_count += 1
                            current_app.logger.debug(
                                f"  Added minor task: '{minor_task_name}' (Order: {minor_index}) linked to Parent ID {major_task_obj.id}"
                            )
                    elif (
                        minor_tasks_list
                    ):  # Log if minor_tasks exists but is not a list
                        current_app.logger.warning(
                            f"Minor tasks data for major task ID {major_task_obj.id} is not a list: {type(minor_tasks_list)}. Skipping minors."
                        )

                if not tasks_data_valid:  # Check flag again after minor task processing
                    db.session.rollback()
                    flash(
                        "Project not created due to critical errors during task processing.",
                        "danger",
                    )
                    return render_template(
                        "CreateProject.html", form=form, user=current_user
                    )

        except json.JSONDecodeError:
            current_app.logger.error(
                f"Failed to decode tasks JSON for user {current_user.id}: {tasks_json_string}"
            )
            flash(
                "Error: Failed to parse task data. Please check the format.", "danger"
            )
            tasks_data_valid = False  # Treat parse error as failure
        except Exception as e:
            db.session.rollback()  # Rollback immediately on unexpected task processing error
            current_app.logger.error(
                f"Unexpected error processing tasks during project creation for user {current_user.id}: {e}",
                exc_info=True,
            )
            flash("An unexpected error occurred while processing tasks.", "danger")
            # Re-render the form with errors
            return render_template("CreateProject.html", form=form, user=current_user)

        # If task data was fundamentally invalid (decode/structure error or flush error), prevent commit
        if not tasks_data_valid:
            db.session.rollback()  # Ensure rollback if flag is false
            flash(
                "Project not created due to errors in task data processing.", "danger"
            )
            # Re-render form, potentially preserving submitted task JSON if possible
            return render_template("CreateProject.html", form=form, user=current_user)

        # <<< REVISED TASK PROCESSING END >>>

        # --- Process Collaborators (Only if user has permission) ---
        collaborators_json_string = request.form.get("collaborators_hidden", "[]")
        collaborators_added_count = 0
        collaborator_errors = []
        if current_user.role in ["admin", "project_manager"]:
            try:
                collaborators_data = json.loads(collaborators_json_string)
                if isinstance(collaborators_data, list):
                    processed_emails = {
                        current_user.email.lower()
                    }  # Creator already added
                    for collab_data in collaborators_data:
                        if (
                            isinstance(collab_data, dict)
                            and collab_data.get("email")
                            and collab_data.get("role")
                        ):
                            email = collab_data["email"].lower().strip()
                            role = collab_data["role"].lower()  # Ensure lowercase role
                            valid_roles = ["viewer", "editor", "co-owner"]
                            if role not in valid_roles:
                                msg = f"Skipping collaborator '{email}' with invalid role '{role}'. Valid roles: {valid_roles}"
                                current_app.logger.warning(msg)
                                collaborator_errors.append(
                                    f"Invalid role '{role}' for {email}."
                                )
                                continue
                            if not email:  # Skip empty emails
                                continue
                            if email in processed_emails:
                                msg = f"Skipping duplicate collaborator email '{email}'"
                                current_app.logger.warning(msg)
                                continue

                            user_to_add = User.query.filter(User.email == email).first()
                            if user_to_add:
                                # Check if this user is already the creator
                                if user_to_add.id == current_user.id:
                                    current_app.logger.warning(
                                        f"Attempted to re-add creator ({email}) as collaborator. Skipping."
                                    )
                                    continue

                                new_collaborator = Collaborator(
                                    user=user_to_add, project=new_project, role=role
                                )
                                db.session.add(new_collaborator)
                                processed_emails.add(email)
                                collaborators_added_count += 1
                            else:
                                msg = f"Could not find user with email '{email}'. Collaborator not added."
                                current_app.logger.warning(msg)
                                collaborator_errors.append(f"User not found: {email}.")
                        else:
                            current_app.logger.warning(
                                f"Invalid collaborator item structure: {collab_data}"
                            )
                            collaborator_errors.append(
                                "Invalid collaborator data format found."
                            )
                else:
                    current_app.logger.warning(
                        f"Invalid structure for collaborators_hidden (not a list) for user {current_user.id}: {collaborators_json_string}"
                    )
                    collaborator_errors.append(
                        "Could not process collaborators due to invalid data structure."
                    )

            except json.JSONDecodeError:
                current_app.logger.error(
                    f"Failed to decode collaborators JSON for user {current_user.id}: {collaborators_json_string}"
                )
                collaborator_errors.append("Failed to parse collaborator data.")
            except Exception as e:
                # Don't rollback here, but log and report error. Project/tasks might still commit.
                current_app.logger.error(
                    f"Unexpected error processing collaborators during project creation for user {current_user.id}: {e}",
                    exc_info=True,
                )
                collaborator_errors.append(
                    "An unexpected error occurred while processing collaborators."
                )
        else:
            current_app.logger.info(
                f"User {current_user.id} (role: {current_user.role}) does not have permission to add collaborators during project creation."
            )

        # --- Attempt to commit all changes (Project, Creator, Tasks, Collaborators) ---
        try:
            db.session.commit()
            current_app.logger.info(
                f"Project '{new_project.id}' ({new_project.name}) created by user {current_user.id} with {tasks_added_count} major tasks, {minor_tasks_added_count} minor tasks, and {collaborators_added_count} additional collaborators."
            )

            # Build success message
            success_message = f"Project '{new_project.name}' created successfully!"
            task_summary = []
            if tasks_added_count > 0:
                task_summary.append(
                    f"{tasks_added_count} major task{'s' if tasks_added_count != 1 else ''}"
                )
            if minor_tasks_added_count > 0:
                task_summary.append(
                    f"{minor_tasks_added_count} minor task{'s' if minor_tasks_added_count != 1 else ''}"
                )
            if task_summary:
                success_message += f" ({' and '.join(task_summary)} added)"
            if collaborators_added_count > 0:
                success_message += f" ({collaborators_added_count} collaborator{'s' if collaborators_added_count != 1 else ''} added)"
            flash(success_message, "success")

            # Flash collaborator warnings now if any occurred during processing
            for error in collaborator_errors:
                flash(f"Warning: {error}", "warning")

            # Redirect to the edit page for the newly created project
            return redirect(url_for("main.editProject", project_id=new_project.id))

        except (
            IntegrityError
        ) as ie:  # Catch potential duplicate link error if check failed race condition
            db.session.rollback()
            # Check if it's specifically a unique constraint violation on the link
            if "project.link" in str(ie.orig):
                flash(
                    "A project with this Figma link likely already exists (Integrity Error).",
                    "danger",
                )
            else:
                flash(
                    "A database integrity error occurred. Please check your inputs.",
                    "danger",
                )
            current_app.logger.warning(
                f"IntegrityError on project creation commit for link {form.link.data} by user {current_user.id}: {ie}"
            )
            # Re-render form with submitted data
            return render_template("CreateProject.html", form=form, user=current_user)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"CRITICAL: Error committing project creation for user {current_user.id}: {e}",
                exc_info=True,
            )
            flash(
                "An critical error occurred while saving the project. Please try again.",
                "danger",
            )
            # Re-render form with submitted data
            return render_template("CreateProject.html", form=form, user=current_user)

    # --- Handle GET request or form validation failure ---
    # Flash WTForms validation errors if POST request failed validation
    if request.method == "POST" and not form.validate():
        for field, errors in form.errors.items():
            for error in errors:
                friendly_name = (
                    form[field].label.text
                    if form[field].label
                    else field.replace("_", " ").title()
                )
                flash(f"{friendly_name}: {error}", "danger")

    return render_template("CreateProject.html", form=form, user=current_user)


@main_bp.route("/projects")
@login_required
def viewProjects():
    # Get projects where the current user is the creator
    projects_list = (
        Project.query.join(Collaborator)
        .filter(Collaborator.user_id == current_user.id, Collaborator.role == "creator")
        .order_by(Project.created_at.desc())
        .all()
    )

    # Manually count tasks and ensure tasks is a list
    for project in projects_list:
        project.task_count = project.tasks.count()  # Add a task_count attribute
        # Either force evaluate the query or add a list property
        project.tasks_list = (
            project.tasks.all()
        )  # Add a tasks_list attribute that's a proper list

    return render_template("ViewProjects.html", projects=projects_list)


@main_bp.route("/projects/shared")
@login_required
def viewSharedProjects():
    # Query for collaborations first
    collaborations = (
        Collaborator.query.join(Project, Collaborator.project_id == Project.id)
        .filter(Collaborator.user_id == current_user.id, Collaborator.role != "creator")
        .order_by(Project.created_at.desc())
        .options(
            db.joinedload(Collaborator.project)  # Just load the project, not its tasks
        )
        .all()
    )

    
    for collab in collaborations:
        # Add task_count as an attribute to each project
        collab.project.task_count = collab.project.tasks.count()
     
        collab.project.tasks_list = collab.project.tasks.all()

    # Then update the template to use project.task_count instead of project.tasks | length
    return render_template("viewSharedProjects.html", collaborations=collaborations)


@main_bp.route("/projects/<string:project_id>/edit", methods=["GET", "POST"])
@login_required
def editProject(project_id):
    project = get_project_or_404(project_id)

    # Authorization check
    if not current_user.can_edit_project(project.id):
        flash("You do not have permission to edit this project.", "danger")
        return redirect(url_for("main.viewProjects"))

    form = EditProjectForm()  # Instantiate for CSRF etc.

    if request.method == "POST":
        if form.validate_on_submit():  # Validates Name and Link from the form
            # Check for link conflict (existing logic seems ok)
            link_changed = project.link != form.link.data
            if link_changed:
                existing_project = Project.query.filter(
                    Project.link == form.link.data, Project.id != project.id
                ).first()
                if existing_project:
                    flash(
                        "Another project with this Figma link already exists.", "danger"
                    )
                    # Re-render: Fetch current DB state for JSON display
                    tasks_db = project.tasks.order_by(Task.order).all()
                    collabs_db = (
                        project.collaborators.join(User)
                        .options(db.joinedload(Collaborator.user))
                        .all()
                    )
                    tasks_json_db = json.dumps(
                        [
                            {"id": task.id, "name": task.name, "order": task.order}
                            for task in tasks_db
                        ],
                        indent=2,
                    )
                    collabs_json_db = json.dumps(
                        [
                            {
                                "id": collab.user_id,
                                "email": collab.user.email,
                                "role": collab.role,
                            }
                            for collab in collabs_db
                        ],
                        indent=2,
                    )
                    delete_form_render = (
                        DeleteProjectForm()
                    )  # Need form instance for render
                    delete_form_render.project_id.data = project_id
                    return render_template(
                        "EditProject.html",
                        form=form,
                        project=project,
                        tasks_json=request.form.get(
                            "tasks", tasks_json_db
                        ),  # Show submitted (potentially bad) JSON
                        collaborators_json=request.form.get(
                            "collaborators", collabs_json_db
                        ),
                        delete_form=delete_form_render,
                    )

            # Update basic project info
            project.name = form.name.data or "Untitled Project"
            project.link = form.link.data
            basic_info_changed = db.session.is_modified(project)

            # <<< FIX 2: REFINED JSON PROCESSING START >>>
            tasks_updated = False
            collabs_updated = False
            json_processing_error = False

            # Process Tasks JSON
            submitted_tasks_json = request.form.get("tasks")  # Get from textarea
            if submitted_tasks_json is not None:  # Only process if field was submitted
                try:
                    submitted_tasks_data = json.loads(submitted_tasks_json)
                    if not isinstance(submitted_tasks_data, list):
                        raise ValueError("Tasks data must be a list of objects.")

                    # Use eager loading to get tasks efficiently
                    current_tasks = {task.id: task for task in project.tasks}
                    submitted_task_ids = set()
                    new_task_order_map = {}  # Maps temp ID or real ID to desired order

                    # --- First Pass: Identify Adds, Updates, and track seen IDs/order ---
                    tasks_to_add = []
                    for index, task_data in enumerate(submitted_tasks_data):
                        if not isinstance(task_data, dict) or "name" not in task_data:
                            current_app.logger.warning(
                                f"EditProject: Skipping invalid task data item at index {index} for project {project_id}: {task_data}"
                            )
                            continue

                        task_id = task_data.get("id")
                        task_name = task_data["name"].strip()
                        # Use index as default order if not provided
                        task_order = task_data.get("order", index)

                        if not task_name:
                            current_app.logger.warning(
                                f"EditProject: Skipping task with empty name at index {index} for project {project_id}"
                            )
                            continue

                        # Map order using task_id if available, otherwise a temporary key
                        order_key = task_id if task_id else f"new_{index}"
                        new_task_order_map[order_key] = task_order

                        if task_id and task_id in current_tasks:
                            # Existing task: Check for updates
                            task = current_tasks[task_id]
                            submitted_task_ids.add(task_id)  # Mark as seen
                            if task.name != task_name:
                                task.name = task_name
                                db.session.add(task)  # Mark for update
                                tasks_updated = True
                            # Order will be handled in the second pass
                        elif (
                            task_id is None
                        ):  # Explicitly check for None ID for new tasks
                            # New task: Prepare for addition
                            # Assign temporary order from map, will be finalized later
                            new_task = Task(
                                project_id=project.id,
                                name=task_name,
                                order=new_task_order_map[order_key],
                            )
                            tasks_to_add.append(new_task)
                            tasks_updated = True
                        else:
                            # Task ID provided but not found in current tasks - treat as error or new?
                            # Let's treat as an error to prevent accidental data linking issues.
                            current_app.logger.warning(
                                f"EditProject: Task ID '{task_id}' submitted but not found in project {project_id}. Skipping."
                            )
                            flash(
                                f"Warning: Submitted task ID '{task_id}' (Name: '{task_name}') does not belong to this project. It was ignored.",
                                "warning",
                            )

                    # --- Second Pass: Determine Deletes ---
                    tasks_to_delete_ids = set(current_tasks.keys()) - submitted_task_ids
                    for task_id_to_delete in tasks_to_delete_ids:
                        db.session.delete(current_tasks[task_id_to_delete])
                        tasks_updated = True
                        current_app.logger.info(
                            f"EditProject: Marked task {task_id_to_delete} for deletion from project {project_id}"
                        )

                    # --- Third Pass: Add New Tasks and Finalize Order ---
                    if tasks_to_add:
                        for task in tasks_to_add:
                            db.session.add(task)
                        current_app.logger.info(
                            f"EditProject: Marked {len(tasks_to_add)} new tasks for addition to project {project_id}"
                        )

                    # If any task changes occurred (add, update, delete), we need to re-evaluate order
                    if tasks_updated:
                        db.session.flush()  # Assign IDs to new tasks, process deletions in memory
                        # Re-fetch all current tasks for the project (including newly added, excluding deleted)
                        final_tasks = project.tasks.all()
                        for task in final_tasks:
                            # Find the desired order from the map (new tasks won't have ID initially, but flush assigns one)
                            # Use the task.id which is now guaranteed to be set after flush
                            new_order = new_task_order_map.get(
                                task.id, task.order
                            )  # Default to existing order if somehow missing

                            # Check temporary key mapping for potentially just-added tasks if ID mapping fails
                            # This part is complex. A simpler way is to rely on the index as default if 'order' wasn't explicit.
                            # The current logic uses task.id which *should* work after flush.

                            if task.order != new_order:
                                task.order = new_order
                                db.session.add(task)  # Mark for order update
                                current_app.logger.debug(
                                    f"EditProject: Updating order for task {task.id} to {new_order}"
                                )

                except json.JSONDecodeError as e:
                    flash(
                        f"Error: Invalid JSON format for Tasks. Changes not saved. {e}",
                        "danger",
                    )
                    current_app.logger.error(
                        f"EditProject: JSON Decode Error for tasks in project {project_id}: {e}"
                    )
                    json_processing_error = True
                except ValueError as e:
                    flash(
                        f"Error processing Tasks data: {e}. Changes not saved.",
                        "danger",
                    )
                    current_app.logger.error(
                        f"EditProject: Value Error processing tasks for project {project_id}: {e}"
                    )
                    json_processing_error = True
                except Exception as e:
                    flash(
                        "An unexpected error occurred while updating tasks. Changes not saved.",
                        "danger",
                    )
                    current_app.logger.error(
                        f"EditProject: Unexpected error processing tasks for project {project_id}: {e}",
                        exc_info=True,
                    )
                    json_processing_error = True

            # Process Collaborators JSON (if user has permission)
            if not json_processing_error and current_user.can_manage_collaborators(
                project.id
            ):
                submitted_collabs_json = request.form.get(
                    "collaborators"
                )  # Get from textarea
                if submitted_collabs_json is not None:
                    try:
                        submitted_collabs_data = json.loads(submitted_collabs_json)
                        if not isinstance(submitted_collabs_data, list):
                            raise ValueError(
                                "Collaborators data must be a list of objects."
                            )

                        current_collaborators = {
                            collab.user_id: collab for collab in project.collaborators
                        }
                        submitted_collab_user_ids = set()
                        creator_id = project.creator.id if project.creator else None

                        for collab_data in submitted_collabs_data:
                            if (
                                not isinstance(collab_data, dict)
                                or "email" not in collab_data
                                or "role" not in collab_data
                            ):
                                current_app.logger.warning(
                                    f"EditProject: Skipping invalid collaborator data item for project {project_id}: {collab_data}"
                                )
                                continue

                            email = collab_data["email"].lower().strip()
                            role = collab_data[
                                "role"
                            ].lower()  # Ensure role is lower case
                            user_id_from_json = collab_data.get(
                                "id"
                            )  # Use ID if provided

                            # --- Find the user robustly ---
                            user_to_process = None
                            if user_id_from_json:
                                # If ID is provided, trust it but verify email matches for safety
                                user_by_id = User.query.get(user_id_from_json)
                                if user_by_id and user_by_id.email.lower() == email:
                                    user_to_process = user_by_id
                                elif user_by_id:
                                    # ID exists but email mismatch - dangerous, log and maybe error?
                                    current_app.logger.warning(
                                        f"EditProject: Collaborator ID {user_id_from_json} email mismatch ('{email}' vs DB '{user_by_id.email}'). Falling back to email lookup for project {project_id}."
                                    )
                                    user_to_process = User.query.filter(
                                        User.email == email
                                    ).first()
                                else:
                                    # ID provided but doesn't exist, try email lookup
                                    user_to_process = User.query.filter(
                                        User.email == email
                                    ).first()
                            else:
                                # No ID provided, look up by email
                                user_to_process = User.query.filter(
                                    User.email == email
                                ).first()

                            if not user_to_process:
                                flash(
                                    f"Warning: Collaborator with email '{email}' not found. Skipping.",
                                    "warning",
                                )
                                continue

                            user_id = user_to_process.id  # Get the definitive user ID

                            # Prevent modifying the creator directly
                            if user_id == creator_id:
                                submitted_collab_user_ids.add(
                                    user_id
                                )  # Mark creator as seen
                                if role != "creator":
                                    flash(
                                        f"Warning: Cannot change role of project creator ('{email}'). Role kept as 'creator'.",
                                        "warning",
                                    )
                                continue  # Skip further processing for creator

                            # Validate role
                            valid_roles = ["viewer", "editor", "co-owner"]
                            if role not in valid_roles:
                                flash(
                                    f"Warning: Invalid role '{role}' for collaborator '{email}'. Skipping.",
                                    "warning",
                                )
                                continue

                            # --- Process Existing or New Collaborator ---
                            if user_id in current_collaborators:
                                # Existing collaborator: Update role if changed
                                collab = current_collaborators[user_id]
                                if collab.role != role:
                                    collab.role = role
                                    db.session.add(collab)
                                    collabs_updated = True
                                    current_app.logger.info(
                                        f"EditProject: Updating role for user {user_id} to '{role}' in project {project_id}"
                                    )
                            else:
                                # New collaborator: Add them
                                new_collaborator = Collaborator(
                                    user_id=user_id, project_id=project.id, role=role
                                )
                                db.session.add(new_collaborator)
                                collabs_updated = True
                                current_app.logger.info(
                                    f"EditProject: Adding user {user_id} as '{role}' to project {project_id}"
                                )

                            submitted_collab_user_ids.add(user_id)  # Mark as seen

                        # --- Determine Collaborators to Remove ---
                        collabs_to_remove_ids = (
                            set(current_collaborators.keys())
                            - submitted_collab_user_ids
                        )
                        for user_id_to_remove in collabs_to_remove_ids:
                            # Double check we are not removing the creator
                            if user_id_to_remove != creator_id:
                                db.session.delete(
                                    current_collaborators[user_id_to_remove]
                                )
                                collabs_updated = True
                                current_app.logger.info(
                                    f"EditProject: Marked collaborator {user_id_to_remove} for removal from project {project_id}"
                                )

                    except json.JSONDecodeError as e:
                        flash(
                            f"Error: Invalid JSON format for Collaborators. Changes not saved. {e}",
                            "danger",
                        )
                        current_app.logger.error(
                            f"EditProject: JSON Decode Error for collabs in project {project_id}: {e}"
                        )
                        json_processing_error = True
                    except ValueError as e:
                        flash(
                            f"Error processing Collaborators data: {e}. Changes not saved.",
                            "danger",
                        )
                        current_app.logger.error(
                            f"EditProject: Value Error processing collabs for project {project_id}: {e}"
                        )
                        json_processing_error = True
                    except Exception as e:
                        flash(
                            "An unexpected error occurred while updating collaborators. Changes not saved.",
                            "danger",
                        )
                        current_app.logger.error(
                            f"EditProject: Unexpected error processing collabs for project {project_id}: {e}",
                            exc_info=True,
                        )
                        json_processing_error = True
            # <<< FIX 2: REFINED JSON PROCESSING END >>>

            if json_processing_error:
                db.session.rollback()  # Rollback ALL changes if JSON processing failed
                # Re-render form with errors, showing submitted JSON
                tasks_db = project.tasks.order_by(Task.order).all()
                collabs_db = (
                    project.collaborators.join(User)
                    .options(db.joinedload(Collaborator.user))
                    .all()
                )
                tasks_json_db = json.dumps(
                    [
                        {"id": task.id, "name": task.name, "order": task.order}
                        for task in tasks_db
                    ],
                    indent=2,
                )
                collabs_json_db = json.dumps(
                    [
                        {
                            "id": collab.user_id,
                            "email": collab.user.email,
                            "role": collab.role,
                        }
                        for collab in collabs_db
                    ],
                    indent=2,
                )
                delete_form_render = DeleteProjectForm()
                delete_form_render.project_id.data = project_id
                # Keep submitted form values for name/link
                form.name.data = request.form.get("name")
                form.link.data = request.form.get("link")
                return render_template(
                    "EditProject.html",
                    form=form,
                    project=project,
                    tasks_json=request.form.get(
                        "tasks", tasks_json_db
                    ),  # Show submitted JSON
                    collaborators_json=request.form.get(
                        "collaborators", collabs_json_db
                    ),
                    delete_form=delete_form_render,
                )
            else:
                # --- Attempt to commit changes ---
                if basic_info_changed or tasks_updated or collabs_updated:
                    try:
                        db.session.commit()
                        flash("Project updated successfully!", "success")
                        current_app.logger.info(
                            f"Project {project_id} updated successfully by user {current_user.id}."
                        )
                    except Exception as e:
                        db.session.rollback()
                        current_app.logger.error(
                            f"Error committing edits for project {project_id}: {e}",
                            exc_info=True,
                        )
                        flash(
                            "An error occurred while saving project changes.", "danger"
                        )
                        # Re-render form after commit error (rare, but possible) - show DB state JSON
                        tasks_db = project.tasks.order_by(Task.order).all()
                        collabs_db = (
                            project.collaborators.join(User)
                            .options(db.joinedload(Collaborator.user))
                            .all()
                        )
                        tasks_json_db = json.dumps(
                            [
                                {"id": task.id, "name": task.name, "order": task.order}
                                for task in tasks_db
                            ],
                            indent=2,
                        )
                        collabs_json_db = json.dumps(
                            [
                                {
                                    "id": collab.user_id,
                                    "email": collab.user.email,
                                    "role": collab.role,
                                }
                                for collab in collabs_db
                            ],
                            indent=2,
                        )
                        delete_form_render = DeleteProjectForm()
                        delete_form_render.project_id.data = project_id
                        form.name.data = request.form.get("name")
                        form.link.data = request.form.get("link")
                        return render_template(
                            "EditProject.html",
                            form=form,
                            project=project,
                            tasks_json=tasks_json_db,  # Show DB state JSON
                            collaborators_json=collabs_json_db,
                            delete_form=delete_form_render,
                        )
                else:
                    flash("No changes detected.", "info")

                # Redirect after successful update or no change
                return redirect(url_for("main.viewProjects"))

        else:
            # WTForms validation failed (name/link format etc.)
            current_app.logger.warning(
                f"EditProject form validation failed for project {project_id}: {form.errors}"
            )
            # Re-render form with validation errors, showing submitted JSON
            tasks_db = project.tasks.order_by(Task.order).all()
            collabs_db = (
                project.collaborators.join(User)
                .options(db.joinedload(Collaborator.user))
                .all()
            )
            tasks_json_db = json.dumps(
                [
                    {"id": task.id, "name": task.name, "order": task.order}
                    for task in tasks_db
                ],
                indent=2,
            )
            collabs_json_db = json.dumps(
                [
                    {
                        "id": collab.user_id,
                        "email": collab.user.email,
                        "role": collab.role,
                    }
                    for collab in collabs_db
                ],
                indent=2,
            )
            delete_form_render = DeleteProjectForm()
            delete_form_render.project_id.data = project_id
            # Form object itself retains submitted values for name/link
            return render_template(
                "EditProject.html",
                form=form,
                project=project,
                tasks_json=request.form.get(
                    "tasks", tasks_json_db
                ),  # Show submitted JSON
                collaborators_json=request.form.get("collaborators", collabs_json_db),
                delete_form=delete_form_render,
            )

    # --- GET Request ---
    # Pre-populate WTForm fields with existing data
    form.name.data = project.name
    form.link.data = project.link

    # Fetch tasks and collaborators for JSON display
    tasks = project.tasks.order_by(Task.order).all()
    collaborators = (
        project.collaborators.join(User).options(db.joinedload(Collaborator.user)).all()
    )

    # Convert to JSON for the textareas, ensuring IDs are present
    tasks_json = json.dumps(
        [{"id": task.id, "name": task.name, "order": task.order} for task in tasks],
        indent=2,  # Pretty print
    )
    collaborators_json = json.dumps(
        [
            {"id": collab.user_id, "email": collab.user.email, "role": collab.role}
            for collab in collaborators
        ],
        indent=2,  # Pretty print
    )

    # Create a proper DeleteProjectForm instance for the delete button
    delete_form = DeleteProjectForm()
    delete_form.project_id.data = project_id  # Pre-populate the project ID

    return render_template(
        "EditProject.html",
        form=form,
        project=project,
        tasks_json=tasks_json,
        collaborators_json=collaborators_json,
        delete_form=delete_form,
    )


@main_bp.route("/projects/<string:project_id>/delete", methods=["POST"])
@login_required
def delete_project(project_id):
    project = get_project_or_404(project_id)

    # Authorization check
    if not current_user.can_delete_project(project.id):
        flash("You do not have permission to delete this project.", "danger")
        # Redirect based on where delete was triggered (e.g., edit page or view page)
        return redirect(request.referrer or url_for("main.view_projects"))

    # Validate the DeleteProjectForm (specifically the confirm text)
    # The form needs to be instantiated and validated here if using confirm_text
    delete_form = DeleteProjectForm()  # Instantiate it
    if delete_form.validate_on_submit():  # This checks the confirmation text
        try:
            # Cascading deletes should handle associated Collaborators, Tasks, TaskTimes, GazeData
            project_name = project.name  # Get name before deleting
            db.session.delete(project)
            db.session.commit()

            # Delete associated static files (session folders)
            project_data_folder = os.path.join(
                current_app.config["UPLOAD_FOLDER"], secure_filename(project_id)
            )
            if os.path.exists(project_data_folder):
                try:
                    shutil.rmtree(project_data_folder)
                    current_app.logger.info(
                        f"Deleted project data folder: {project_data_folder}"
                    )
                except Exception as e:
                    current_app.logger.error(
                        f"Error deleting project data folder {project_data_folder}: {e}",
                        exc_info=True,
                    )
                  

            flash(
                f"Project '{project_name}' and associated data deleted successfully.",
                "success",
            )
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Error deleting project {project_id}: {e}", exc_info=True
            )
            flash("An error occurred while deleting the project.", "danger")
    else:
        # If form validation fails (e.g., didn't type DELETE correctly)
        flash(
            "Project deletion confirmation failed. Please type 'DELETE' exactly.",
            "danger",
        )
        # Redirect back to where they came from (likely the edit page)
        return redirect(
            request.referrer or url_for("main.editProject", project_id=project_id)
        )

    return redirect(
        url_for("main.view_projects")
    )  # Redirect to projects list after successful deletion


# === Review, Calibration & Upload Routes ===


@main_bp.route("/review/<uuid:project_id>")
@login_required  # Now we're requiring login to enforce calibration check
def review(project_id):
    # Check if the user has completed calibration
    if not current_user.calibrated:
        flash(
            "You need to complete eye-tracking calibration before starting a review session.",
            "warning",
        )
        # Store the intended destination in the session to redirect back after calibration
        session["next_after_calibration"] = url_for(
            "main.review", project_id=project_id
        )
        return redirect(url_for("main.calibration"))

    project_id_str = str(project_id)
    project = Project.query.get_or_404(project_id_str)
    # Generate the proxied link (using embed.figma.com seems standard for embeds)
    proxied_link = (
        project.link.replace("www.figma.com", "embed.figma.com")
        + "&embed-host=share&hide-ui=true"  # Hide Figma UI?
    )

    # Get project tasks for the review session
    tasks = project.tasks.order_by(Task.order).all()
    # Prepare tasks in the format expected by review.js
    project_tasks_json = [{"name": task.name, "minor_tasks": []} for task in tasks]

    return render_template(
        "review.html",
        project=project,
        proxied_link=proxied_link,
        project_tasks_json=project_tasks_json,
    )


@main_bp.route("/proxy/figma/<string:project_id>")
def proxy_figma(project_id):
    project = get_project_or_404(project_id)
    figma_url = project.link

    try:
        response = requests.get(figma_url)
        response.raise_for_status()

        return Response(
            response.content,
            status=response.status_code,
            headers={
                "Content-Type": response.headers.get("Content-Type"),
                "Content-Security-Policy": "frame-ancestors 'self' *",
            },
        )
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Proxy error fetching {figma_url}: {e}")
        return f"Error fetching the URL: {e}", 502


@main_bp.route("/upload", methods=["POST"])
# @login_required # Removed based on comment in /review route? Or should uploads require login? Assume requires login for now.
@login_required
def upload_review_data():
    # Get data from form
    project_id = request.form.get("project_id")
    benchmark_flag = request.form.get("benchmark", "false").lower() == "true"
    task_times_json = request.form.get("task_times")
    gaze_data_json = request.form.get("gaze_data")  # Get gaze data
    video_file = request.files.get("video")

    if not project_id:
        return jsonify({"error": "Missing project_id"}), 400
    if not task_times_json:
        return jsonify({"error": "Missing task_times data"}), 400
    # Video is required for a meaningful review
    if "video" not in request.files or not video_file or video_file.filename == "":
        return jsonify({"error": "No video file provided"}), 400

    project = Project.query.get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    # Authorization: Check if user can submit to this project
    # Anyone can submit if login not required, otherwise check permissions
    # If login IS required:
    if not check_project_permission(
        project, required_roles=["creator", "co-owner", "editor", "viewer", "admin"]
    ):  # Allow anyone associated
        return jsonify({"error": "Permission denied to submit to this project"}), 403

    # Handle benchmark conflicts/limits
    session_id = "benchmark" if benchmark_flag else str(uuid.uuid4())
    video_filename_base = session_id  # Use session ID for video filename

    if benchmark_flag:
        if project.benchmarked:
            return (
                jsonify({"error": "Benchmark already exists for this project"}),
                409,
            )  # Conflict
    else:
        # Check submission limits for non-benchmarks
        review_count = (
            db.session.query(TaskTime.session_id)
            .filter_by(project_id=project_id, is_benchmark=False)
            .distinct()
            .count()
        )
        if review_count >= project.max_submissions:
            return (
                jsonify(
                    {
                        "error": f"Maximum number of reviews ({project.max_submissions}) reached for this project"
                    }
                ),
                403,
            )

    # --- File Saving ---
    saved_video_path = None  # Track if video is saved for cleanup on DB error
    try:
        # Secure project_id and session_id for path creation
        safe_project_id = secure_filename(str(project_id))
        safe_session_id = secure_filename(session_id)

        # Create directory structure
        session_folder = os.path.join(
            current_app.config["UPLOAD_FOLDER"], safe_project_id, safe_session_id
        )
        video_folder = os.path.join(session_folder, "Video")
        # raw_folder = os.path.join(session_folder, "Raw") # Raw folder for gaze/other data?
        os.makedirs(video_folder, exist_ok=True)
        # os.makedirs(raw_folder, exist_ok=True)

        # Save video file
        # Ensure file extension is reasonable (e.g., .webm)
        _, file_ext = os.path.splitext(video_file.filename)
        if file_ext.lower() not in [".webm", ".mp4", ".mov"]:  # Basic check
            file_ext = ".webm"  # Default to webm if extension is weird/missing

        video_filename = f"{video_filename_base}{file_ext}"
        video_path = os.path.join(video_folder, video_filename)
        video_file.save(video_path)
        saved_video_path = video_path  # Mark as saved
        current_app.logger.info(f"Saved video to: {video_path}")

    except Exception as e:
        current_app.logger.error(
            f"Error saving video file for project {project_id}, session {session_id}: {e}",
            exc_info=True,
        )
        return jsonify({"error": "Failed to save uploaded video file."}), 500

    # --- Database Saving ---
    try:
        # Parse task times
        task_times = json.loads(task_times_json)
        if not isinstance(task_times, list):
            raise ValueError("task_times data is not a list")

        # Parse gaze data
        gaze_data = []
        if gaze_data_json:
            gaze_data = json.loads(gaze_data_json)
            if not isinstance(gaze_data, list):
                raise ValueError("gaze_data is not a list")

        # Store TaskTime and GazeData records
        # Create TaskTime entries first
        task_time_records = []
        for task_data in task_times:
            if (
                not isinstance(task_data, dict)
                or "task" not in task_data
                or "time" not in task_data
            ):
                current_app.logger.warning(
                    f"Skipping invalid task_data item: {task_data}"
                )
                continue
            # Ensure time is float or can be converted
            try:
                time_spent_float = float(task_data["time"])
            except (ValueError, TypeError):
                current_app.logger.warning(
                    f"Skipping task_data with invalid time: {task_data}"
                )
                continue

            tt = TaskTime(
                project_id=project_id,
                user_id=(
                    current_user.id if current_user.is_authenticated else None
                ),  # Link to submitting user if logged in
                session_id=session_id,
                task_name=task_data["task"],
                time_spent=time_spent_float,
                is_benchmark=benchmark_flag,
            )
            db.session.add(tt)
            task_time_records.append(tt)  # Keep track to link gaze data

        if not task_time_records:
            raise ValueError("No valid task time entries were processed.")

        # Commit TaskTime entries to get their IDs
        db.session.flush()  # Assign IDs without full commit yet

        # Store GazeData linked to TaskTime
        # Link all gaze points to the FIRST TaskTime entry for this session for simplicity.
        # A better approach might involve matching timestamps, but this is complex.
        if task_time_records and gaze_data:
            target_task_time_id = task_time_records[0].id
            gaze_objects_to_add = []
            for point in gaze_data:
                # Expecting [x, y] or [x, y, timestamp_ms] or {"x": x, "y": y, "t": ms}
                x_val, y_val, t_val = None, None, None
                if isinstance(point, dict) and "x" in point and "y" in point:
                    x_val = point.get("x")
                    y_val = point.get("y")
                    t_val = point.get("t")  # Timestamp is optional
                elif isinstance(point, (list, tuple)) and len(point) >= 2:
                    x_val = point[0]
                    y_val = point[1]
                    if len(point) >= 3:
                        t_val = point[2]

                # Basic validation: check if x and y are numbers
                try:
                    if x_val is not None:
                        x_val = float(x_val)
                    if y_val is not None:
                        y_val = float(y_val)
                    if t_val is not None:
                        t_val = int(t_val)  # Timestamp as int
                except (ValueError, TypeError):
                    current_app.logger.warning(
                        f"Skipping invalid gaze point data: {point}"
                    )
                    continue  # Skip this point

                if x_val is not None and y_val is not None:
                    gd = GazeData(
                        task_time_id=target_task_time_id,
                        x=x_val,
                        y=y_val,
                        timestamp_ms=t_val,  # Can be None if not provided
                    )
                    gaze_objects_to_add.append(gd)

            if gaze_objects_to_add:
                db.session.bulk_save_objects(
                    gaze_objects_to_add
                )  # Efficiently add many gaze points
                current_app.logger.info(
                    f"Added {len(gaze_objects_to_add)} gaze points for TaskTime ID {target_task_time_id}"
                )

        # Update project benchmark status if applicable
        if benchmark_flag:
            project.benchmarked = True
            db.session.add(project)  # Add project to session if modified

        db.session.commit()  # Commit all changes
        current_app.logger.info(
            f"Saved TaskTime data for project {project_id}, session {session_id}"
        )

    except json.JSONDecodeError as e:
        db.session.rollback()
        current_app.logger.error(
            f"JSON Decode Error processing upload for project {project_id}: {e}"
        )
        # Clean up saved video file if DB save failed
        if saved_video_path and os.path.exists(saved_video_path):
            try:
                os.remove(saved_video_path)
            except Exception as cleanup_e:
                current_app.logger.error(
                    f"Error cleaning up video file {saved_video_path}: {cleanup_e}"
                )
        return jsonify({"error": f"Invalid JSON data format: {e}"}), 400
    except ValueError as e:
        db.session.rollback()
        current_app.logger.error(
            f"Value Error processing upload for project {project_id}: {e}"
        )
        # Clean up saved video file if DB save failed
        if saved_video_path and os.path.exists(saved_video_path):
            try:
                os.remove(saved_video_path)
            except Exception as cleanup_e:
                current_app.logger.error(
                    f"Error cleaning up video file {saved_video_path}: {cleanup_e}"
                )
        return jsonify({"error": f"Invalid data structure: {e}"}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error saving review data for project {project_id}: {e}", exc_info=True
        )
        # Clean up saved video file if DB save failed
        if saved_video_path and os.path.exists(saved_video_path):
            try:
                os.remove(saved_video_path)
                # Maybe remove session folder if empty? Needs careful check
                # if not os.listdir(session_folder): os.rmdir(session_folder) # Risky if other files exist
            except Exception as cleanup_e:
                current_app.logger.error(
                    f"Error cleaning up video file {saved_video_path}: {cleanup_e}"
                )
        return jsonify({"error": "Failed to save review data to database."}), 500

    
    relative_video_path = os.path.join(
        "static_data",
        "data",
        "Projects",
        safe_project_id,
        safe_session_id,
        "Video",
        video_filename,
    ).replace("\\", "/")

    return (
        jsonify(
            {
                "message": "Review data uploaded successfully",
                "session_id": session_id,
                "video_path": relative_video_path,  # Optional: return path
            }
        ),
        200,
    )


@main_bp.route("/viewReviewBroad/<uuid:project_id>")
@login_required
def view_review_broad(project_id):
    project_id_str = str(project_id)
    project = get_project_or_404(project_id_str)

    # Authorization check
    if not check_project_permission(project):
        flash(
            "You do not have permission to view this project's submissions.", "danger"
        )
        return redirect(url_for("main.home"))  # Redirect home if no access

    project_data_folder = os.path.join(
        current_app.config["UPLOAD_FOLDER"], secure_filename(project_id_str)
    )
    videos = []

    if os.path.exists(project_data_folder):
        try:
            # Get session IDs from TaskTime table for this project (excluding benchmark)
            valid_session_ids = {
                tt.session_id
                for tt in TaskTime.query.with_entities(TaskTime.session_id)
                .filter_by(project_id=project_id_str, is_benchmark=False)
                .distinct()
            }

            for session_id in valid_session_ids:
                # Make sure session_id is not 'benchmark' just in case
                if session_id.lower() == "benchmark":
                    continue

                safe_session_id = secure_filename(session_id)
                session_path = os.path.join(project_data_folder, safe_session_id)
                video_folder = os.path.join(session_path, "Video")

                if os.path.isdir(video_folder):
                    for filename in os.listdir(video_folder):
                        # Look for common video extensions
                        if filename.lower().endswith(
                            (".webm", ".mp4", ".mov")
                        ): 
                            # Construct relative static path for url_for
                            relative_path = os.path.join(
                                "static_data",
                                "data",
                                "Projects",
                                secure_filename(project_id_str),
                                safe_session_id,  # Use secured session ID
                                "Video",
                                filename,
                            ).replace(
                                "\\", "/"
                            )  # Use forward slashes for URL

                            videos.append(
                                {
                                    "path": relative_path,
                                    "session_id": session_id,  # Use actual session ID for logic
                                    "filename": filename,
                                }
                            )
                            break  # Assume one video per session/Video folder
        except Exception as e:
            current_app.logger.error(
                f"Error reading session folders for project {project_id_str}: {e}",
                exc_info=True,
            )
            flash("Error loading project submissions.", "danger")

   
    # Example sort by session_id (string sort)
    videos.sort(
        key=lambda v: v.get("session_id", ""), reverse=True
    )  # Sort newest-ish first if UUIDs

    return render_template(
        "viewReviewBroad.html", videos=videos, project_id=project_id_str
    )


@main_bp.route(
    "/viewReviewSpecific/<string:session_id>"
)  # Session ID is now string (UUID or 'benchmark')
@login_required
def view_review_specific(session_id):
    project_id = request.args.get("project_id")
    if not project_id:
        flash("Project ID is missing.", "danger")
        return redirect(url_for("main.home"))  # Or back

    project = Project.query.get(project_id)
    if not project:
        flash("Project not found.", "danger")
        return redirect(url_for("main.home"))  # Or back

    # Authorization check
    if not check_project_permission(project):
        flash("You do not have permission to view this submission.", "danger")
        return redirect(url_for("main.view_projects"))

    # Fetch benchmark times for comparison (order by task name maybe?)
    benchmark_times_db = (
        TaskTime.query.filter_by(project_id=project_id, is_benchmark=True)
        .order_by(TaskTime.task_name)
        .all()
    )
    benchmark_times = [
        {"task": task.task_name, "time": task.time_spent} for task in benchmark_times_db
    ]

    # Fetch review times for this specific session (order by timestamp or task name?)
    review_times_db = (
        TaskTime.query.filter_by(
            project_id=project_id,
            session_id=session_id,
            is_benchmark=False,  # Ensure we don't fetch benchmark times here
        )
        .order_by(TaskTime.timestamp)
        .all()
    )  # Order by when they were recorded
    review_times = [
        {"task": task.task_name, "time": task.time_spent} for task in review_times_db
    ]

    # Find the video file path
    video_url = None
    safe_project_id = secure_filename(str(project_id))
    safe_session_id = secure_filename(session_id)
    video_folder_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"], safe_project_id, safe_session_id, "Video"
    )

    if os.path.exists(video_folder_path):
        try:
            for filename in os.listdir(video_folder_path):
                if filename.lower().endswith((".webm", ".mp4", ".mov")):
                    relative_path = os.path.join(
                        "static_data",
                        "data",
                        "Projects",
                        safe_project_id,
                        safe_session_id,
                        "Video",
                        filename,
                    ).replace("\\", "/")
                    video_url = relative_path
                    break  # Found the video
        except Exception as e:
            current_app.logger.error(
                f"Error finding video file in {video_folder_path}: {e}"
            )

    if not video_url:
        flash(f"Video file for session '{session_id}' not found.", "warning")
        # Don't block page load, template should handle missing video

    return render_template(
        "viewReviewSpecific.html",
        benchmark_times=benchmark_times,
        review_times=review_times,
        video_url=video_url,  # Pass relative URL for url_for('static')
        project_id=project_id,
        session_id=session_id,  # Pass session_id to template as well
    )


@main_bp.route("/delete_review", methods=["POST"])
@login_required
def delete_review():
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "Invalid request data"}), 400

    project_id = data.get("project_id")
    session_id = data.get("session_id")  # Use session_id from client

    if not project_id or not session_id:
        return (
            jsonify({"success": False, "message": "Missing project_id or session_id"}),
            400,
        )

    # Don't allow deleting the benchmark session via this route
    if session_id.lower() == "benchmark":
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Cannot delete benchmark session here. Use the dedicated delete benchmark action.",
                }
            ),
            400,
        )

    project = Project.query.get(project_id)
    if not project:
        return jsonify({"success": False, "message": "Project not found"}), 404

    # Authorization: Allow creator, co-owner, admin?
    if not current_user.can_manage_collaborators(
        project_id
    ):  # Reuse manage collaborators permission
        return jsonify({"success": False, "message": "Permission denied"}), 403

    # --- Delete Database Entries ---
    deleted_count = 0
    try:
        # Find TaskTime entries for this session (also deletes linked GazeData via cascade)
        # Ensure we don't delete benchmark entries if session_id somehow matches
        task_times_to_delete = TaskTime.query.filter_by(
            project_id=project_id,
            session_id=session_id,
            is_benchmark=False,  # Explicitly target non-benchmarks
        ).all()

        if task_times_to_delete:
            deleted_count = len(task_times_to_delete)
            for tt in task_times_to_delete:
                db.session.delete(tt)
            db.session.commit()
            current_app.logger.info(
                f"Deleted {deleted_count} TaskTime/GazeData records for project {project_id}, session {session_id}"
            )
        else:
            current_app.logger.warning(
                f"No TaskTime records found to delete for project {project_id}, session {session_id}"
            )
            # Still proceed to delete files if they exist

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error deleting database records for review {project_id}/{session_id}: {e}",
            exc_info=True,
        )
        return (
            jsonify({"success": False, "message": "Database error during deletion."}),
            500,
        )

    # --- Delete Filesystem Data ---
    try:
        safe_project_id = secure_filename(str(project_id))
        safe_session_id = secure_filename(session_id)
        session_folder_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"], safe_project_id, safe_session_id
        )

        if os.path.exists(session_folder_path):
            shutil.rmtree(session_folder_path)
            current_app.logger.info(f"Deleted session folder: {session_folder_path}")
            return (
                jsonify(
                    {
                        "success": True,
                        "message": "Review submission deleted successfully.",
                    }
                ),
                200,
            )
        else:
            # If folder doesn't exist but DB entries might have, still report success
            current_app.logger.warning(
                f"Session folder not found, but database entries deleted (if any): {session_folder_path}"
            )
            # Check if DB records were deleted to determine message
            if deleted_count > 0:
                return (
                    jsonify(
                        {
                            "success": True,
                            "message": "Review data deleted (files not found).",
                        }
                    ),
                    200,
                )
            else:
                # Nothing was found in DB or FS
                return (
                    jsonify(
                        {"success": False, "message": "Review submission not found."}
                    ),
                    404,
                )

    except Exception as e:
        current_app.logger.error(
            f"Error deleting session folder {project_id}/{session_id}: {e}",
            exc_info=True,
        )
        # Return partial success? Or error? Let's return error as FS cleanup failed.
        message = (
            "Database records deleted, but failed to delete files."
            if deleted_count > 0
            else "Failed to delete submission files."
        )
        return jsonify({"success": False, "message": f"{message} Error: {e}"}), 500


@main_bp.route("/delete_benchmark/<uuid:project_id>", methods=["POST"])
@login_required
def delete_benchmark(project_id):
    project_id_str = str(project_id)
    project = get_project_or_404(project_id_str)

    # Authorization (Creator or Admin should be able to delete benchmark)
    if not current_user.can_delete_project(
        project.id
    ):  # Use can_delete_project permission
        flash(
            "You do not have permission to delete the benchmark for this project.",
            "danger",
        )
        # Redirect back to where delete was likely triggered
        return redirect(request.referrer or url_for("main.viewProjects"))

    benchmark_session_id = "benchmark"

    # --- Delete Database Entries ---
    try:
        # Find TaskTime entries for the benchmark session (also deletes linked GazeData via cascade)
        deleted_count = TaskTime.query.filter_by(
            project_id=project_id_str,
            session_id=benchmark_session_id,
            is_benchmark=True,
        ).delete()
        # Update project status only if something was deleted
        if deleted_count > 0:
            project.benchmarked = False
            db.session.add(project)  # Make sure project is added to session for update
            db.session.commit()
            current_app.logger.info(
                f"Deleted {deleted_count} benchmark TaskTime/GazeData records for project {project_id_str}"
            )
        else:
            # No benchmark records found, commit any potential pending changes? Unlikely needed.
            db.session.rollback()  # Rollback if nothing was done
            current_app.logger.warning(
                f"No benchmark database records found to delete for project {project_id_str}"
            )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error deleting benchmark database records for project {project_id_str}: {e}",
            exc_info=True,
        )
        flash("Database error while deleting benchmark data.", "danger")
        return redirect(request.referrer or url_for("main.viewProjects"))

    # --- Delete Filesystem Data ---
    try:
        safe_project_id = secure_filename(project_id_str)
        safe_session_id = secure_filename(benchmark_session_id)
        session_folder_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"], safe_project_id, safe_session_id
        )

        if os.path.exists(session_folder_path):
            shutil.rmtree(session_folder_path)
            current_app.logger.info(
                f"Deleted benchmark session folder: {session_folder_path}"
            )
        else:
            current_app.logger.warning(
                f"Benchmark session folder not found: {session_folder_path}"
            )

        flash("Benchmark deleted successfully!", "success")
    except Exception as e:
        current_app.logger.error(
            f"Error deleting benchmark session folder for project {project_id_str}: {e}",
            exc_info=True,
        )
        flash(
            "Benchmark database entries deleted, but failed to delete files.", "warning"
        )

    return redirect(request.referrer or url_for("main.viewProjects"))


@main_bp.route("/calibration")
@login_required
def calibration():
    # Ensure user is authenticated, redirect handled by @login_required
    return render_template("calibration.html")


@main_bp.route("/calibration_complete", methods=["POST"])
@login_required
def calibration_complete():
    try:
        current_user.calibrated = True
        db.session.commit()

        # Check if there's a pending redirection after calibration
        next_page = session.pop("next_after_calibration", None)

        if next_page:
            return (
                jsonify(
                    {"message": "Calibration status updated", "redirect": next_page}
                ),
                200,
            )
        else:
            return jsonify({"message": "Calibration status updated"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error updating calibration status for user {current_user.id}: {e}",
            exc_info=True,
        )
        return jsonify({"error": "Failed to update calibration status"}), 500


# @main_bp.route("/generate_heatmap/<uuid:project_id>")
# @login_required
# def generate_heatmap(project_id):
#     project_id_str = str(project_id)
#     project = get_project_or_404(project_id_str)

#     # Authorization
#     if not check_project_permission(project):
#          flash("You do not have permission to view this project's heatmap.", "danger")
#          return redirect(url_for('main.home'))

#     # Fetch actual gaze data for this project
#     # Get all TaskTime IDs for the project (including benchmark?)
#     # Let's include benchmark for heatmap? Or exclude? Exclude for now.
#     task_time_ids = [
#         tt.id for tt in TaskTime.query.with_entities(TaskTime.id).filter_by(
#             project_id=project_id_str,
#             is_benchmark=False # Exclude benchmark data from heatmap
#         ).all()
#     ]

#     if not task_time_ids:
#          flash("No review data found to generate heatmap.", "info")
#          # Render template with a message or redirect
#          return render_template("heatmap.html", project=project, heatmap_data=None, message="No review gaze data available.")

#     # Fetch GazeData points efficiently
#     gaze_points = GazeData.query.filter(
#         GazeData.task_time_id.in_(task_time_ids),
#         GazeData.x.isnot(None), # Ensure coordinates are not null
#         GazeData.y.isnot(None)
#     ).all()


#     if not gaze_points:
#          flash("No valid gaze data points found for reviews of this project.", "info")
#          return render_template("heatmap.html", project=project, heatmap_data=None, message="No valid gaze data points available.")

#     # Extract X, Y coordinates
#     x_coords = [p.x for p in gaze_points]
#     y_coords = [p.y for p in gaze_points]


#     # --- Generate Heatmap using Matplotlib ---
#     try:
#         # Determine bounds dynamically or use standard screen size?
#         # Dynamic bounds might be better if screen sizes vary widely
#         min_x, max_x = min(x_coords), max(x_coords)
#         min_y, max_y = min(y_coords), max(y_coords)
#         # Ensure range is valid
#         range_x = max_x - min_x
#         range_y = max_y - min_y
#         if range_x <= 0 or range_y <= 0:
#              # Fallback to a default screen size if data is degenerate
#              min_x, max_x = 0, 1920
#              min_y, max_y = 0, 1080
#              range_x, range_y = 1920, 1080

#         # Adjust bins based on data range
#         bins_x = 100
#         # Maintain aspect ratio for bins based on data range
#         bins_y = int(bins_x * (range_y / range_x)) if range_x > 0 else 50
#         bins_y = max(10, bins_y) # Ensure minimum number of bins


#         heatmap, xedges, yedges = np.histogram2d(
#             x_coords, y_coords,
#             bins=(bins_x, bins_y),
#             range=[[min_x, max_x], [min_y, max_y]] # Define range based on data
#         )

#         # Optional: Apply smoothing/log scale for better visualization
#         # heatmap = np.log1p(heatmap) # Log scale can help with sparse data
#         from scipy.ndimage import gaussian_filter
#         heatmap = gaussian_filter(heatmap, sigma=3) # Increase sigma for more blur/smoothing

#         plt.figure(figsize=(12, 12 * (range_y / range_x) if range_x > 0 else 7 )) # Adjust figure size based on aspect ratio
#         # Use extent to label axes correctly based on range
#         plt.imshow(heatmap.T, origin='lower', cmap='inferno', # Or 'hot', 'viridis' etc.
#                    extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]],
#                    aspect='auto') # Adjust aspect ratio if needed
#         plt.colorbar(label='Gaze Intensity / Density')
#         plt.title(f"Gaze Heatmap for Project: {project.name}")
#         plt.xlabel("Screen X Coordinate")
#         plt.ylabel("Screen Y Coordinate")
#         plt.xlim(min_x, max_x) # Ensure axes match range
#         plt.ylim(min_y, max_y)
#         plt.grid(True, alpha=0.2) # Add faint grid

#         # Save plot to a BytesIO object
#         img = BytesIO()
#         plt.savefig(img, format='png', bbox_inches='tight') # Use tight bounding box
#         img.seek(0)
#         plt.close() # Close the plot to free memory

#         # Encode image as base64
#         img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')

#         return render_template("heatmap.html", project=project, heatmap_data=img_base64, message=None)

#     except Exception as e:
#         current_app.logger.error(f"Error generating heatmap for project {project_id_str}: {e}", exc_info=True)
#         flash("Could not generate heatmap due to an error.", "danger")
#         return render_template("heatmap.html", project=project, heatmap_data=None, message="Error generating heatmap.")


# === Figma Proxy (Optional - Review ToS and Need) ===
# Remove this if not needed or if it violates Figma ToS
@main_bp.route("/proxy/")
def proxy():
    target_url = request.args.get("url")
    if not target_url:
        return "No URL provided.", 400

    # Basic validation - refine this significantly if keeping the proxy
    allowed_domains = ["embed.figma.com", "www.figma.com"]
    try:
        from urllib.parse import urlparse

        parsed_url = urlparse(target_url)
        if (
            not parsed_url.scheme in ["http", "https"]
            or parsed_url.netloc not in allowed_domains
        ):
            current_app.logger.warning(
                f"Proxy attempt blocked for domain: {parsed_url.netloc}"
            )
            return "Unauthorized domain.", 403
    except Exception:
        return "Invalid URL format.", 400

    try:
        # Send request with stream=True for potentially large content
        response = requests.get(target_url, stream=True, timeout=10)  # Add timeout
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        # Remove headers that might prevent embedding
        excluded_headers = [
            "content-security-policy",
            "x-frame-options",
            "content-encoding",
            "transfer-encoding",
        ]
        headers = {
            name: value
            for name, value in response.raw.headers.items()
            if name.lower() not in excluded_headers
        }

        # Stream the response back to the client
        return Response(
            response.raw.stream(decode_content=False), response.status_code, headers
        )

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Proxy error fetching {target_url}: {e}")
        return f"Error fetching the URL: {e}", 502  # Bad Gateway
    except Exception as e:
        current_app.logger.error(
            f"Generic proxy error for {target_url}: {e}", exc_info=True
        )
        return "An unexpected error occurred in the proxy.", 500


# === Admin Panel Routes ===


@main_bp.route("/admin", methods=["GET", "POST"])
@login_required
def admin_panel():
    if current_user.role != "admin":
        flash("You do not have permission to access the admin panel.", "danger")
        return redirect(url_for("main.home"))

    edit_account_form = EditAccountTypeForm()
    delete_user_form = DeleteUserForm()
    delete_project_form = DeleteProjectForm()  # For deleting projects listed below

    # Use prefixes or distinct submit button names if handling multiple forms via one route
    # Add name="submit_edit_user" to the submit button in the template
    if "submit_edit_user" in request.form and edit_account_form.validate_on_submit():
        user = User.query.filter(
            User.username.ilike(edit_account_form.username.data)
        ).first()
        if user:
            if user.role == "admin" and User.query.filter_by(role="admin").count() <= 1:
                flash("Cannot change role of the only administrator.", "danger")
            elif user.id == current_user.id:
                flash("Cannot change your own role.", "danger")
            else:
                user.role = edit_account_form.role.data
                db.session.commit()
                flash(f"User '{user.username}' role updated to {user.role}.", "success")
        else:
            flash("User not found.", "danger")
        return redirect(url_for("main.admin_panel"))  # Redirect after POST

    # Add name="submit_delete_user" to the submit button in the template
    elif "submit_delete_user" in request.form and delete_user_form.validate_on_submit():
        user = User.query.filter(
            User.username.ilike(delete_user_form.username.data)
        ).first()
        if user:
            if user.id == current_user.id:
                flash("You cannot delete your own account.", "danger")
            elif (
                user.role == "admin" and User.query.filter_by(role="admin").count() <= 1
            ):
                flash("Cannot delete the only administrator.", "danger")
            else:
                try:
                    # Manually delete projects owned by user first? Or rely on cascade?
                    # Cascade might be okay if DB supports it well. If using SQLite, manual might be safer.
                    # For now, rely on cascade defined in models (ondelete='CASCADE')
                    username_deleted = user.username  # Get username before deleting

                    # Delete user's profile pic file first
                    if user.picture and user.picture != "images/pic.png":
                        pic_path = os.path.join(
                            current_app.config["USER_PROFILE_UPLOAD_FOLDER"],
                            user.picture,
                        )
                        if os.path.exists(pic_path):
                            try:
                                os.remove(pic_path)
                                current_app.logger.info(
                                    f"Deleted profile picture {pic_path} for user {username_deleted}"
                                )
                            except Exception as pic_e:
                                current_app.logger.error(
                                    f"Error deleting profile picture {pic_path}: {pic_e}"
                                )

                    db.session.delete(user)
                    db.session.commit()
                    flash(
                        f"User '{username_deleted}' and associated data (projects, submissions) deleted successfully.",
                        "success",
                    )
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(
                        f"Error deleting user {user.username}: {e}", exc_info=True
                    )
                    flash("An error occurred while deleting the user.", "danger")
        else:
            flash("User not found.", "danger")
        return redirect(url_for("main.admin_panel"))

    # Handle project deletion via the dedicated route /admin/delete_project triggered by the forms below

    # Add logic to fetch users/projects to list in the admin panel
    all_users = User.query.order_by(User.username).all()
    all_projects = Project.query.order_by(Project.created_at.desc()).all()

    return render_template(
        "adminPanel.html",
        edit_account_form=edit_account_form,
        delete_user_form=delete_user_form,
        delete_project_form=delete_project_form,  # Pass form for use in listing
        all_users=all_users,
        all_projects=all_projects,
    )


# Route specifically for handling project deletion from the admin panel list
@main_bp.route("/admin/delete_project", methods=["POST"])
@login_required
def admin_delete_project():
    if current_user.role != "admin":
        return jsonify({"success": False, "message": "Permission denied"}), 403

    form = DeleteProjectForm()  # Process this specific form
    if form.validate_on_submit():  # Checks hidden project_id and confirm_text
        project = Project.query.get(form.project_id.data)
        if project:
            try:
                project_name = project.name
                project_id_str = project.id  # Get ID before deleting
                # Cascading deletes should handle related data
                db.session.delete(project)
                db.session.commit()

                # Delete associated static files
                project_data_folder = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], secure_filename(project_id_str)
                )
                if os.path.exists(project_data_folder):
                    try:
                        shutil.rmtree(project_data_folder)
                        current_app.logger.info(
                            f"Admin deleted project data folder: {project_data_folder}"
                        )
                    except Exception as e:
                        current_app.logger.error(
                            f"Admin error deleting project data folder {project_data_folder}: {e}",
                            exc_info=True,
                        )

                flash(
                    f"Project '{project_name}' ({project_id_str[:8]}...) deleted by admin.",
                    "success",
                )
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(
                    f"Admin error deleting project {project.id}: {e}", exc_info=True
                )
                flash("An error occurred while deleting the project.", "danger")
        else:
            flash("Project not found.", "danger")
    else:
        # Flash form errors if validation fails (e.g., confirm text mismatch)
        error_msg = "Project deletion confirmation failed."
        if "confirm_text" in form.errors:
            error_msg += f" {form.errors['confirm_text'][0]}"
        elif "project_id" in form.errors:
            error_msg += " Missing project ID."
        flash(error_msg, "danger")

    return redirect(url_for("main.admin_panel"))


# === REMOVED Routes ===
# /write_logs - Removed due to security risk. Implement proper server-side logging.
# /save_gaze_data - Merged into /upload route logic.
# /clear-login-success - Flash messages are typically displayed once and cleared automatically.
