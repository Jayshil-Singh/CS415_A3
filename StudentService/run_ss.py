from flask import Flask
from app.API.config import Config
from app.Core.models import db
from app.API.routes import register_routes
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import timedelta

def create_app():
    app = Flask(__name__)
    
    # Set template and static folders relative to the app root
    app_root = os.path.dirname(os.path.abspath(__file__))
    app.template_folder = os.path.join(app_root, 'app', 'templates')
    app.static_folder = os.path.join(app_root, 'app', 'static')
    
    # Configure logging
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/studentservice.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('StudentService startup')
    
    # Load configuration
    app.config.from_object(Config)
    
    # Configure session
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # Session expires after 2 hours
    app.config['SESSION_COOKIE_SECURE'] = True  # Only send cookie over HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection

    # Initialize database
    db.init_app(app)
    with app.app_context():
        try:
            db.create_all()
            app.logger.info('Database tables created successfully')
        except Exception as e:
            app.logger.error(f'Error creating database tables: {str(e)}')
            raise

    # Register routes
    try:
        register_routes(app)
        app.logger.info('Routes registered successfully')
    except Exception as e:
        app.logger.error(f'Error registering routes: {str(e)}')
        raise

    return app

if __name__ == "__main__":
    app = create_app()
    # In development, you might want to disable HTTPS requirement for session cookie
    if app.debug:
        app.config['SESSION_COOKIE_SECURE'] = False
    app.run(debug=True, port=5002)
