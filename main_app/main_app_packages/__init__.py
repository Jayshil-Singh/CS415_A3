from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from .config import Config
# from flask_login import LoginManager # Example if using Flask-Login
from .models import db
from .routes import main_bp
from .error_handlers import (
    handle_error, handle_500_error, handle_404_error,
    CustomError, AuthenticationError, AuthorizationError,
    ResourceNotFoundError, ValidationError, ServiceUnavailableError
)
from .logger import setup_logger, request_logger

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
    CORS(app, resources={r"/*": {"origins": app.config['CORS_ORIGINS']}})
    # login_manager.init_app(app)

    # Setup logging
    setup_logger(app)

    # Import and register blueprints
    from .routes import main_bp  # Corrected to relative import for blueprint
    from .auth import auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')

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