from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from .models import User,Admin
from . import db
import secrets
import requests
from urllib.parse import urlencode
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
import os
from datetime import datetime
from . import db
from .models import ProRegistrationRequest
import uuid
import os
from flask_mail import Message
from . import mail
from twilio.rest import Client
import re
import random
import string
from flask_login import current_user, login_required
from flask_login import login_user

auth = Blueprint('auth', __name__)



@auth.route('/login', methods=['GET'])
def login_get():
    return render_template("login.html")

from werkzeug.security import check_password_hash, generate_password_hash

@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form['username'].strip().lower()
    password = request.form['password']

    # Try to find Admin first
    account = Admin.query.filter_by(email=email).first()
    is_admin = True

    # If no admin found, check User
    if not account:
        account = User.query.filter_by(Email=email).first()
        is_admin = False

    if not account:
        flash("No account found with that email.", "error")
        return redirect(url_for('auth.login_get'))

    # Compare password (replace with check_password_hash if passwords are hashed)
    stored_password = account.password if is_admin else account.Password
    if password != stored_password:
        flash("Incorrect password", "error")
        return redirect(url_for('auth.login_get'))

    # Email verification for normal users
    if not is_admin and not account.is_email_verified:
        flash("Please verify your email before logging in.", "error")
        return redirect(url_for('auth.login_get'))

    # Login successful
    if is_admin:
        session['admin_id'] = account.id
        flash("Logged in as Admin!", "success")
        return redirect(url_for('admin.dashboard'))
    else:
        session['user_id'] = account.ID
        login_user(account)  # ← FIXED: pass the actual user object
        flash("Logged in successfully!", "success")
        return redirect(url_for('views.Base'))




# Google OAuth routes
@auth.route('/login/google')
def google_login():
    # Manual Google OAuth URL construction
    redirect_uri = url_for('auth.google_callback', _external=True)
    
    params = {
        'client_id': current_app.config['GOOGLE_CLIENT_ID'],
        'redirect_uri': redirect_uri,
        'scope': 'openid email profile',
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'select_account'
    }
    
    auth_url = 'https://accounts.google.com/o/oauth2/auth?' + urlencode(params)
    return redirect(auth_url)

