from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import User
from . import db

views = Blueprint('views', __name__)

@views.route('/')
def Base():
    return render_template("home.html")

@views.route('/profile/<int:user_id>')
def profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template("userProfile.html", user=user)

@views.route('/profile/<int:user_id>/update', methods=['POST'])
def update_profile(user_id):
    user = User.query.get_or_404(user_id)

    user.Bio = request.form['bio']
    user.Location = request.form['location']
    user.Experience = request.form['experience']
    user.CellPhone = request.form['cellphone']
    user.Email = request.form['email']
    user.availability = request.form['availability']

    db.session.commit()

    flash('Profile successfully updated!', 'success')  # <-- Flash message
    return redirect(url_for('views.profile', user_id=user_id))
