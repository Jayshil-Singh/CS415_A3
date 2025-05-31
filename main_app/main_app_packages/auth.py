from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
# from flask_login import login_user, logout_user, current_user
# from .models import User # Assuming you have a User model
# from . import db # Assuming you have db from __init__.py
from functools import wraps
import jwt
import os

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # TODO: Implement actual login logic
        flash('Login functionality not implemented yet', 'warning')
        return redirect(url_for('main_bp.index'))
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Your registration logic
    return "Register Page (Not Implemented)"

@auth_bp.route('/logout')
def logout():
    # logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main_bp.index'))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        if session.get('role') != 'admin':
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def verify_token(token):
    """Verify JWT token"""
    try:
        secret_key = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def create_token(user_data):
    """Create JWT token"""
    secret_key = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
    token = jwt.encode(user_data, secret_key, algorithm='HS256')
    return token

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            
            secret_key = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
            data = jwt.decode(token, secret_key, algorithms=['HS256'])
            # You can add additional token validation here if needed
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
            
        return f(*args, **kwargs)
    return decorated

# Remember to register this blueprint in __init__.py if you use it.