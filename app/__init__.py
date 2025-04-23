# __init__.py
from flask import Flask, render_template, request, session as flask_session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
import os
import logging
from logging.handlers import RotatingFileHandler

# Import extensions but initialize them later
from .models import db, mail # Import db and mail from models

login_manager = LoginManager()
migrate = Migrate()

def create_app(config_class=None):
    app = Flask(__name__)

    # Load configuration
    if config_class is None:
        app.config.from_object("config.Config") # Default config
    else:
        app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Configure LoginManager
    login_manager.login_view = "main.login" # Use 'main' blueprint name now
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    # Register the single main blueprint
    from .routes import main_bp # Import the single blueprint
    app.register_blueprint(main_bp)

    # User loader callback
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User # Import here to avoid circular dependency
        return User.query.get(str(user_id))

    # Custom error handlers
    @app.errorhandler(404)
    def page_not_found(e):
         app.logger.warning(f"404 Not Found: {request.url} - Referrer: {request.referrer}")
         return render_template('404.html'), 404

    @app.errorhandler(500) # Catch specific 500 errors first
    def internal_server_error(e):
        db.session.rollback() # Rollback potentially broken db session
        app.logger.error(f"Internal Server Error: {e}", exc_info=True)
        error_message = "An internal server error occurred." # Generic message for user
        return render_template('error.html', error=error_message), 500


    @app.errorhandler(Exception) # Catch broader exceptions
    def handle_exception(e):

        if hasattr(e, 'code'):
            try:
                code = int(e.code)  # Convert to int if it's a string
                if 400 <= code < 500:
                    app.logger.warning(f"HTTP Exception {code}: {e.description} - URL: {request.url}")
                    # You might want specific templates for 403, 401 etc.
                    return render_template('error.html', error=f"Error {code}: {e.description}"), code
            except (ValueError, TypeError):
                # If code can't be converted to int, or other error occurs
                app.logger.warning(f"HTTP Exception with non-numeric code: {e.code}: {e}")
        
        # Treat as 500 if not an HTTP client error
        db.session.rollback() # Rollback potentially broken db session
        app.logger.error(f"Unhandled Exception: {e}", exc_info=True)
        error_message = "An unexpected error occurred."
        return render_template('error.html', error=error_message), 500



    # Configure Logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/eyecdesign.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('EyeC.Design startup')

    # Add shell context processor for CLI tools like 'flask shell'
    @app.shell_context_processor
    def make_shell_context():
        from .models import User, Project, Task, Collaborator, TaskTime, GazeData
        return {'db': db, 'User': User, 'Project': Project, 'Task': Task,
                'Collaborator': Collaborator, 'TaskTime': TaskTime, 'GazeData': GazeData}

    return app