@auth.route('/callback/google')
def google_callback():
    try:
        # Get the authorization code from Google
        code = request.args.get('code')
        if not code:
            flash("Google login was cancelled.", "error")
            return redirect(url_for('auth.login_get'))

        # Exchange code for access token
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'client_id': current_app.config['GOOGLE_CLIENT_ID'],
            'client_secret': current_app.config['GOOGLE_CLIENT_SECRET'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': url_for('auth.google_callback', _external=True)
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if 'access_token' not in token_json:
            print(f"Token error: {token_json}")
            flash("Google login failed. Please try again.", "error")
            return redirect(url_for('auth.login_get'))

        # Get user info using access token
        user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        headers = {'Authorization': f'Bearer {token_json["access_token"]}'}
        user_response = requests.get(user_info_url, headers=headers)
        user_info = user_response.json()
        
        if 'email' not in user_info:
            print(f"User info error: {user_info}")
            flash("Could not retrieve user information from Google.", "error")
            return redirect(url_for('auth.login_get'))

        # Process user information
        email = user_info['email']
        name = user_info.get('given_name', '')
        surname = user_info.get('family_name', '')
        
        print(f"Google user info: {user_info}")  # Debug info
        
        # Check if user exists
        user = User.query.filter_by(Email=email).first()
        
        if not user:
            # Create new user with Google info
            user = User(
                Name=name,
                Surname=surname,
                Email=email,
                Password=secrets.token_urlsafe(20)  # Random password for Google users
            )
            db.session.add(user)
            db.session.commit()
            flash(f"Welcome {name}! Your account has been created with Google.", "success")
        else:
            flash(f"Welcome back {user.Name}! Logged in with Google.", "success")
        
        # ✅ Log user in with Flask-Login
        login_user(user)

        # (optional) keep session['user_id'] if you still use it elsewhere
        session['user_id'] = user.ID

        return redirect(url_for('views.Base'))
        
    except Exception as e:
        print(f"Google OAuth callback error: {e}")
        flash("Google login failed. Please try again.", "error")
        return redirect(url_for('auth.login_get'))



# --------------------------
# Helpers
# --------------------------
def generate_code(length=6):
    """Generate a numeric verification code."""
    return ''.join(random.choices(string.digits, k=length))

def send_email_verification(email, code):
    """Send verification code to user's email."""
    msg = Message(
        subject="Your ProNearBy Email Verification Code",
        recipients=[email],
        body=f"Your verification code is: {code}"
    )
    mail.send(msg)

# --------------------------
# Signup Routes
# --------------------------
@auth.route('/signup', methods=['GET'])
def signup_get():
    return render_template('signUp.html')

@auth.route('/signup', methods=['POST'])
def signup_post():
    name = request.form['name'].strip()
    surname = request.form['surname'].strip()
    email = request.form['email'].strip().lower()
    contact = request.form['contact'].strip()
    password = request.form['password']
    confirm_password = request.form['confirm_password']

    # Password match check
    if password != confirm_password:
        flash("Passwords do not match", "error")
        return render_template("signUp.html", name=name, surname=surname, email=email, contact=contact)

    # Email validation
    email_regex = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    if not re.match(email_regex, email):
        flash("Invalid email format", "error")
        return render_template("signUp.html", name=name, surname=surname, email=email, contact=contact)

    # Contact number validation
    phone_regex = r"^\d{10}$"
    if not re.match(phone_regex, contact):
        flash("Invalid contact number. Must be 10 digits.", "error")
        return render_template("signUp.html", name=name, surname=surname, email=email, contact=contact)

    # Check for duplicates
    if User.query.filter_by(Email=email).first():
        flash("Email already registered", "error")
        return render_template("signUp.html", name=name, surname=surname, email=email, contact=contact)

    if User.query.filter_by(CellPhone=contact).first():
        flash("Contact number already registered", "error")
        return render_template("signUp.html", name=name, surname=surname, email=email, contact=contact)

    # Save new user (email verification pending)
    new_user = User(
        Name=name,
        Surname=surname,
        Email=email,
        CellPhone=contact,
        Password=password,  # TODO: hash password
        is_email_verified=False,
        is_phone_verified=False
    )
    db.session.add(new_user)
    db.session.commit()

    # Generate email verification code
    email_code = generate_code()
    session['pending_user_id'] = new_user.ID
    session['pending_email'] = new_user.Email
    session['email_code'] = email_code

    # Send email code
    send_email_verification(email, email_code)

    flash("Account created! Please verify your email.", "info")
    return redirect(url_for('auth.verify_page'))

# --------------------------
# Verification Routes
# --------------------------
@auth.route('/verify', methods=['GET'])
def verify_page():
    """Show form to enter email verification code."""
    if 'pending_user_id' not in session:
        flash("No user pending verification.", "error")
        return redirect(url_for('auth.signup_get'))
    return render_template('verify.html')

@auth.route('/verify_email', methods=['POST'])
def verify_email():
    entered_code = request.form['code']
    if entered_code == session.get('email_code'):
        user = User.query.filter_by(Email=session.get('pending_email')).first()
        if user:
            user.is_email_verified = True
            db.session.commit()
            flash("Email verified successfully!", "success")
            # Clean up session
            session.pop('pending_user_id', None)
            session.pop('pending_email', None)
            session.pop('email_code', None)
        return redirect(url_for('auth.login_get'))
    flash("Invalid verification code", "error")
    return redirect(url_for('auth.verify_page'))




@auth.route('/register/pro_type')
def choose_pro_type():
    return render_template('choose_pro_type.html')

@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login_get'))





ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'mp4', 'mov', 'webm'}


import re
import json
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from flask import flash, redirect, render_template, request, url_for
from .models import ProRegistrationRequest
from . import db
import os

UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')

def save_file(file, subfolder):
    if file and file.filename != '':
        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        filename = secure_filename(unique_name)
        
        folder_path = os.path.join(UPLOAD_FOLDER, subfolder)
        os.makedirs(folder_path, exist_ok=True)
        
        filepath = os.path.join(folder_path, filename)
        file.save(filepath)
        
        # Return relative path for DB or HTML usage
        return f'uploads/{subfolder}/{filename}'
    return None



@auth.route('/register/certified', methods=['GET', 'POST'])

