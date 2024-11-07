# models.py, database models for the application
# 2024


#         CONTENTS OF THIS FILE A-Z
#    *Imports                     | ~Line 12-16
#    User                         | ~Line 21-31   -Dominic Minnich
#    .?.?.                        | ~Line ??


from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin  # Import UserMixin for built-in methods
from datetime import datetime

db = SQLAlchemy()

# models.py


class User(db.Model, UserMixin):  # Inherit from UserMixin to add necessary properties
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
#Kyle Benich
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True) # Primary key, unique identifier for each project (This is what a user has in their "projects" list)
    link = db.Column(db.String(255), unique=True, nullable=False) # Unique link to Figma
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) # Time of creation, used for EoL
    creator = db.Column(db.Integer, nullable=False) # User ID of creator
    priviledged = db.Column(db.Boolean, nullable=False) # This will not change, and allows the collaberator field to be used. This allows for demotion of a owner to not affect the project
    tasks = db.Column(db.JSON, nullable=False) # JSON object of tasks (Example in Disc)
    max_submissions = db.Column(db.Integer, nullable=False) # Max number of submissions
    eol_time = db.Column(db.DateTime, nullable=False) # End of life time
    collaborators = db.Column(db.JSON, nullable=False) # JSON object of collaborators (Example in Disc)
    numPauses = db.Column(db.Integer, nullable=False) # Number of times the project has been paused (Maximum of.. 3? 2?)
