# config.py
from datetime import timedelta
import os

# Determine the base directory of the application
basedir = os.path.abspath(os.path.dirname(__file__))

DB_FOLDER = os.path.join(os.getcwd(), 'databases')

class Config:
    # --- Security ---
    # WARNING: Storing secrets directly in code is insecure for production.
    # Use environment variables, an instance folder config, or secrets management.
    SECRET_KEY = os.environ.get('SECRET_KEY') or "another-very-strong-dev-secret-key-345" # Default for dev

    # --- Database ---
    # Uses app.db in the base directory by default
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance/app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Flask-Mail Configuration ---
    # WARNING: Hardcoding credentials is insecure. Use environment variables.
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com' # Example
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']

    # IMPORTANT: Set these via environment variables in production!
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or '' # e.g., 'your-email@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or '' # e.g., 'your-app-password'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'EyeC Design <noreply@eyec.design>' # Example

    # --- Application Specific ---
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'static_data', 'data', 'Projects')
    USER_PROFILE_UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads', 'userProfiles')
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'} # For profile pics
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024 #100MB upload limit for videos

    # Project Limits & Config
    MAX_PROJECTS_STUDENT = 4
    MAX_PROJECTS_PRIVILEGED = 100 # PM/Admin
    EOL_DAYS_STUDENT = timedelta(days=10) # Use timedelta
    EOL_DAYS_PRIVILEGED = timedelta(days=300)
    MAX_SUBMISSIONS_BENCHMARK = 1 # Only one benchmark allowed
    MAX_SUBMISSIONS_DEFAULT = 50 # Max reviews per project

    # Ensure upload folders exist on application start
    try:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(USER_PROFILE_UPLOAD_FOLDER, exist_ok=True)
    except OSError as e:
        print(f"Error creating upload directories: {e}")

    # --- Security Headers (Optional - requires Flask-Talisman or manual setup) ---
    # CSP = { ... } # Content Security Policy definition