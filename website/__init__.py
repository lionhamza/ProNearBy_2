from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "PRONEARBY.COM"
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:ProNearBy%4011@localhost:5432/ProNearBy_DB'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Google OAuth Config
    app.config['GOOGLE_CLIENT_ID'] = '1063377439419-e3l1r2l8mdftvsvvjls9psok6gf74med.apps.googleusercontent.com'
    app.config['GOOGLE_CLIENT_SECRET'] = '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'

    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
    
    db.init_app(app)

    from .views import views
    from .auth import auth
    from .models import User
    from .admin import admin

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(admin)

    @app.context_processor
    def inject_user():
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            return dict(user=user)
        return dict(user=None)

    # ✅ 413 Error Handler goes here
    @app.errorhandler(413)
    def too_large(e):
        return "File is too large. Maximum allowed size is 50MB.", 413

    with app.app_context():
        db.create_all()

    return app