from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from .models import User
from . import db
import secrets
import requests
from urllib.parse import urlencode

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET'])
def login_get():
    return render_template("login.html")

@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(Email=email).first()
    print("Typed password:", repr(password))
    if not user:
        flash("No user found with that email.", "error")
        return redirect(url_for('auth.login_get'))

    if password != user.Password:
        flash("Incorrect password", "error")
        return redirect(url_for('auth.login_get'))
         
    session['user_id'] = user.ID
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
        
        session['user_id'] = user.ID
        return redirect(url_for('views.Base'))
        
    except Exception as e:
        print(f"Google OAuth callback error: {e}")
        flash("Google login failed. Please try again.", "error")
        return redirect(url_for('auth.login_get'))

@auth.route('/signup', methods=['GET'])
def signup_get():
    return render_template('signUp.html')

@auth.route('/signup', methods=['POST'])
def signup_post():
    name = request.form['name']
    surname = request.form['surname']
    email = request.form['email']
    contact = request.form['contact']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    
    if password != confirm_password:
        flash("Passwords do not match", "error")
        return redirect(url_for('auth.signup_get'))

    existing_user = User.query.filter_by(Email=email).first()
    if existing_user:
        flash("Email already registered", "error")
        return redirect(url_for('auth.signup_get'))

    new_user = User(Name=name, Surname=surname, Email=email, CellPhone=contact, Password=password)
    db.session.add(new_user)
    db.session.commit()

    flash("Account created! You can now sign in.", "success")
    return redirect(url_for('auth.login_get'))

@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login_get'))