def register_certified():
    if request.method == 'POST':
        if current_user.is_authenticated:
            # Auto-fill from logged-in user
            form_data = {
                'name': current_user.Name,
                'surname': current_user.Surname,
                'email': current_user.Email,
                'contact': current_user.CellPhone,
                'service': request.form.get('service', '').strip(),
                'experience': request.form.get('experience', '').strip(),
                'availability': request.form.get('availability', '').strip(),
                'location': request.form.get('location', '').strip()
            }
            password = None
            confirm_password = None
        else:
            # Normal flow
            form_data = {
                'name': request.form.get('name', '').strip(),
                'surname': request.form.get('surname', '').strip(),
                'email': request.form.get('email', '').strip().lower(),
                'contact': request.form.get('contact', '').strip(),
                'service': request.form.get('service', '').strip(),
                'experience': request.form.get('experience', '').strip(),
                'availability': request.form.get('availability', '').strip(),
                'location': request.form.get('location', '').strip()
            }
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')

        # Validation (skip name/email/password if logged in)
        if not current_user.is_authenticated:
            if not re.match(r"^[A-Za-z]{2,50}$", form_data['name']):
                flash("First name must contain only letters and be 2–50 characters.", "error")
                return render_template('register_certified.html', form_data=form_data)

            if not re.match(r"^[A-Za-z]{2,50}$", form_data['surname']):
                flash("Surname must contain only letters and be 2–50 characters.", "error")
                return render_template('register_certified.html', form_data=form_data)

            if not re.match(r"^[^@]+@[^@]+\.[^@]+$", form_data['email']):
                flash("Invalid email address format.", "error")
                return render_template('register_certified.html', form_data=form_data)

            if not re.match(r"^(\+27|0)[0-9]{9}$", form_data['contact']):
                flash("Invalid contact number. Example: +27831234567 or 0831234567", "error")
                return render_template('register_certified.html', form_data=form_data)

            if password != confirm_password:
                flash("Passwords do not match.", "error")
                return render_template('register_certified.html', form_data=form_data)

            if not re.match(r"^(?=.*[A-Z])(?=.*\d).{8,}$", password):
                flash("Password must have at least 8 characters, one uppercase letter, and one number.", "error")
                return render_template('register_certified.html', form_data=form_data)

        if len(form_data['service']) < 2 or len(form_data['experience']) < 1 or len(form_data['availability']) < 2 or len(form_data['location']) < 2:
            flash("All service details must be filled out correctly.", "error")
            return render_template('register_certified.html', form_data=form_data)

        existing_request = ProRegistrationRequest.query.filter(
            (ProRegistrationRequest.email == form_data['email']) |
            (ProRegistrationRequest.contact == form_data['contact'])
        ).first()
        if existing_request:
            flash("A registration request with this email or contact already exists.", "error")
            return render_template('register_certified.html', form_data=form_data)

        # Handle file uploads
        id_doc_path = save_file(request.files.get('id_doc'), 'uploads/id_docs')
        cert_doc_path = save_file(request.files.get('cert_doc'), 'uploads/cert_docs')

        portfolio_paths = []
        for f in request.files.getlist('portfolio_files'):
            path = save_file(f, 'uploads/portfolio')
            if path:
                portfolio_paths.append(path)

        intro_video_path = save_file(request.files.get('intro_video'), 'uploads/videos')

        # Hash password only if new user
        hashed_password = generate_password_hash(password) if password else current_user.Password

        # Create new ProRegistrationRequest
        new_request = ProRegistrationRequest(
            name=form_data['name'],
            surname=form_data['surname'],
            email=form_data['email'],
            contact=form_data['contact'],
            password=hashed_password,
            service=form_data['service'],
            experience=form_data['experience'],
            availability=form_data['availability'],
            location=form_data['location'],
            id_doc=id_doc_path,
            cert_doc=cert_doc_path,
            portfolio_files=json.dumps(portfolio_paths),
            intro_video=intro_video_path,
            is_certified=True,
            status='pending'
        )

        db.session.add(new_request)
        db.session.commit()

        # Generate and send email verification code
        if not current_user.is_authenticated:
            email_code = generate_code()
            session['pending_user_id'] = new_request.id
            session['pending_email'] = new_request.email
            session['email_code'] = email_code
            send_email_verification(new_request.email, email_code)

        flash("Your registration request has been submitted for review.", "success")
        return redirect(url_for('auth.verify_page' if not current_user.is_authenticated else 'views.feed'))

    return render_template('register_certified.html', form_data={})


import re
import json
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from flask import flash, redirect, render_template, request, url_for
from .models import ProRegistrationRequest
from . import db
import os

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'mp4', 'mov', 'webm'}
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file, subfolder):
    if file and file.filename != '' and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        filename = secure_filename(unique_name)
        folder_path = os.path.join(UPLOAD_FOLDER, subfolder)
        os.makedirs(folder_path, exist_ok=True)
        filepath = os.path.join(folder_path, filename)
        file.save(filepath)
        return f'uploads/{subfolder}/{filename}'
    return None

