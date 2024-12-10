# models.py, database models for the application
# 2024


#         CONTENTS OF THIS FILE A-Z
#    *Imports                     | ~Line 12-16
#    Class User                   | ~Line 21-31   -Dominic Minnich
#    .?.?.                        | ~Line ??


import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin  # Import UserMixin for built-in methods
from datetime import datetime

db = SQLAlchemy()
mail = Mail()

class User(db.Model, UserMixin):  # Inherit from UserMixin to add necessary properties
    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False,
    )
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), default="student", nullable=False)
    calibrated = db.Column(db.Boolean, default=False, nullable=False)
    picture = db.Column(db.String(200))  # Store path or URL to the picture
    projects = db.Column(db.JSON, nullable=True)  # Store JSON of project IDs
    shared_projects = db.Column(db.JSON, nullable=True)  # Store JSON of project IDs
    config = db.Column(db.JSON, nullable=True)  # Store JSON of user settings
    email_opt_in = db.Column(db.Boolean, default=False, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Kyle Benich
class Project(db.Model):
    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False,
    )
    link = db.Column(
        db.String(255), unique=True, nullable=False
    )  # Unique link to Figma
    created_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )  # Time of creation, used for EoL
    creator = db.Column(db.Integer, nullable=False)  # User ID of creator
    priviledged = db.Column(
        db.Boolean, nullable=False
    )  # This will not change, and allows the collaberator field to be used. This allows for demotion of a owner to not affect the project
    tasks = db.Column(db.JSON, nullable=False)  # JSON object of tasks (Example in Disc)
    max_submissions = db.Column(db.Integer, nullable=False)  # Max number of submissions
    eol_time = db.Column(db.DateTime, nullable=False)  # End of life time
    collaborators = db.Column(
        db.JSON, nullable=False
    )  # JSON object of collaborators (Example in Disc)
    numPauses = db.Column(
        db.Integer, nullable=False
    )  # Number of times the project has been paused (Maximum of.. 3? 2?)

    @staticmethod
    def generate_unique_id():
        while True:
            new_id = str(uuid.uuid4())
            if not User.query.get(new_id) and not Project.query.get(new_id):
                return new_id

    @staticmethod
    def find_user_id_by_email(email):
        user = User.query.filter_by(email=email).first()
        return user.id if user else None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.id = self.generate_unique_id()
