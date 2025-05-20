# run_es.py
import os
from flask import Flask, redirect, url_for, session, flash
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from a .env file.
# This is crucial for managing configurations like SECRET_KEY and PORT,
# especially in different environments (development vs. production).
load_dotenv()

# Import the database initialization function and your blueprint.
# These imports assume 'db.py' and 'routes.py' are directly within the 'enrollment_services' package.
from enrollment_services.db import init_db
from enrollment_services.routes import enrollment_bp

def create_app():
    """
    Factory function to create and configure the Flask application.
    This pattern is recommended for more complex applications as it allows
    for different configurations (e.g., testing, development, production).
    """
    # Initialize Flask app.
    # `template_folder` is explicitly set to ensure Flask finds your HTML templates
    # correctly, as they are nested inside 'enrollment_services/templates'.
    app = Flask(__name__, template_folder='enrollment_services/templates')

    # --- Application Configuration ---

    # Configure SECRET_KEY for session management.
    # It's crucial for security that this key is kept secret and
    # generated randomly. Using an environment variable is best practice.
    # A default is provided for development convenience, but CHANGE THIS FOR PRODUCTION!
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'a_very_strong_and_secret_key_for_dev_do_not_use_in_prod_12345')

    # Configure database URI.
    # Flask-SQLAlchemy will use this to connect to your SQLite database file.
    # The database file 'enrollment.db' will be created in the root directory
    # where you run 'run_es.py'.
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///enrollment.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False # Suppresses a warning and saves memory

    # Enable CORS (Cross-Origin Resource Sharing).
    # This is important if your frontend (e.g., a React/Angular app) is served
    # from a different origin (domain:port) than your Flask backend.
    # For local development, this typically allows your frontend (e.g., on port 3000)
    # to make requests to your Flask app (e.g., on port 5004).
    CORS(app)

    # --- Database Initialization ---
    # Call the init_db function to bind SQLAlchemy to the app and create tables.
    init_db(app)

    # --- Blueprint Registration ---
    # Register your 'enrollment_bp' blueprint.
    # The `url_prefix` means all routes defined within 'enrollment_bp' (in routes.py)
    # will be prefixed with '/enrollment_services'.
    # For example:
    # - `@enrollment_bp.route('/enroll')` will be accessible at `/enrollment_services/enroll`
    # - `@enrollment_bp.route('/students')` will be accessible at `/enrollment_services/students`
    app.register_blueprint(enrollment_bp, url_prefix='/enrollment_services')

    # --- Root Route Redirection ---
    # This route handles requests to the base URL of your application (e.g., http://localhost:5004/).
    # It redirects users to the dashboard page within your blueprint.
    @app.route('/')
    def root_home():
        # Redirect to the dashboard route defined in the 'enrollment' blueprint.
        # url_for needs the blueprint name ('enrollment') followed by the route function name ('dashboard').
        return redirect(url_for('enrollment.dashboard'))

    return app

# --- Main Application Execution Block ---
# This block ensures that the Flask app is created and run only when this script
# is executed directly (not when imported as a module).
if __name__ == '__main__':
    app = create_app()

    # Get the port from environment variables, defaulting to 5004.
    # This makes your application more flexible for deployment.
    port = int(os.environ.get("PORT", 5004))

    # Run the Flask development server.
    # `host='0.0.0.0'` makes the server accessible externally (useful in Docker/VMs).
    # `debug=True` enables debug mode, providing detailed error messages and
    # automatic reloader on code changes. Set to False for production.
    app.run(host='0.0.0.0', port=port, debug=True)