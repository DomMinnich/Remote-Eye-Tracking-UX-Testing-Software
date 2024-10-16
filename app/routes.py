# routes.py, routes for the Flask application

from flask import Blueprint, render_template, redirect, session, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from .models import db, User
from .forms import RegistrationForm, LoginForm

main = Blueprint('main', __name__)
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user:
            flash('Username already exists. Please choose a different username.', 'danger')
        else:
            new_user = User(username=form.username.data)
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('main.login'))
    return render_template('register.html', form=form)


@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None:
            flash('- Username Not Found -', 'danger')
        elif not user.check_password(form.password.data):
            flash('- Incorrect Password -', 'danger')
        else:
            login_user(user)
            flash('Logged In Successfully!', 'success')  # Only success message
            return render_template('login.html', form=form)

    return render_template('login.html', form=form)


    return render_template('login.html', form=form)

@main.route('/clear-login-success', methods=['POST'])
def clear_login_success():
    session.pop("login_success", None)
    return '', 204  # Return 'No Content' response


@main.route('/logout')
def logout():
    logout_user()
    flash('Logged Out Successfully!', 'success')
    return redirect(url_for('main.login'))

@main.route('/')
@login_required
def home():
    return render_template('home.html')
