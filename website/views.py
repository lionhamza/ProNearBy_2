from sqlalchemy import func
from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import User, Post, ServiceRequest, Message as MessageModel, Like, QuoteRequest
from flask_login import login_required, current_user
from . import db
from flask import session
from datetime import datetime
from flask import jsonify
from flask_mail import Message
from . import mail
import math
import os
import re
import random
import string
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, and_
from werkzeug.utils import secure_filename
from flask import current_app

admin = Blueprint('admin', __name__, url_prefix='/admin')
views = Blueprint('views', __name__)

from .models import Like


# ──────────────────────────────────────────────
#  UTILITY: Haversine distance (returns km)
# ──────────────────────────────────────────────

def haversine_km(lat1, lon1, lat2, lon2):
    """Returns distance in km between two lat/lon points using the Haversine formula."""
    R = 6371  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


# ──────────────────────────────────────────────
#  UTILITY: File helpers
# ──────────────────────────────────────────────

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ──────────────────────────────────────────────
#  UTILITY: Verification code + email
# ──────────────────────────────────────────────

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


# ──────────────────────────────────────────────
#  UTILITY: Email notification helpers
# ──────────────────────────────────────────────

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
{url_for('views.mock_feed', _external=True)}

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


# ──────────────────────────────────────────────
#  ROUTES
# ──────────────────────────────────────────────

@views.route('/')
def Base():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_get'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    unread_messages_count = MessageModel.query.filter_by(
        receiver_id=user_id,
        is_read=False
    ).count()

    if user.user_type == "professional":
        pending_requests_count = ServiceRequest.query.filter_by(
            receiver_id=user_id
        ).count()
    else:
        pending_requests_count = ServiceRequest.query.filter_by(
            sender_id=user_id
        ).count()

    posts = Post.query.filter(Post.user_id != user_id).options(joinedload(Post.user)).all()
    random.shuffle(posts)

    liked_post_ids = [like.post_id for like in Like.query.filter_by(user_id=user_id).all()]

    return render_template(
        "home.html",
        user=user,
        posts=posts,
        liked_post_ids=liked_post_ids,
        unread_messages_count=unread_messages_count,
        pending_requests_count=pending_requests_count
    )


@views.route('/profile/<int:user_id>')
def profile(user_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login_get'))

    current_user_id = session['user_id']
    profile_owner = User.query.get(user_id)

    posts = Post.query.filter_by(user_id=user_id).order_by(Post.timestamp.desc()).all()
    liked_post_ids = [like.post_id for like in Like.query.filter_by(user_id=current_user_id).all()]

    return render_template(
        "userProfile.html",
        profile_owner=profile_owner,
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


@views.route('/profile/<int:user_id>/update', methods=['POST'])
def update_profile(user_id):
    user = User.query.get_or_404(user_id)

    user.Bio = request.form['bio']
    user.Location = request.form['location']
    user.Experience = request.form['experience']
    user.availability = request.form['availability']

    if 'profile_pic' in request.files:
        file = request.files['profile_pic']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.root_path, 'static/uploads', filename)
            file.save(filepath)
            user.Image = f'uploads/{filename}'

    if 'cover_pic' in request.files:
        file = request.files['cover_pic']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.root_path, 'static/uploads', filename)
            file.save(filepath)
            user.CoverImage = f'uploads/{filename}'

    db.session.commit()
    flash('Profile successfully updated!', 'success')
    return redirect(url_for('views.profile', user_id=user_id))


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
            media_paths.append(f'uploads/{filename}')

    new_post = Post(content=content, media=media_paths, user=user)
    db.session.add(new_post)
    db.session.commit()

    flash('Post created with media!', 'success')
    return redirect(url_for('views.profile', user_id=user_id))


