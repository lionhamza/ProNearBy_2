from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
import os
from flask_login import LoginManager, current_user

# Initialize extensions
db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # App secrets
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "PRONEARBY.COM")
    
    # Database config
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'postgresql://pronearby_db_user:eU5bWVLra6jEV5iJt55wb0BFqmuSJAat@dpg-d2qdr6mr433s73e6q010-a/pronearby_db',
        #'postgresql://postgres:ProNearBy%4011@localhost:5432/ProNearBy_DB'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Google OAuth Config
    app.config['GOOGLE_CLIENT_ID'] = os.environ.get(
        'GOOGLE_CLIENT_ID',
        '1063377439419-e3l1r2l8mdftvsvvjls9psok6gf74med.apps.googleusercontent.com'
    )
    app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get(
        'GOOGLE_CLIENT_SECRET',
        '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'
    )

    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

    # Email config
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'pronearby.service@gmail.com')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'ovlw fhpk nrbq ctkv')  # app password
    app.config['MAIL_DEFAULT_SENDER'] = 'ProNearBy <pronearby.service@gmail.com>'

    # Initialize extensions with app
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login_get'

    # Import models *after* db is ready
    from .models import User  

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from .views import views
    from .auth import auth
    from .admin import admin

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(admin)

    # Add user context globally
    @app.context_processor
    def inject_user():
        return dict(user=current_user)

    # 413 Error Handler
    @app.errorhandler(413)
    def too_large(e):
        return "File is too large. Maximum allowed size is 50MB.", 413

    # Create database tables
    with app.app_context():
        db.create_all()

    return app

