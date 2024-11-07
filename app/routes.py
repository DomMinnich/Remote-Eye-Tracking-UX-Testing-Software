# routes.py, routes for the Flask application
#2024


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

#Imports
from flask import Blueprint, render_template, redirect, session, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from .models import db, User
from .forms import RegistrationForm, LoginForm
# Blueprint
main = Blueprint('main', __name__)
# LoginManager instance
login_manager = LoginManager()


# Routes

# /
@main.route('/')
@login_required
def home():
    return render_template('home.html')

# /aboutUs route
@main.route('/aboutUs')
def aboutUs():
    return render_template('aboutUs.html')


# /clear-login-success
@main.route('/clear-login-success', methods=['POST'])
def clear_login_success():
    session.pop("login_success", None)
    return '', 204  # Return 'No Content' response

# /logout
@main.route('/logout')
def logout():
    logout_user()
    flash('Logged Out Successfully!', 'success')
    return redirect(url_for('main.login'))

# /login
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

# /register
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

# User_loader
@login_manager.user_loader
def load_user(user_id):
    # Since user_id is now a UUID string, I removed the int() conversion
    return User.query.get(user_id)

# /profile
@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

# /settings
@main.route('/settings')
@login_required
def settings():
    return render_template('settings.html', user=current_user)

@main.route('/ViewProjects')
@login_required
def ViewProjects():
    return render_template('ViewProjects.html', user=current_user) 