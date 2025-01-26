import time
from flask import Flask, flash, render_template, redirect, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
import hashlib
from werkzeug.utils import secure_filename
from gofilepy import GofileClient
import requests
from form import RegistrationForm, LoginForm, UploadForm
from models import *
from sqlalchemy import *
from datetime import datetime
from pytz import timezone
import zipfile
from io import BytesIO
import os
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
tz = timezone("Asia/Kolkata")

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"  

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return db.session.execute(db.select(User).where(User.username == user_id)).scalar_one_or_none()

@app.template_filter('date')
def format_date(timestamp, fmt="%d-%m-%y %H:%M"):
    return datetime.fromtimestamp(timestamp, tz).strftime(fmt)

client = GofileClient()

url = "https://spoo.me"
headers = {
    "Accept": "application/json",
    "Content-Type": "application/x-www-form-urlencoded"
}
salt = "mysalt"


@app.route("/",methods=['GET',"POST"])
def home():
    return render_template('home.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = hashlib.sha256((form.password.data + salt).encode('utf-8')).hexdigest()
        user = User(
            username=form.username.data,
            fullname=form.fullname.data,
            email=form.email.data,
            password=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}! Go Login Now !', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).where(User.username == form.username.data)).scalar_one_or_none()
        hashed_password = hashlib.sha256((form.password.data + salt).encode('utf-8')).hexdigest()
        if user and hashed_password == user.password:
            login_user(user, remember=form.remember.data)
            flash('You have been logged in!', 'success')
            next = request.args.get('next')
            return redirect(next or url_for('upload'))
        else:
            flash("Login Unsuccessful, Please check Username and Password", "danger")
    return render_template('login.html', form=form)

@app.route('/upload',methods=['GET',"POST"])
def upload():
    return render_template('upload.html')

@app.route('/gofile', methods=['GET', 'POST'])
def uploadgofile():
    form = UploadForm()
    if form.validate_on_submit():
        timestamp = int(time.time())
        short_name = form.short_name.data
        password = form.password.data
        files = request.files.getlist('file')

        if not files or len(files) == 0:
            flash("No files selected for upload.", "danger")
            return render_template('upload.html', form=form)

        if len(files) > 1:
            # Package files into a ZIP archive
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file in files:
                    if file:
                        filename = secure_filename(file.filename)
                        zip_file.writestr(filename, file.read())
            zip_buffer.seek(0)
            upload_file = zip_buffer
        else:
            # Handle single file upload
            file = files[0]
            if not file:
                flash("Invalid file.", "danger")
                return render_template('upload.html', form=form)
            upload_file = file.stream

        # Upload the file (ZIP or single) to Gofile
        gofile_response = client.upload(file=upload_file)
        page_link = gofile_response.page_link

        shortened_url = None
        if short_name:
            payload = {
                "url": page_link,
                "alias": short_name,
            }
            if password:
                payload["password"] = password

            # Request the shortened URL
            response = requests.post(url, data=payload, headers=headers)

            if response.status_code == 200:
                shortened_url = response.json().get('short_url')
            else:
                flash("Error creating shortened URL. Please try a different name.")

        # Check if the user is authenticated
        if current_user.is_authenticated:
            # Store the URL in the database for authenticated users
            file_url = FileURL(url=page_link, shortened_url=shortened_url, timestamp=timestamp, user_id=current_user.username)
            db.session.add(file_url)
            db.session.commit()

        flash('File uploaded and URL created successfully!', 'success')
        return render_template('upload-gofile.html', form=form, shortened_url=shortened_url)

    return render_template('upload-gofile.html', form=form)


@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user
    current_page = request.args.get('page', 1, type=int)
    query = db.select(FileURL).where(FileURL.user_id == user.username).order_by(desc(FileURL.timestamp))
    user_files = db.paginate(query, page = current_page, per_page=10)
    page_list = user_files.iter_pages(left_edge=1,right_edge=1, left_current=2, right_current=2)

    if not user_files:
        flash("You have not uploaded any files yet.", "info")
    
    return render_template('dashboard.html', user=user, current_page=current_page, files=user_files, pagination=page_list)

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)