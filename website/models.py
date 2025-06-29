from sqlalchemy.dialects.postgresql import JSON  # add this at the top
from . import db

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
