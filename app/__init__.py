# __init__.py, initialization file for the Flask application
# 2024

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .models import db
from .routes import main, login_manager

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'  # Redirect unauthorized users to login page

    app.register_blueprint(main)

    with app.app_context():
        db.create_all()  # Creates database tables for our data models

    return app
