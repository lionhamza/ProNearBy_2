from flask import Blueprint, render_template, request, redirect, url_for, flash
# in views.py
from .models import User, Post, ServiceRequest, Message as MessageModel, Like,QuoteRequest
from flask_login import login_required, current_user
from . import db
from flask import session
from datetime import datetime
from flask import jsonify
from . import mail
admin = Blueprint('admin', __name__, url_prefix='/admin')
views = Blueprint('views', __name__)

import random
from sqlalchemy.orm import joinedload

from .models import Like  # make sure Like is imported

@views.route('/')
def Base():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_get'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    # ✅ Unread messages count
    unread_messages_count = MessageModel.query.filter_by(
        receiver_id=user_id,
        is_read=False
    ).count()

    # ✅ Pending service requests count
    pending_requests_count = ServiceRequest.query.filter_by(
        receiver_id=user_id
    ).count()

    service_requests = ServiceRequest.query.filter_by(receiver_id=user_id).order_by(ServiceRequest.created_at.desc()).all()

    # Fetch posts (excluding own)
    posts = Post.query.filter(Post.user_id != user_id).options(joinedload(Post.user)).all()
    random.shuffle(posts)

    liked_post_ids = [like.post_id for like in Like.query.filter_by(user_id=user_id).all()]

    return render_template(
        "home.html",
        user=user,
        posts=posts,
        service_requests=service_requests,
        liked_post_ids=liked_post_ids,
        unread_messages_count=unread_messages_count,   # 👈 pass to template
        pending_requests_count=pending_requests_count # 👈 pass to template
    )



from .models import Like  # if not already imported

@views.route('/profile/<int:user_id>')
def profile(user_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login_get'))

    current_user_id = session['user_id']
    profile_owner = User.query.get(user_id)  # rename from user → profile_owner

    posts = Post.query.filter_by(user_id=user_id).order_by(Post.timestamp.desc()).all()
    liked_post_ids = [like.post_id for like in Like.query.filter_by(user_id=current_user_id).all()]

    return render_template(
        "userProfile.html", 
        profile_owner=profile_owner,  # pass as profile_owner
        posts=posts, 
        current_user_id=current_user_id,
        liked_post_ids=liked_post_ids
    )

@views.route('/my_profile')
def my_profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_get'))

    user = User.query.get(session['user_id'])

    if not user:
        return redirect(url_for('auth.login_get'))

    if user.user_type == 'regular':
        return redirect(url_for('views.regular_user', user_id=user.ID))
    else:
        return redirect(url_for('views.profile', user_id=user.ID))


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
    files = request.files.getlist('post_media')  # matches input name

    media_paths = []

    for file in files:
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.root_path, 'static/uploads', filename)
            file.save(filepath)
            media_paths.append(f'uploads/{filename}')  # Save relative path for template

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
                     availability, rating, reviews, user_type, bio=None, image=None):
            self.ID = id
            self.Name = name
            self.Surname = surname
            self.Service = service
            self.Location = location
            self.Experience = experience
            self.availability = availability
            self.Rating = rating
            self.Reviews = reviews
            self.user_type = user_type  # ✅ now available in template
            self.Bio = bio
            self.Image = image

    search_query = request.args.get('search', '')
    location_query = request.args.get('location', '')

    # ✅ Only show certified and experienced professionals
    query = User.query.filter(User.user_type.in_(["certifiedPro", "experiencedPro"]))

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

    # Exclude the logged-in user
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
            user_type=u.user_type,  # ✅ passed in
            bio=u.Bio,
            image=u.Image if u.Image else "assets/defualtPP.png"  # ✅ fallback handled here
        ) for u in users
    ]

    return render_template("feed.html", professionals=professionals,
                           search=search_query, location=location_query)





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

from sqlalchemy import or_

