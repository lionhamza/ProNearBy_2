from . import db

class User(db.Model):
    __tablename__ = 'User_Info'  # <-- match this to your real table name

    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String)
    Location = db.Column(db.String)
    Service = db.Column(db.String)
    #experience = db.Column(db.String) 
    CellPhone = db.Column(db.String)
    #availability = db.Column(db.String)
    #rating = db.Column(db.Float)
    #reviews = db.Column(db.Integer)

    #image = db.Column(db.String)  # e.g. 'assets/electrician.jpg'
