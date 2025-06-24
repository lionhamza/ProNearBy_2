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

import os
from werkzeug.utils import secure_filename
from flask import current_app

@views.route('/profile/<int:user_id>/update', methods=['POST'])
def update_profile(user_id):
    user = User.query.get_or_404(user_id)

    # Update text fields
    user.Bio = request.form['bio']
    user.Location = request.form['location']
    user.Experience = request.form['experience']
    user.CellPhone = request.form['cellphone']
    user.Email = request.form['email']
    user.availability = request.form['availability']

    # Handle profile picture upload
    if 'profile_pic' in request.files:
        file = request.files['profile_pic']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.root_path, 'static/uploads', filename)
            file.save(filepath)
            user.Image = f'uploads/{filename}'  # Save path relative to /static/

    if 'cover_pic' in request.files:
        file=request.files['cover_pic']
        if file and file.filename !='':
            filename=secure_filename(file.filename)
            filepath=os.path.join(current_app.root_path,'static/uploads',filename)
            file.save(filepath)
            user.CoverImage=f'uploads/{filename}'
    db.session.commit()
    flash('Profile successfully updated!', 'success')
    return redirect(url_for('views.profile', user_id=user_id))
