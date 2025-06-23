from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "PRONEARBY.COM"

    # ✅ Correct connection string (notice %40 for '@')
    # URL-encode the `@` symbol in your password using `%40`
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:ProNearBy%4011@localhost:5432/ProNearBy_DB'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Import and register your blueprints
    from .views import views
    from .auth import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    return app
