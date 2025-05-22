from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from .config import Config
# from flask_login import LoginManager # Example if using Flask-Login
from .models import db
from .error_handlers import (
    handle_error, handle_500_error, handle_404_error,
    CustomError, AuthenticationError, AuthorizationError,
    ResourceNotFoundError, ValidationError, ServiceUnavailableError
)
from .logger import setup_logger, request_logger
from .auth import auth_bp
from .main import main_bp

# db = SQLAlchemy() # Example
# login_manager = LoginManager() # Example
# login_manager.login_view = 'main_routes.login' # Example: redirect to login if @login_required

def create_app(config_class=Config):
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    CORS(app)
    # login_manager.init_app(app)

    # Setup logging
    setup_logger(app)
    
    # Configure the app
    app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production
    app.config['LOGIN_SERVICE_URL'] = 'http://127.0.0.1:5002'  # Login service running on port 5002
    app.config['LOGIN_SERVICE_PORT'] = 5002  # Explicitly set login service port
    app.config['PROFILE_SERVICE_URL'] = 'http://127.0.0.1:5003'  # Profile service running on port 5003
    app.config['CALLBACK_URL'] = 'http://127.0.0.1:5000/auth/callback'  # Callback URL for login service

    # Import and register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)

    # Initialize app
    config_class.init_app(app)

    # Create database tables
    with app.app_context():
        db.create_all()

    # Example context processor to make PROFILE_SERVICE_URL available in all templates
    @app.context_processor
    def inject_profile_service_url():
        return dict(PROFILE_SERVICE_URL=app.config.get('PROFILE_SERVICE_URL'))

    # Register error handlers
    app.register_error_handler(CustomError, handle_error)
    app.register_error_handler(500, handle_500_error)
    app.register_error_handler(404, handle_404_error)
    
    # Add request logging middleware
    @app.before_request
    def before_request():
        request_logger(app.logger.info)(lambda: None)()

    return app