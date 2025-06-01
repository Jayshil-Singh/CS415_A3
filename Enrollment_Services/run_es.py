import os
from flask import Flask, redirect, url_for, session, flash, request, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import timedelta
from flask_migrate import Migrate

# Load environment variables from a .env file.
load_dotenv()

# Import the blueprint from your routes
from enrollment_services.routes import enrollment_bp

# Import the single db instance
from enrollment_services.db import db

# Initialize migrate (not yet bound to app)
migrate = Migrate()

def create_app():
    app = Flask(__name__, template_folder='enrollment_services/templates')

    # --- Configuration ---
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev_secret_key')
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL') or "sqlite:///enrollment.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config['JWT_EXPIRATION_DELTA'] = timedelta(hours=1)
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', app.secret_key)

    # --- Extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # --- Register Blueprints ---
    app.register_blueprint(enrollment_bp, url_prefix='/enrollment_services')

    # --- Ensure DB Tables are Created ---
    with app.app_context():
        db.create_all()

    # --- Public Login Page ---
    @app.route('/login')
    def login_page():
        session.pop('jwt_token', None)
        flash('Please log in to access the Enrollment Services.', 'info')
        return render_template('login.html')

    # --- Authentication Middleware ---
    @app.before_request
    def check_authentication():
        public_endpoints = [
            'login_page',
            'enrollment.login',
            'static',
            'enrollment.set_session_token'
        ]
        if request.endpoint in public_endpoints:
            return
        if 'jwt_token' not in session:
            flash("You need to log in to access this page.", "error")
            return redirect(url_for('login_page'))

    # --- Root Redirect ---
    @app.route('/')
    def root_home():
        if 'jwt_token' in session:
            return redirect(url_for('enrollment.enroll'))
        else:
            return redirect(url_for('login_page'))

    return app

# --- Run App ---
if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get("PORT", 5004))
    app.run(host='0.0.0.0', port=port, debug=True)
