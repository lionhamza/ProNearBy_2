from sqlalchemy.dialects.postgresql import JSON  # add this at the top
from . import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'User_Info'  # <-- match this to your real table name

    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)

    Name = db.Column(db.String)
    Email=db.Column(db.String)
    Location = db.Column(db.String)
    Service = db.Column(db.String)
    Experience = db.Column(db.String) 
    CellPhone = db.Column(db.String)
    availability = db.Column(db.String)
    Rating = db.Column(db.Float)
    Reviews = db.Column(db.Integer)
    Bio =db.Column(db.String)
    Surname=db.Column(db.String)
    Image = db.Column(db.String)  # e.g. 'assets/electrician.jpg'
    CoverImage=db.Column(db.String)
    Password=db.Column(db.String)


class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500))
    media = db.Column(JSON, nullable=True)  # <-- changed from image to media
    timestamp = db.Column(db.DateTime, default=db.func.now())

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
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())




class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True)

    sender_id = db.Column(db.Integer, db.ForeignKey('User_Info.ID'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('User_Info.ID'), nullable=False)

    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
