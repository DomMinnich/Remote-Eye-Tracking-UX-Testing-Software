# forms.py, forms for the Flask application

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitButton
from wtforms.validators import DataRequired

class SampleForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitButton('Submit')