@views.route('/messages', methods=['GET', 'POST'])
def messages():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_get'))

    current_user_id = session['user_id']
    selected_user_id = request.args.get('user_id', type=int)

    # Sending new message
    if request.method == 'POST':
        content = request.form['message']
        if selected_user_id and content.strip():
            new_message = MessageModel(
                sender_id=current_user_id,
                receiver_id=selected_user_id,
                content=content
            )
            db.session.add(new_message)
            db.session.commit()
            flash("Message sent!", "success")
            return redirect(url_for('views.messages', user_id=selected_user_id))

    # Conversation with selected user
    messages = []
    selected_user = None
    if selected_user_id:
        selected_user = User.query.get(selected_user_id)
        messages = MessageModel.query.filter(
            (MessageModel.sender_id == current_user_id) & (MessageModel.receiver_id == selected_user_id) |
            (MessageModel.sender_id == selected_user_id) & (MessageModel.receiver_id == current_user_id)
        ).order_by(MessageModel.timestamp).all()

        # Mark unread messages as read
        for msg in messages:
            if msg.receiver_id == current_user_id and not msg.is_read:
                msg.is_read = True
        db.session.commit()

    # 1️⃣ Users who have exchanged messages
    messaged_user_ids = db.session.query(MessageModel.sender_id).filter(
        MessageModel.receiver_id == current_user_id
    ).union(
        db.session.query(MessageModel.receiver_id).filter(
            MessageModel.sender_id == current_user_id
        )
    ).distinct().all()
    messaged_user_ids = [uid[0] for uid in messaged_user_ids if uid[0] != current_user_id]

    # 2️⃣ Users you are “connected” with (example: service requests sent/received)
    from .models import ServiceRequest
    connected_user_ids = db.session.query(ServiceRequest.sender_id).filter_by(
        receiver_id=current_user_id
    ).union(
        db.session.query(ServiceRequest.receiver_id).filter_by(
            sender_id=current_user_id
        )
    ).distinct().all()
    connected_user_ids = [uid[0] for uid in connected_user_ids if uid[0] != current_user_id]

    # Combine both sets
    final_user_ids = list(set(messaged_user_ids + connected_user_ids))

    # Fetch user objects
    users = User.query.filter(User.ID.in_(final_user_ids)).all()

    # Count unread messages
    unread_counts = {}
    for u in users:
        unread_counts[u.ID] = MessageModel.query.filter_by(
            sender_id=u.ID,
            receiver_id=current_user_id,
            is_read=False
        ).count()

    return render_template(
        'messages.html',
        users=users,
        selected_user=selected_user,
        messages=messages,
        unread_counts=unread_counts
    )

from flask_mail import Message

# Utility functions
def send_request_email_to_pro(pro_email, pro_name, service, request_id):
    """Notify pro about a new request."""
    msg = Message(
        subject="New Service Request on ProNearBy",
        recipients=[pro_email],
        body=f"""
Hi {pro_name},

You have received a new service request for: {service}.

👉 Please log in to your ProNearBy account to accept or decline the request:
{url_for('views.Base', _external=True)}

Best regards,  
ProNearBy Team
"""
    )
    mail.send(msg)


def send_decline_email_to_user(user_email, user_name, service):
    """Notify user their request was declined."""
    msg = Message(
        subject="Your Service Request was Declined - ProNearBy",
        recipients=[user_email],
        body=f"""
Hi {user_name},

Unfortunately, your service request for "{service}" was declined.  

👉 Please log in to ProNearBy to connect with other professionals who can help:
{url_for('views.feed', _external=True)}

Best regards,  
ProNearBy Team
"""
    )
    mail.send(msg)

def send_request_accepted_email_to_user(user_email, user_name, pro_name, request_obj):
    """Notify user that their request has been accepted by the pro."""
    msg = Message(
        subject="Your Service Request Has Been Accepted! - ProNearBy",
        recipients=[user_email],
        body=f"""
Hi {user_name},

Good news! {pro_name} has accepted your service request.

Here are the request details:
📍 Location: {request_obj.location}
📅 Date: {request_obj.preferred_date.strftime('%Y-%m-%d') if request_obj.preferred_date else 'N/A'}
⏰ Time: {request_obj.preferred_time.strftime('%H:%M') if request_obj.preferred_time else 'N/A'}
📝 Description: {request_obj.description}

👉 You can log in to your ProNearBy account to follow up and communicate directly:
{url_for('views.Base', _external=True)}

Best regards,  
The ProNearBy Team
"""
    )
    mail.send(msg)

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

@views.route('/request/<int:request_id>/accept', methods=['POST'])
@login_required
def accept_request(request_id):
    request_obj = ServiceRequest.query.get_or_404(request_id)

    if request_obj.receiver_id != session['user_id']:
        flash("Unauthorized action", "error")
        return redirect(url_for('views.Base'))

    # Build default message with request details
    default_msg = f"""
📍 Location: {request_obj.location}
📅 Date: {request_obj.preferred_date.strftime('%Y-%m-%d') if request_obj.preferred_date else 'N/A'}
⏰ Time: {request_obj.preferred_time.strftime('%H:%M') if request_obj.preferred_time else 'N/A'}
📝 Description: {request_obj.description}
"""

    msg = MessageModel(
        sender_id=request_obj.receiver_id,
        receiver_id=request_obj.sender_id,
        content=default_msg.strip()
    )
    db.session.add(msg)

    # ✅ Only update status instead of deleting
    request_obj.status = 'accepted'

    db.session.commit()

    # ✅ Send email to user
    user = User.query.get(request_obj.sender_id)
    pro = User.query.get(request_obj.receiver_id)
    if user and user.Email:
        send_request_accepted_email_to_user(
            user.Email,
            user.Name,
            pro.Name,
            request_obj
        )

    flash("Service request accepted. Details sent to user!", "success")
    return redirect(url_for('views.Base'))


@views.route('/request/<int:request_id>/decline', methods=['POST'])
def decline_request(request_id):
    request_obj = ServiceRequest.query.get_or_404(request_id)

    if request_obj.receiver_id != session['user_id']:
        flash("Unauthorized action", "error")
        return redirect(url_for('views.Base'))

    # Update status
    request_obj.status = 'declined'
    db.session.commit()

    # Send email to the User
    user = User.query.get(request_obj.sender_id)
    if user and user.Email:
        send_decline_email_to_user(user.Email, user.Name, request_obj.service)

    db.session.delete(request_obj)
    db.session.commit()

    flash("Service request declined. User notified.", "info")
    return redirect(url_for('views.Base'))

