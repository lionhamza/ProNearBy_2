from . import db

class User(db.Model):
    __tablename__ = 'users'  # <-- match this to your real table name

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    address = db.Column(db.String)
    profession = db.Column(db.String)
    experience = db.Column(db.String)
    contact = db.Column(db.String)
    availability = db.Column(db.String)
    rating = db.Column(db.Float)
    reviews = db.Column(db.Integer)
    image = db.Column(db.String)  # e.g. 'assets/electrician.jpg'
