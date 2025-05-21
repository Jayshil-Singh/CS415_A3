# run_es.py
import os
from flask import Flask, redirect, url_for, session, flash, request, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables from a .env file.
load_dotenv()

# Import the database initialization function and your blueprint.
from enrollment_services.db import init_db
from enrollment_services.routes import enrollment_bp

def create_app():
    """
    Factory function to create and configure the Flask application.
    """
    app = Flask(__name__, template_folder='enrollment_services/templates')

    # --- Application Configuration ---

    # Configure SECRET_KEY for session management.
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'a_very_strong_and_secret_key_for_dev_do_not_use_in_prod_12345')

    # Configure database URI.
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///enrollment.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # JWT Configuration
    app.config['JWT_EXPIRATION_DELTA'] = timedelta(hours=1) # Tokens expire in 1 hour
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', app.secret_key)

    # Enable CORS (Cross-Origin Resource Sharing).
    CORS(app)

    # --- Database Initialization ---
    # Call the init_db function to bind SQLAlchemy to the app and create tables.
    init_db(app)

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
            'static' # Allows access to Flask's static file serving (CSS, JS, images)
            'enrollment.set_session_token'
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
            return redirect(url_for('enrollment.dashboard'))
        else:
            # Not authenticated, redirect to the dedicated login page
            return redirect(url_for('login_page'))

    return app

# --- Main Application Execution Block ---
if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get("PORT", 5004))
    app.run(host='0.0.0.0', port=port, debug=True)