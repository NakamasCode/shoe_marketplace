from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os
import cloudinary

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = "main.login"  # safer with blueprint prefix

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")  # make sure Config has SECRET_KEY & SQLALCHEMY_DATABASE_URI

    # Cloudinary setup
    cloudinary.config(
        cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
        api_key=os.environ.get("CLOUDINARY_API_KEY"),
        api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
        secure=True
    )

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    # Register blueprint
    from app.routes import main
    app.register_blueprint(main)

    # Create tables automatically if they don't exist
    with app.app_context():
        db.create_all()

    return app