@views.route('/complete_request/<int:request_id>', methods=['POST'])
@login_required
def complete_request(request_id):
    request_obj = ServiceRequest.query.get_or_404(request_id)

    # Only the assigned pro (receiver_id) can complete
    if request_obj.receiver_id != current_user.ID:
        flash("You cannot mark this request as completed.", "danger")
        return redirect(url_for('views.Base'))

    request_obj.status = 'completed'
    db.session.commit()

    # TODO: send review request notification/email to customer
    flash("Service marked as completed. A review request has been sent to the customer.", "success")
    return redirect(url_for('views.Base'))



@views.route("/like/<int:post_id>", methods=["POST"])
def like_post(post_id):
    user_id = session.get("user_id")
    post = Post.query.get_or_404(post_id)
    
    existing_like = Like.query.filter_by(user_id=user_id, post_id=post_id).first()
    
    if existing_like:
        db.session.delete(existing_like)
        liked = False
    else:
        new_like = Like(user_id=user_id, post_id=post_id)
        db.session.add(new_like)
        liked = True

    db.session.commit()

    like_count = Like.query.filter_by(post_id=post_id).count()

    return jsonify({
        "success": True,
        "liked": liked,
        "like_count": like_count
    })

import os
import re
from flask import request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

import random
import string
import re
from flask import flash, redirect, url_for, request, current_app
from werkzeug.utils import secure_filename

from flask_mail import Message

import os

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


@views.route('/update_contact/<int:user_id>', methods=['POST'])
def update_contact(user_id):
    user = User.query.get_or_404(user_id)

    new_email = request.form.get('email').strip().lower()
    new_phone = request.form.get('cellphone').strip()

    email_changed = new_email != user.Email
    phone_changed = new_phone != user.CellPhone

    # Email validation
    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(email_regex, new_email):
        flash("Invalid email format.", "error")
        return redirect(url_for('views.Base'))

    # Check if new email already exists
    if email_changed:
        existing_user = User.query.filter_by(Email=new_email).first()
        if existing_user and existing_user.ID != user.ID:
            flash("This email is already in use by another account.", "error")
            return redirect(url_for('views.Base'))

    # Phone validation
    phone_regex = r"^\+?[0-9]{7,15}$"
    if not re.match(phone_regex, new_phone):
        flash("Invalid phone number format.", "error")
        return redirect(url_for('views.Base'))

    # Update contact details
    user.Email = new_email
    user.CellPhone = new_phone

    # Reset verification if changed
    if email_changed:
        user.is_email_verified = False
        code = generate_code()
        user.email_verification_code = code  # Make sure your User model has this column
        send_email_verification(new_email, code)

    if phone_changed:
        user.is_phone_verified = False
        # Optionally send SMS verification here

    # Handle profile picture upload
    if 'profile_pic' in request.files:
        file = request.files['profile_pic']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.root_path, 'static/uploads', filename)
            file.save(filepath)
            user.Image = f'uploads/{filename}'

    db.session.commit()

    if email_changed or phone_changed:
        flash("Please verify your updated contact information.", "warning")
        return redirect(url_for('views.verify_contact', user_id=user.ID))

    flash("Contact info updated successfully.", "success")
    return redirect(url_for('views.Base'))



@views.route('/regular_profile/<int:user_id>')
def regular_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('regular_user.html', user=user)

@views.route('/edit_contact_info/<int:user_id>')
def edit_contact_info(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('edit_contact_info.html', user=user)

@views.route('/verify_contact/<int:user_id>')
def verify_contact(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('verify.html', user=user)


@views.route('/request_quote', methods=['POST'])
@login_required
def request_quote():
    # Get form data
    receiver_id = request.form.get('receiver_id')
    project_title = request.form.get('project_title')
    details = request.form.get('details')
    location = request.form.get('location')  # optional
    preferred_date = request.form.get('preferred_date')  # optional
    preferred_time = request.form.get('preferred_time')  # optional

    # Handle optional file upload
    attachment_file = request.files.get('attachment')
    attachment_filename = None
    if attachment_file and attachment_file.filename != '':
        attachment_filename = f"uploads/{attachment_file.filename}"
        attachment_file.save(os.path.join('static', attachment_filename))

    # Create new QuoteRequest
    new_quote = QuoteRequest(
        sender_id=current_user.ID,
        receiver_id=receiver_id,
        project_title=project_title,
        details=details,
        location=location,
        attachment=attachment_filename,
        preferred_date=preferred_date if preferred_date else None,
        preferred_time=preferred_time if preferred_time else None
    )

    db.session.add(new_quote)
    db.session.commit()

    flash("Quote request sent to pro!", "success")
    return redirect(url_for('views.dashboard'))
