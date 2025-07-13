from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import User , Post , ServiceRequest,Message
from . import db
from flask import session
from datetime import datetime

views = Blueprint('views', __name__)

import random
from sqlalchemy.orm import joinedload

@views.route('/')
def Base():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_get'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    # Only fetch requests sent to this professional
    service_requests = ServiceRequest.query.filter_by(receiver_id=user_id).order_by(ServiceRequest.created_at.desc()).all()

    # ✅ Fetch posts (excluding own posts if needed)
    posts = Post.query.filter(Post.user_id != user_id).options(joinedload(Post.user)).order_by(Post.timestamp.desc()).all()


    return render_template("home.html", user=user, posts=posts, service_requests=service_requests)


@views.route('/profile/<int:user_id>')
def profile(user_id):
    user = User.query.get_or_404(user_id)
    current_user_id = session.get('user_id')
    return render_template("userProfile.html", user=user, current_user_id=current_user_id)


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
            self.Image = image  # NOTE: it's now 'uploads/filename.jpg'

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

    # ✅ Exclude the currently logged-in user from results
    if 'user_id' in session:
        query = query.filter(User.ID != session['user_id'])

    users = query.all()

    professionals = [
        MockPro(
            id=u.ID,
            name=u.Name,
            surname=u.Surname,
            service=u.Service,
            location=u.Location,
            experience=u.Experience,
            availability=u.availability,
            rating=u.Rating or 0.0,
            reviews=u.Reviews or 0,
            bio=u.Bio,
            image=f'uploads/{u.Image}' if u.Image else None
        ) for u in users
    ]

    return render_template("feed.html", professionals=professionals, 
                           search=search_query, location=location_query)


@views.route('/request_service', methods=['POST'])
def request_service():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_get'))

    sender_id = session['user_id']
    receiver_id = request.form['receiver_id']
    service = request.form['service']
    service_type = request.form.get('service_type')
    location = request.form['location']
    description = request.form['description']
    preferred_date = request.form.get('preferred_date')
    preferred_time = request.form.get('preferred_time')

    # Handle image upload
    image_file = request.files.get('image')
    image_filename = None

    if image_file and image_file.filename != '':
        from werkzeug.utils import secure_filename
        import os

        upload_folder = os.path.join('static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)

        filename = secure_filename(image_file.filename)
        filepath = os.path.join(upload_folder, filename)
        image_file.save(filepath)
        image_filename = f"uploads/{filename}"  # saved path in DB

    new_request = ServiceRequest(
        sender_id=sender_id,
        receiver_id=receiver_id,
        service=service,
        service_type=service_type,
        location=location,
        description=description,
        image=image_filename,
        preferred_date=datetime.strptime(preferred_date, '%Y-%m-%d').date() if preferred_date else None,
        preferred_time=datetime.strptime(preferred_time, '%H:%M').time() if preferred_time else None
    )

    db.session.add(new_request)
    db.session.commit()
    flash('Service request sent successfully!', 'success')
    return redirect(request.referrer or url_for('views.feed'))

@views.app_context_processor
def inject_service_requests():
    from .models import ServiceRequest, User

    if 'user_id' not in session:
        return {}

    pro_id = session['user_id']

    # Requests where this user is the professional (receiver)
    service_requests = ServiceRequest.query.filter_by(receiver_id=pro_id).order_by(ServiceRequest.created_at.desc()).all()


    # Load sender details (who sent the request)
    for request in service_requests:
        request.sender = User.query.get(request.sender_id)

    return {'service_requests': service_requests}


from flask import session, request, redirect, url_for, render_template, flash
from sqlalchemy import or_

@views.route('/messages', methods=['GET', 'POST'])
def messages():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_get'))

    current_user_id = session['user_id']
    selected_user_id = request.args.get('user_id', type=int)

    # Handle message sending
    if request.method == 'POST':
        content = request.form['message']
        if selected_user_id and content.strip():
            new_message = Message(
                sender_id=current_user_id,
                receiver_id=selected_user_id,
                content=content
            )
            db.session.add(new_message)
            db.session.commit()
            flash("Message sent!", "success")
            return redirect(url_for('views.messages', user_id=selected_user_id))

    # Fetch conversation
    messages = []
    selected_user = None
    if selected_user_id:
        selected_user = User.query.get(selected_user_id)
        messages = Message.query.filter(
            or_(
                (Message.sender_id == current_user_id) & (Message.receiver_id == selected_user_id),
                (Message.sender_id == selected_user_id) & (Message.receiver_id == current_user_id)
            )
        ).order_by(Message.timestamp).all()

    # ✅ Only show users who have exchanged messages (accepted requests)
    from sqlalchemy import distinct
    messaged_user_ids = db.session.query(distinct(Message.sender_id)).filter(Message.receiver_id == current_user_id).union(
        db.session.query(distinct(Message.receiver_id)).filter(Message.sender_id == current_user_id)
    ).all()
    messaged_user_ids = [uid[0] for uid in messaged_user_ids]
    other_users = User.query.filter(User.ID.in_(messaged_user_ids)).all()

    return render_template('messages.html', 
                           users=other_users, 
                           selected_user=selected_user,
                           messages=messages)


@views.route('/request/<int:request_id>/accept', methods=['POST'])
def accept_request(request_id):
    request_obj = ServiceRequest.query.get_or_404(request_id)

    # Only the receiver can accept
    if request_obj.receiver_id != session['user_id']:
        flash("Unauthorized action", "error")
        return redirect(url_for('views.Base'))

    # Send default message with request details
    default_msg = f"""
📍 Location: {request_obj.location}
📅 Date: {request_obj.preferred_date.strftime('%Y-%m-%d') if request_obj.preferred_date else 'N/A'}
⏰ Time: {request_obj.preferred_time.strftime('%H:%M') if request_obj.preferred_time else 'N/A'}
📝 Description: {request_obj.description}
"""

    msg = Message(
        sender_id=request_obj.receiver_id,
        receiver_id=request_obj.sender_id,
        content=default_msg.strip()
    )
    db.session.add(msg)

    # Delete the request (optional: or mark it as 'accepted' if you want to track)
    db.session.delete(request_obj)
    db.session.commit()
    flash("Service request accepted. Details sent to user!", "success")
    return redirect(url_for('views.Base'))


@views.route('/request/<int:request_id>/decline', methods=['POST'])
def decline_request(request_id):
    request_obj = ServiceRequest.query.get_or_404(request_id)

    if request_obj.receiver_id != session['user_id']:
        flash("Unauthorized action", "error")
        return redirect(url_for('views.Base'))

    db.session.delete(request_obj)
    db.session.commit()
    flash("Service request declined and removed.", "info")
    return redirect(url_for('views.Base'))
