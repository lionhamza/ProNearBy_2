from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

db = SQLAlchemy()
mail = Mail()
from flask_login import LoginManager, current_user
from .models import User

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "PRONEARBY.COM"
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:ProNearBy%4011@localhost:5432/ProNearBy_DB'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Google OAuth Config
    app.config['GOOGLE_CLIENT_ID'] = '1063377439419-e3l1r2l8mdftvsvvjls9psok6gf74med.apps.googleusercontent.com'
    app.config['GOOGLE_CLIENT_SECRET'] = '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'

    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

    # Email config
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'pronearby.service@gmail.com'
    app.config['MAIL_PASSWORD'] = 'ovlw fhpk nrbq ctkv'  # App-specific password
    app.config['MAIL_DEFAULT_SENDER'] = 'ProNearBy <pronearby.service@gmail.com>'

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login_get'  # page to redirect if not logged in

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .views import views
    from .auth import auth
    from .admin import admin

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(admin)

    @app.context_processor
    def inject_user():
        # current_user is now available
        return dict(user=current_user)

    # 413 Error Handler
    @app.errorhandler(413)
    def too_large(e):
        return "File is too large. Maximum allowed size is 50MB.", 413

    with app.app_context():
        db.create_all()

    return app
