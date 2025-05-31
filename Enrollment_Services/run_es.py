import os
from flask import Flask, redirect, url_for, session, flash, request, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import timedelta

# Import SQLAlchemy and Migrate directly as they will be initialized here
# from flask_sqlalchemy import SQLAlchemy # REMOVE this line
# from flask_migrate import Migrate # Keep if you use Flask-Migrate in run_es directly, but typically migrated from db.py
from flask_migrate import Migrate #

# Load environment variables from a .env file.
load_dotenv()

# Import the blueprint from your routes
from enrollment_services.routes import enrollment_bp

# IMPORT THE SINGLE DB INSTANCE from enrollment_services.db
from enrollment_services.db import db, init_db #

# Initialize extensions without binding to app yet
# db = SQLAlchemy() # REMOVE this line - it creates a second instance!
migrate = Migrate()

def create_app():
    """
    Factory function to create and configure the Flask application.
    This function now contains all app configurations and extension initializations.
    """
    app = Flask(__name__, template_folder='enrollment_services/templates')

    # --- Application Configuration ---

    # Configure SECRET_KEY for session management.
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'a_very_strong_and_secret_key_for_dev_do_not_use_in_prod_12345')

    # Configure database URI. This is crucial for SQLAlchemy and Flask-Migrate.
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL') or "sqlite:///enrollment.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False # Recommended to disable for performance

    # JWT Configuration
    app.config['JWT_EXPIRATION_DELTA'] = timedelta(hours=1) # Tokens expire in 1 hour
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', app.secret_key)

    # --- Extension Initialization ---
    # Bind SQLAlchemy and Flask-Migrate to the app instance
    # Use the init_db function from enrollment_services.db, or directly db.init_app(app) here.
    # Since init_db also calls create_all(), let's use it for simplicity
    init_db(app) # Use the imported init_db function
    migrate.init_app(app, db) # Now this 'db' refers to the one initialized by init_db

    # Enable CORS (Cross-Origin Resource Sharing).
    CORS(app)

    # --- Blueprint Registration ---
    # Register your 'enrollment_bp' blueprint.
    # All routes defined within 'enrollment_bp' will be prefixed with '/enrollment_services'.
    app.register_blueprint(enrollment_bp, url_prefix='/enrollment_services')

    # --- Login Page Route (Accessible BEFORE authentication) ---
    @app.route('/login')
    def login_page():
        # Clear any existing JWT from Flask session
        session.pop('jwt_token', None)
        flash('Please log in to access the Enrollment Services.', 'info')
        return render_template('login.html')

    # --- Global Before Request Hook for Authentication ---
    @app.before_request
    def check_authentication():
        # List of endpoints that are publicly accessible (do NOT require login)
        public_endpoints = [
            'login_page', # The function name for @app.route('/login')
            'enrollment.login', # The blueprint endpoint for @enrollment_bp.route('/auth/login', methods=['POST'])
            'static', # Allows access to Flask's static file serving (CSS, JS, images)
            'enrollment.set_session_token' # Endpoint to set session token
        ]

        # If the requested endpoint is explicitly public, allow access
        if request.endpoint in public_endpoints:
            return

        # For all other routes (which are considered protected), check for JWT in session
        if 'jwt_token' not in session:
            flash("You need to log in to access this page.", "error")
            return redirect(url_for('login_page'))

        # If a token exists in session, allow the request to proceed.
        # The `@token_required` decorator on specific API endpoints will then
        # handle actual JWT validation and provide `current_user` context.

    # --- Root Route Redirection ---
    # Handles requests to the base URL (e.g., http://localhost:5004/).
    @app.route('/')
    def root_home():
        # If the user has a JWT in their Flask session (meaning they've logged in)
        if 'jwt_token' in session:
            # They are authenticated, redirect to the dashboard within the blueprint
            return redirect(url_for('enrollment.enroll'))
        else:
            # Not authenticated, redirect to the dedicated login page
            return redirect(url_for('login_page'))

    return app

# --- Main Application Execution Block ---
if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get("PORT", 5004))
    app.run(host='0.0.0.0', port=port, debug=True)