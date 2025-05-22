from flask import Blueprint, render_template, redirect, url_for, session, current_app
from .auth import token_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # If user is not logged in, redirect to login page
    if 'token' not in session:
        return redirect(url_for('auth.login'))
    # If logged in, redirect to profile service
    return redirect(current_app.config['PROFILE_SERVICE_URL'])