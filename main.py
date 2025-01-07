from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename
from gofilepy import GofileClient
import requests
import re

app = Flask(__name__)

# Spoo.me API endpoint and headers
url = "https://spoo.me"
headers = {
    "Accept": "application/json",
    "Content-Type": "application/x-www-form-urlencoded"
}

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# Flask config setup
app.config['SECRET_KEY'] = 'your_secret_key'

# Initialize Gofile client
client = GofileClient()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_password(password):
    if len(password) < 8:
        return False
    if not re.search(r'[a-zA-Z]', password):  
        return False
    if not re.search(r'\d', password):  
        return False
    if not re.search(r'[@.]', password):  
        return False
    if re.search(r'[@.]{2,}', password):  
        return False
    return True

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        short_name = request.form.get('short_name')
        password = request.form.get('password')
        file = request.files['file']

        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        # If the user does not select a file
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        # Validate password
        if password and not is_valid_password(password):
            flash("Password must be at least 8 characters long, contain a letter, a number, and a special character (@ or .), and not have consecutive special characters.")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            # Upload the file directly to GoFile without saving it locally
            gofile_response = client.upload(file=file)
            page_link = gofile_response.page_link

            # URL shortening logic
            shortened_url = None
            if short_name:
                # Prepare payload for the URL shortening API
                payload = {
                    "url": page_link,
                    "alias": short_name,  # Custom alias provided by the user
                    "max-clicks": 50,     # Optional max clicks
                    "password": password if password else "SuperStrongPassword@18322"  
                }

                response = requests.post(url, data=payload, headers=headers)

                if response.status_code == 200:
                    # Extract the shortened URL from the API response
                    shortened_url = response.json().get('short_url')
                else:
                    flash(f"Choose a different name for the URL.")

            return render_template('upload.html', shortened_url=shortened_url)

    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)
