# models.py, database models for the application
# 2024


#         CONTENTS OF THIS STYLE FILE A-Z
#    *Imports                     | ~Line 12-16
#    User                         | ~Line 21-31   -Dominic Minnich
#    .?.?.                        | ~Line ??


from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin  # Import UserMixin for built-in methods

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