@views.route('/mock-feed', methods=['GET'])
def mock_feed():

    class MockPro:
        def __init__(self, id, name, surname, service, location, experience,
                     availability, rating, reviews, user_type, bio=None, image=None, distance=None):
            self.ID = id
            self.Name = name
            self.Surname = surname
            self.Service = service
            self.Location = location
            self.Experience = experience
            self.availability = availability
            self.Rating = rating
            self.Reviews = reviews
            self.user_type = user_type
            self.Bio = bio or ""
            self.Image = image or "assets/defaultPP.png"
            self.Distance = distance

            # ETA in minutes based on real km distance
            if distance is not None:
                average_speed_kmh = 50
                self.ETA_minutes = round((distance / average_speed_kmh) * 60)
            else:
                self.ETA_minutes = None

    search_query = request.args.get('search', '').strip()
    location_query = request.args.get('location', '').strip()
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)

    # Base query — distance is NOT computed in SQL
    query = User.query.filter(User.user_type.in_(["certifiedPro", "experiencedPro"]))

    if search_query:
        query = query.filter(
            db.or_(
                User.Service.ilike(f"%{search_query}%"),
                User.Name.ilike(f"%{search_query}%"),
                User.Surname.ilike(f"%{search_query}%")
            )
        )

    if 'user_id' in session:
        query = query.filter(User.ID != session['user_id'])

    users = query.all()

    professionals = []
    for u in users:
        dist = None
        if lat is not None and lng is not None and u.Latitude and u.Longitude:
            dist = round(haversine_km(lat, lng, u.Latitude, u.Longitude), 2)

        professionals.append(MockPro(
            id=u.ID,
            name=u.Name,
            surname=u.Surname,
            service=u.Service or "",
            location=u.Location or "",
            experience=u.Experience or "",
            availability=u.availability or "",
            rating=u.Rating or 0.0,
            reviews=u.Reviews or 0,
            user_type=u.user_type,
            bio=u.Bio or "",
            image=u.Image or "assets/defaultPP.png",
            distance=dist
        ))

    # Sort by real km distance; pros with no coords go to the bottom
    if lat is not None and lng is not None:
        professionals.sort(key=lambda p: p.Distance if p.Distance is not None else float('inf'))

    return render_template(
        "feed.html",
        professionals=professionals,
        search=search_query,
        location=location_query,
        lat=lat,
        lng=lng
    )


