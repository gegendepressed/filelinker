from flask_wtf import FlaskForm
from wtforms import validators, StringField, PasswordField, SubmitField, FileField,BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from flask_wtf.file import FileField,FileAllowed,FileSize

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
    remember = BooleanField('Remember Me') 
    submit = SubmitField('Login')


class UploadForm(FlaskForm):
    title=StringField('Title',validators=[Length(max=100)])
    message = TextAreaField("Message", validators=[Length(max=1000)])
    file = FileField('Upload a File', validators=[DataRequired()], render_kw={'multiple': True})
    short_name = StringField('URL Name', validators=[DataRequired()])
    password = PasswordField('Password (Optional)')
    submit = SubmitField('Upload File')

class MessageForm(FlaskForm):
    title = StringField("Title",validators=[DataRequired(),Length(max=100)])
    message = TextAreaField("Message", validators=[DataRequired(), Length(max=1000)])
    image = FileField("Attach Image (Optional)",validators=[validators.Optional(),
                                        FileAllowed(['jpg', 'gif', 'jpeg', 'png'], 'Please choose jpg, png or gif!'),
                                        FileSize(max_size=2*1024*1024, message="File must be under 2MB")
                                        ])
    shareable_msg = BooleanField("Make Message Shareable")
    submit = SubmitField("Send Message")
