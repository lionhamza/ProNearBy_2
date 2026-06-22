from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from . import db  # ✅ now safe, since db is defined in __init__.py
from sqlalchemy import Boolean
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'User_Info'

    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(100))
    Email = db.Column(db.String(100))
    Location = db.Column(db.String(200))
    
    # New fields for coordinates
    Latitude = db.Column(db.Float, nullable=True)
    Longitude = db.Column(db.Float, nullable=True)

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
    
    user_type = db.Column(db.String(50), default='regular')

    is_email_verified = db.Column(Boolean, default=False)
    is_phone_verified = db.Column(Boolean, default=False)

    def get_id(self):
        return str(self.ID)

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
    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])

class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('User_Info.ID'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('User_Info.ID'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)  # 👈 new field
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
    latitude = db.Column(db.Float, nullable=True)   # ← ADD THIS
    longitude = db.Column(db.Float, nullable=True)  # ← ADD THIS

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

class QuoteRequest(db.Model):
    __tablename__ = 'quote_requests'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('User_Info.ID'), nullable=True)  # optional if anonymous
    receiver_id = db.Column(db.Integer, db.ForeignKey('User_Info.ID'), nullable=False)
    
    project_title = db.Column(db.String(150), nullable=False)
    details = db.Column(db.Text, nullable=False)
    
    location = db.Column(db.String(200))  # optional
    attachment = db.Column(db.String(300))  # optional, file path
    
    preferred_date = db.Column(db.Date)  # optional
    preferred_time = db.Column(db.Time)  # optional
    
    status = db.Column(db.String(20), default='pending')  # 'pending', 'accepted', 'declined'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_quote_requests')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_quote_requests')

    def __repr__(self):
        return f"<QuoteRequest {self.project_title} to {self.receiver_id}>"


# Add this as a new file, e.g. website/wallet_models.py, OR paste these three
# classes into your existing models.py so they share the same `db` instance
# as your User model (they must, for the ForeignKey to resolve).
#
# Confirmed against your actual User model:
#   - Table name is 'User_Info' (not the default 'user'), primary key is 'ID'.
#     The ForeignKey('User_Info.ID') below matches this.
#
# Other assumptions — adjust if these don't match your actual project:
#   1. You're using Flask-SQLAlchemy with a `db = SQLAlchemy()` instance.
#      Change the import below to wherever that instance actually lives
#      (e.g. `from .extensions import db` or `from website import db`).
#   2. Money is stored as Numeric, never float — floats lose precision on
#      currency math and that's the kind of bug that costs someone real rands.
#   3. PaymentMethod stores ONLY a payment-gateway token (Stripe/PayFast/etc),
#      never a raw card number, CVV, or full PAN. Storing real card data
#      yourself pulls you into PCI-DSS scope — let the gateway hold it.

from datetime import datetime
import uuid

from . import db  # <-- adjust to your actual db import


class Wallet(db.Model):
    __tablename__ = 'wallets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User_Info.ID'), unique=True, nullable=False)

    balance = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    pending_balance = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('wallet', uselist=False))
    transactions = db.relationship(
        'Transaction', backref='wallet', lazy='dynamic',
        order_by='Transaction.created_at.desc()', cascade='all, delete-orphan'
    )
    payment_methods = db.relationship(
        'PaymentMethod', backref='wallet', lazy=True, cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Wallet user_id={self.user_id} balance={self.balance}>'


class PaymentMethod(db.Model):
    __tablename__ = 'payment_methods'

    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=False)

    brand = db.Column(db.String(20), nullable=False)       # 'visa' | 'mastercard' | 'amex' | 'discover'
    last4 = db.Column(db.String(4), nullable=False)
    exp_month = db.Column(db.Integer, nullable=False)
    exp_year = db.Column(db.Integer, nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)

    # Reference token from your payment gateway (e.g. Stripe payment_method id,
    # PayFast token). This is what you actually charge — never store the PAN.
    provider_token = db.Column(db.String(255), nullable=False, unique=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<PaymentMethod {self.brand} ****{self.last4}>'


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=False)

    type = db.Column(db.String(10), nullable=False)         # 'credit' | 'debit'
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'completed' | 'pending' | 'failed'

    # Unique idempotency / gateway reference — stops a retried webhook or a
    # double form-submit from creating two transactions for one payment.
    reference = db.Column(db.String(64), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        db.CheckConstraint("type IN ('credit', 'debit')", name='ck_transaction_type'),
        db.CheckConstraint("status IN ('completed', 'pending', 'failed')", name='ck_transaction_status'),
        db.CheckConstraint('amount > 0', name='ck_transaction_amount_positive'),
    )

    def __repr__(self):
        return f'<Transaction {self.type} {self.amount} ({self.status})>'