@views.route('/messages', methods=['GET', 'POST'])
def messages():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_get'))

    current_user_id = session['user_id']
    selected_user_id = request.args.get('user_id', type=int)

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

    messages = []
    selected_user = None
    if selected_user_id:
        selected_user = User.query.get(selected_user_id)
        messages = MessageModel.query.filter(
            (MessageModel.sender_id == current_user_id) & (MessageModel.receiver_id == selected_user_id) |
            (MessageModel.sender_id == selected_user_id) & (MessageModel.receiver_id == current_user_id)
        ).order_by(MessageModel.timestamp).all()

        for msg in messages:
            if msg.receiver_id == current_user_id and not msg.is_read:
                msg.is_read = True
        db.session.commit()

    messaged_user_ids = db.session.query(MessageModel.sender_id).filter(
        MessageModel.receiver_id == current_user_id
    ).union(
        db.session.query(MessageModel.receiver_id).filter(
            MessageModel.sender_id == current_user_id
        )
    ).distinct().all()
    messaged_user_ids = [uid[0] for uid in messaged_user_ids if uid[0] != current_user_id]

    from .models import ServiceRequest
    connected_user_ids = db.session.query(ServiceRequest.sender_id).filter_by(
        receiver_id=current_user_id
    ).union(
        db.session.query(ServiceRequest.receiver_id).filter_by(
            sender_id=current_user_id
        )
    ).distinct().all()
    connected_user_ids = [uid[0] for uid in connected_user_ids if uid[0] != current_user_id]

    final_user_ids = list(set(messaged_user_ids + connected_user_ids))

    filtered_user_ids = []
    for uid in final_user_ids:
        completed_request = ServiceRequest.query.filter(
            ((ServiceRequest.sender_id == current_user_id) & (ServiceRequest.receiver_id == uid)) |
            ((ServiceRequest.receiver_id == current_user_id) & (ServiceRequest.sender_id == uid)),
            ServiceRequest.status == "completed"
        ).first()
        if not completed_request:
            filtered_user_ids.append(uid)

    users = User.query.filter(User.ID.in_(filtered_user_ids)).all()

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

    image_file = request.files.get('image')
    image_filename = None

    if image_file and image_file.filename != '':
        upload_folder = os.path.join('static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        filename = secure_filename(image_file.filename)
        filepath = os.path.join(upload_folder, filename)
        image_file.save(filepath)
        image_filename = f"uploads/{filename}"

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
    return redirect(request.referrer or url_for('views.mock_feed'))


@views.route('/request/<int:request_id>/accept', methods=['POST'])
@login_required
def accept_request(request_id):
    request_obj = ServiceRequest.query.get_or_404(request_id)

    if request_obj.receiver_id != session['user_id']:
        flash("Unauthorized action", "error")
        return redirect(url_for('views.Base'))

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

    request_obj.status = 'accepted'
    db.session.commit()

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

    request_obj.status = 'declined'
    db.session.commit()

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

    if request_obj.receiver_id != current_user.ID:
        flash("You cannot mark this request as completed.", "danger")
        return redirect(url_for('views.Base'))

    request_obj.status = 'awaiting_confirmation'
    db.session.commit()

    flash("You marked the service as completed. Waiting for user confirmation.", "success")
    return redirect(url_for('views.Base'))


@views.route('/confirm_completion/<int:request_id>', methods=['POST'])
@login_required
def confirm_completion_by_user(request_id):
    request_obj = ServiceRequest.query.get_or_404(request_id)

    if request_obj.sender_id != current_user.ID:
        flash("You cannot confirm this request.", "danger")
        return redirect(url_for('views.Base'))

    request_obj.status = 'completed'
    db.session.commit()

    messages_to_delete = MessageModel.query.filter(
        or_(
            and_(MessageModel.sender_id == request_obj.sender_id, MessageModel.receiver_id == request_obj.receiver_id),
            and_(MessageModel.sender_id == request_obj.receiver_id, MessageModel.receiver_id == request_obj.sender_id)
        )
    ).all()

    for msg in messages_to_delete:
        db.session.delete(msg)
    db.session.commit()

    flash("You confirmed the service is complete! Messages between you and the pro were deleted.", "success")
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


@views.route('/update_contact/<int:user_id>', methods=['POST'])
def update_contact(user_id):
    user = User.query.get_or_404(user_id)

    new_email = request.form.get('email').strip().lower()
    new_phone = request.form.get('cellphone').strip()

    email_changed = new_email != user.Email
    phone_changed = new_phone != user.CellPhone

    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(email_regex, new_email):
        flash("Invalid email format.", "error")
        return redirect(url_for('views.Base'))

    if email_changed:
        existing_user = User.query.filter_by(Email=new_email).first()
        if existing_user and existing_user.ID != user.ID:
            flash("This email is already in use by another account.", "error")
            return redirect(url_for('views.Base'))

    phone_regex = r"^\+?[0-9]{7,15}$"
    if not re.match(phone_regex, new_phone):
        flash("Invalid phone number format.", "error")
        return redirect(url_for('views.Base'))

    user.Email = new_email
    user.CellPhone = new_phone

    if email_changed:
        user.is_email_verified = False
        code = generate_code()
        user.email_verification_code = code
        send_email_verification(new_email, code)

    if phone_changed:
        user.is_phone_verified = False

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
    receiver_id = request.form.get('receiver_id')
    project_title = request.form.get('project_title')
    details = request.form.get('details')
    location = request.form.get('location')
    preferred_date = request.form.get('preferred_date')
    preferred_time = request.form.get('preferred_time')

    attachment_file = request.files.get('attachment')
    attachment_filename = None
    if attachment_file and attachment_file.filename != '':
        attachment_filename = f"uploads/{attachment_file.filename}"
        attachment_file.save(os.path.join('static', attachment_filename))

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