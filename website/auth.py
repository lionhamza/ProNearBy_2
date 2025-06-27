from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .models import User
from . import db


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

    # You should hash and verify passwords properly — simplified here
    if password !=user.Password:  # For testing, you can hardcode the password or match some logic
        flash("Incorrect password", "error")
        return redirect(url_for('auth.login_get'))
         
    session['user_id'] = user.ID  # Store user session
    flash("Logged in successfully!", "success")
    return redirect(url_for('views.Base'))  # Home page
 


@auth.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out successfully!", "success")
    return redirect(url_for('auth.login_get'))


#from flask import Blueprint, render_template, request, redirect, url_for, flash
#from .models import User


# Show sign-up page

@auth.route('/signup', methods=['GET'])
def signup_get():  # <- THIS NAME
    return render_template('signup.html')


# Handle form submission
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

    # Optional: check if email exists first
    existing_user = User.query.filter_by(Email=email).first()
    if existing_user:
        flash("Email already registered", "error")
        return redirect(url_for('auth.signup_get'))

    new_user = User(Name=name, Surname=surname, Email=email, CellPhone=contact, Password=password)
    db.session.add(new_user)
    db.session.commit()

    flash("Account created! You can now sign in.", "success")
    return redirect(url_for('auth.login_get'))