@auth.route('/register/experienced', methods=['GET', 'POST'])
def register_experienced():
    if request.method == 'POST':
        if current_user.is_authenticated:
            # Auto-fill from logged-in user
            form_data = {
                'name': current_user.Name,
                'surname': current_user.Surname,
                'email': current_user.Email,
                'contact': current_user.CellPhone,
                'service': request.form.get('service', '').strip(),
                'experience': request.form.get('experience', '').strip(),
                'availability': request.form.get('availability', '').strip(),
                'location': request.form.get('location', '').strip()
            }
            password = None
            confirm_password = None
        else:
            # Normal flow
            form_data = {
                'name': request.form.get('name', '').strip(),
                'surname': request.form.get('surname', '').strip(),
                'email': request.form.get('email', '').strip().lower(),
                'contact': request.form.get('contact', '').strip(),
                'service': request.form.get('service', '').strip(),
                'experience': request.form.get('experience', '').strip(),
                'availability': request.form.get('availability', '').strip(),
                'location': request.form.get('location', '').strip()
            }
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')

        # Validations (skip name/email/password if logged in)
        if not current_user.is_authenticated:
            if not re.match(r"^[A-Za-z]{2,50}$", form_data['name']):
                flash("First name must contain only letters and be 2–50 characters.", "error")
                return render_template('register_experienced.html', form_data=form_data)

            if not re.match(r"^[A-Za-z]{2,50}$", form_data['surname']):
                flash("Surname must contain only letters and be 2–50 characters.", "error")
                return render_template('register_experienced.html', form_data=form_data)

            if not re.match(r"^[^@]+@[^@]+\.[^@]+$", form_data['email']):
                flash("Invalid email format.", "error")
                return render_template('register_experienced.html', form_data=form_data)

            if not re.match(r"^(\+27|0)[0-9]{9}$", form_data['contact']):
                flash("Invalid contact number format.", "error")
                return render_template('register_experienced.html', form_data=form_data)

            if password != confirm_password:
                flash("Passwords do not match.", "error")
                return render_template('register_experienced.html', form_data=form_data)

            if not re.match(r"^(?=.*[A-Z])(?=.*\d).{8,}$", password):
                flash("Password must have at least 8 characters, one uppercase letter, and one number.", "error")
                return render_template('register_experienced.html', form_data=form_data)

        if len(form_data['service']) < 2 or len(form_data['experience']) < 1 or len(form_data['location']) < 2:
            flash("Service, experience, and location must be filled in.", "error")
            return render_template('register_experienced.html', form_data=form_data)

        # Duplicate check
        existing_request = ProRegistrationRequest.query.filter(
            (ProRegistrationRequest.email == form_data['email']) |
            (ProRegistrationRequest.contact == form_data['contact'])
        ).first()
        if existing_request:
            flash("A registration request with this email or contact already exists.", "error")
            return render_template('register_experienced.html', form_data=form_data)

        # Handle file uploads
        id_doc_path = save_file(request.files.get('id_doc'), 'uploads/id_docs')
        if not id_doc_path:
            flash("Valid government ID (pdf/jpg/png) is required.", "error")
            return render_template('register_experienced.html', form_data=form_data)

        intro_video_path = save_file(request.files.get('intro_video'), 'uploads/videos')

        portfolio_paths = []
        portfolio_files = request.files.getlist('portfolio_files')
        for f in portfolio_files[:3]:
            path = save_file(f, 'uploads/portfolio')
            if path:
                portfolio_paths.append(path)
        if len(portfolio_files) > 3:
            flash("Only the first 3 portfolio files were uploaded.", "info")

        # Hash password only if new user
        hashed_password = generate_password_hash(password) if password else current_user.Password

        # Create new ProRegistrationRequest
        new_request = ProRegistrationRequest(
            name=form_data['name'],
            surname=form_data['surname'],
            email=form_data['email'],
            contact=form_data['contact'],
            password=hashed_password,
            service=form_data['service'],
            experience=form_data['experience'],
            availability=form_data['availability'],
            location=form_data['location'],
            id_doc=id_doc_path,
            intro_video=intro_video_path,
            portfolio_files=json.dumps(portfolio_paths),
            is_certified=False,
            status='pending',
            submitted_at=datetime.utcnow()
        )

        db.session.add(new_request)
        db.session.commit()

        # Generate and send email verification code if not logged in
        if not current_user.is_authenticated:
            email_code = generate_code()
            session['pending_user_id'] = new_request.id
            session['pending_email'] = new_request.email
            session['email_code'] = email_code
            send_email_verification(new_request.email, email_code)

        flash("Your registration request has been submitted for review.", "success")
        return redirect(url_for('auth.verify_page' if not current_user.is_authenticated else 'views.feed'))

    return render_template('register_experienced.html', form_data={})



@auth.route('/h', methods=['GET'])
def home():
    return render_template('index.html') 
