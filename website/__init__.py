from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "PRONEARBY.COM"

    # Switch to SQLite for easier development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pronearby.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Google OAuth Config - Your actual credentials
    app.config['GOOGLE_CLIENT_ID'] = '1063377439419-e3l1r2l8mdftvsvvjls9psok6gf74med.apps.googleusercontent.com'
    app.config['GOOGLE_CLIENT_SECRET'] = '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'

    db.init_app(app)

    # Import and register your blueprints
    from .views import views
    from .auth import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # Create database tables
    with app.app_context():
        db.create_all()

    return app
