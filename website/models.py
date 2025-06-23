from . import db

class User(db.Model):
    __tablename__ = 'User_Info'  # <-- match this to your real table name

    ID = db.Column(db.Integer, primary_key=True)
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
