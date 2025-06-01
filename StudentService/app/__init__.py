import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.Core.models import db

def create_app():
    app = Flask(__name__)
    
    # Configure the SQLAlchemy database
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance', 'studentservice.db'))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Set a secure secret key for sessions
    app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production
    
    # Initialize SQLAlchemy with the app
    db.init_app(app)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    except Exception as e:
        print(f"Error creating instance directory: {e}")

    # Register blueprints
    from app.API.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    # Register routes
    from app.API.routes import register_routes
    register_routes(app)
    
    return app 