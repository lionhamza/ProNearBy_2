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

class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500))
    media = db.Column(JSON, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('User_Info.ID'))
    user = db.relationship('User', backref=db.backref('posts', lazy=True))

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

class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('User_Info.ID'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('User_Info.ID'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
