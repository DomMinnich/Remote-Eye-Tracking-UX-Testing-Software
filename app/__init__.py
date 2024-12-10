# Dominic Minnich 2024
# __init__.py, initialization file for the Flask application

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .models import db, mail
from .routes import main, login_manager
from flask_mail import Mail

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    # Redirect unauthorized users to login page
    login_manager.login_view = "main.login"

    app.register_blueprint(main)

    # For development error debugging purposes you can comment out the following blocks
    @app.errorhandler(404)
    def page_not_found(e):
            return render_template('404.html'), 404
    
    @app.errorhandler(Exception)
    def handle_exception(e):
            return render_template('error.html'), 500


    with app.app_context():
        db.create_all()  # Creates database tables for our data models

    return app
