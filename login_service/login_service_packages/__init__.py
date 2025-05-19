from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .config import Config
from .models import db

def create_app(config_class=Config):
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    from .auth import auth_bp
    # Register auth blueprint without URL prefix for the root route
    app.register_blueprint(auth_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app 