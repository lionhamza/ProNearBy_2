from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from . import db  # ✅ now safe, since db is defined in __init__.py

class User(db.Model):
    __tablename__ = 'User_Info'

    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(100))
    Email = db.Column(db.String(100))
    Location = db.Column(db.String(200))
    Service = db.Column(db.String(100))
    Experience = db.Column(db.String(200))
    CellPhone = db.Column(db.String(20))
    availability = db.Column(db.String(100))
    Rating = db.Column(db.Float)
    Reviews = db.Column(db.Integer)
    Bio = db.Column(db.Text)
    Surname = db.Column(db.String(100))
    Image = db.Column(db.String(200))
    CoverImage = db.Column(db.String(200))
    Password = db.Column(db.String(200))
    
    user_type = db.Column(db.String(50), default='regular')  # new field


class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500))
    media = db.Column(JSON, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('User_Info.ID'))
    user = db.relationship('User', backref=db.backref('posts', lazy=True))
    @property
    def like_count(self):
        return self.likes.count()
    
class ServiceRequest(db.Model):
    __tablename__ = 'service_requests'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('User_Info.ID'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('User_Info.ID'), nullable=False)
    service = db.Column(db.Text, nullable=False)
    service_type = db.Column(db.Text)
    location = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.Text)
    preferred_date = db.Column(db.Date)
    preferred_time = db.Column(db.Time)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    status = db.Column(db.String(20), nullable=False, default='pending')  # New column


class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('User_Info.ID'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('User_Info.ID'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User_Info.ID'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User')
    post = db.relationship('Post', backref=db.backref('likes', lazy='dynamic'))


class ProRegistrationRequest(db.Model):
    __tablename__ = 'pro_registration_requests'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    contact = db.Column(db.String(20), nullable=False, unique=True)

    password = db.Column(db.String(200), nullable=False)  # store hashed
    service = db.Column(db.String(100), nullable=False)
    experience = db.Column(db.String(200), nullable=False)
    availability = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text)
    location = db.Column(db.String(200))

    # Uploads
    id_doc = db.Column(db.String(300))  # file path to government ID
    cert_doc = db.Column(db.String(300))  # for certified pros (optional)
    portfolio_files = db.Column(JSON)  # list of image paths
    intro_video = db.Column(db.String(300))  # path to video file

    is_certified = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

class Admin(db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # store hashed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserComplaint(db.Model):
    __tablename__ = 'user_complaints'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User_Info.ID'))
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User')
