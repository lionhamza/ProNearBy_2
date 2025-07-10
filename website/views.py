from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import User , Post
from . import db
from flask import session

views = Blueprint('views', __name__)

import random
from sqlalchemy.orm import joinedload

@views.route('/')
def Base():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_get'))

    user = User.query.get(session['user_id'])

    # Load all posts and eager-load the user who made each post
    posts = Post.query.options(joinedload(Post.user)).all()
    random.shuffle(posts)

    return render_template("home.html", user=user, posts=posts)



@views.route('/profile/<int:user_id>')
def profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template("userProfile.html", user=user)

@views.route('/login')
def login():
    return render_template("login.html")


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
    #user.CellPhone = request.form['cellphone']
    #user.Email = request.form['email']
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




#this for adding a post
@views.route('/profile/<int:user_id>/post', methods=['POST'])
def create_post(user_id):
    user = User.query.get_or_404(user_id)
    content = request.form['content']
    files = request.files.getlist('post_media')

    media_paths = []

    for file in files:
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.root_path, 'static/uploads', filename)
            file.save(filepath)
            media_paths.append(f'uploads/{filename}')  # Save relative path

    new_post = Post(content=content, media=media_paths, user=user)
    db.session.add(new_post)
    db.session.commit()

    flash('Post created with media!', 'success')
    return redirect(url_for('views.profile', user_id=user_id))


@views.route('/feed', methods=['GET'])
def feed():
    search_query = request.args.get('search', '')
    location_query = request.args.get('location', '')
    
    query = User.query
    
    if search_query:
        query = query.filter(
            db.or_(
                User.Service.ilike(f'%{search_query}%'),
                User.Name.ilike(f'%{search_query}%'),
                User.Surname.ilike(f'%{search_query}%')
            )
        )
    
    if location_query:
        query = query.filter(User.Location.ilike(f'%{location_query}%'))
    
    professionals = query.all()
    return render_template("feed.html", professionals=professionals, search=search_query, location=location_query)


@views.route('/mock-feed', methods=['GET'])
def mock_feed():
    from flask import request
    
    # Create mock professionals data
    class MockPro:
        def __init__(self, id, name, surname, service, location, experience, 
                     availability, rating, reviews, bio=None, image=None):
            self.ID = id
            self.Name = name
            self.Surname = surname
            self.Service = service
            self.Location = location
            self.Experience = experience
            self.availability = availability
            self.Rating = rating
            self.Reviews = reviews
            self.Bio = bio
            self.Image = image

    professionals = [
        MockPro(1, "John", "Doe", "Electrician", "Pretoria, South Africa", 
                "5+ years", "Mon-Fri, 8am-5pm", 4.7, 88, 
                "Helping homes stay bright and safe", "assets/electrician.jpg"),
        MockPro(2, "Jane", "Smith", "Plumber", "Johannesburg, South Africa", 
                "6+ years", "Mon-Sat, 7am-6pm", 4.8, 95, 
                "Fixing leaks with expertise and precision", None),
        MockPro(3, "Michael", "Johnson", "Carpenter", "Cape Town, South Africa", 
                "10+ years", "Weekdays only", 4.9, 120, 
                "Quality woodwork and home repairs", None),
        MockPro(4, "Sarah", "Williams", "Painter", "Durban, South Africa", 
                "4+ years", "All week, 9am-7pm", 4.6, 72, 
                "Adding color to your life with professional painting services", None)
    ]
    
    search_query = request.args.get('search', '')
    location_query = request.args.get('location', '')
    
    # Filter professionals based on search query if provided
    if search_query:
        professionals = [p for p in professionals if 
                         search_query.lower() in p.Name.lower() or 
                         search_query.lower() in p.Surname.lower() or 
                         search_query.lower() in p.Service.lower()]
    
    # Filter by location if provided
    if location_query:
        professionals = [p for p in professionals if 
                         location_query.lower() in p.Location.lower()]
    
    return render_template("feed.html", professionals=professionals, 
                          search=search_query, location=location_query)