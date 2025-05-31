from flask import Blueprint, request, jsonify, current_app, render_template, redirect, flash, session, url_for
from datetime import datetime, timedelta
from .models import db, User, LoginAttempt
import jwt
from functools import wraps
import re
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'message': 'Authorization header is missing!'}), 401
            
        try:
            # Verify "Bearer " prefix
            if not auth_header.startswith('Bearer '):
                return jsonify({'message': 'Invalid token format!'}), 401
                
            token = auth_header.split(' ')[1]
            data = jwt.decode(
                token, 
                current_app.config['JWT_SECRET_KEY'], 
                algorithms=['HS256'],
                options={"require": ["exp", "iat", "sub", "jti"]}
            )
            
            current_user = User.query.get(data['sub'])
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
                
            if not current_user.is_active:
                return jsonify({'message': 'User account is disabled!'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401
        except Exception as e:
            current_app.logger.error(f"Token validation error: {str(e)}")
            return jsonify({'message': 'Token validation failed!'}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated

@auth_bp.route('/')
def login_page():
    return render_template('login.html')

def validate_student_id(student_id):
    """Validate student ID format"""
    pattern = r'^S\d{8}$'
    return bool(re.match(pattern, student_id, re.IGNORECASE))

def is_brute_force_attempt(user_id, ip_address):
    """Check for potential brute force attempts"""
    time_window = datetime.utcnow() - timedelta(minutes=15)
    failed_attempts = LoginAttempt.query.filter(
        LoginAttempt.user_id == user_id,
        LoginAttempt.ip_address == ip_address,
        LoginAttempt.timestamp >= time_window,
        LoginAttempt.success == False
    ).count()
    return failed_attempts >= 5

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password = request.form.get('password')
        
        if not identifier or not password:
            flash('Please provide both student ID and password', 'error')
            return render_template('login.html')
        
        # Clean and validate student ID
        student_id = identifier.upper()
        if not validate_student_id(student_id):
            flash('Invalid student ID format. Please use: SXXXXXXXX (where X is a digit)', 'error')
            return render_template('login.html')
        
        # Check for brute force attempts
        if is_brute_force_attempt(student_id, request.remote_addr):
            flash('Too many failed attempts. Please try again later.', 'error')
            return render_template('login.html'), 429
        
        # Check database for student
        user = User.query.get(student_id)
        
        # Record login attempt
        login_attempt = LoginAttempt(
            user_id=user.id if user else None,
            ip_address=request.remote_addr,
            success=False
        )
        
        if not user:
            db.session.add(login_attempt)
            db.session.commit()
            flash('Invalid credentials', 'error')  # Generic error message for security
            return render_template('login.html')
        
        if not user.check_password(password):
            db.session.add(login_attempt)
            db.session.commit()
            flash('Invalid credentials', 'error')  # Generic error message for security
            return render_template('login.html')
        
        if not user.is_active:
            db.session.add(login_attempt)
            db.session.commit()
            flash('Account is disabled', 'error')
            return render_template('login.html')
        
        # Update last login and record successful attempt
        user.last_login = datetime.utcnow()
        login_attempt.success = True
        db.session.add(login_attempt)
        db.session.commit()
        
        # Generate JWT token with additional security claims
        token_data = {
            'sub': user.id,  # subject (user ID)
            'role': 'student',
            'iat': datetime.utcnow(),  # issued at
            'exp': datetime.utcnow() + timedelta(hours=1),  # expiration
            'jti': str(uuid.uuid4()),  # unique token ID
        }
        
        token = jwt.encode(
            token_data,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        
        # Set secure session data
        session.clear()  # Clear any existing session data
        session['token'] = token
        session['user_id'] = user.id
        session['email'] = user.email
        session['user_type'] = 'student'
        session['_fresh'] = True
        
        # Get redirect URL from config
        student_service_url = current_app.config['SERVICES']['STUDENT']
        return redirect(student_service_url)
        
    return render_template('login.html')

@auth_bp.route('/api/verify', methods=['GET'])
@token_required
def verify_token(current_user):
    return jsonify({
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'role': 'student',
            'last_login': current_user.last_login.isoformat() if current_user.last_login else None
        }
    })

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.login_page')) 