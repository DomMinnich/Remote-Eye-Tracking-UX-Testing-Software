# models.py, database models for the application
# 2024


#         CONTENTS OF THIS FILE A-Z
#    *Imports                     | ~Line 12-16
#    Class User                   | ~Line 21-31   -Dominic Minnich
#    .?.?.                        | ~Line ??


import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin  # Import UserMixin for built-in methods

db = SQLAlchemy()


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
    config = db.Column(db.JSON, nullable=True)  # Store JSON of user settings

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
