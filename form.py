from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField,BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import db,User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    fullname = StringField('Full Name', validators=[DataRequired(), Length(min=3, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')  # Add this line for the remember me checkbox
    submit = SubmitField('Login')


class UploadForm(FlaskForm):
    file = FileField('Upload a File', validators=[DataRequired()], render_kw={'multiple': True})
    short_name = StringField('URL Name', validators=[DataRequired()])
    password = PasswordField('Password (Optional)')
    submit = SubmitField('Upload File')
