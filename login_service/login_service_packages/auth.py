from flask import Blueprint, request, jsonify, current_app, render_template
from datetime import datetime, timedelta
from .models import db, User, LoginAttempt
import jwt
from functools import wraps
import re

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'message': 'Invalid token!'}), 401
        except:
            return jsonify({'message': 'Invalid token!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@auth_bp.route('/')
def login_page():
    return render_template('login.html')

@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['id', 'username', 'email', 'password', 'role']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Validate role
    if data['role'] not in ['student', 'sas_manager', 'admin']:
        return jsonify({'message': 'Invalid role'}), 400
    
    # Check if user already exists
    if User.query.get(data['id']):
        return jsonify({'message': 'User ID already exists'}), 400
    
    # Create new user
    user = User(
        id=data['id'],
        username=data['username'],
        email=data['email'],
        role=data['role']
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

def validate_student_email(email):
    # USP student email format: s[8 digits]@student.usp.ac.fj
    pattern = r'^s\d{8}@student\.usp\.ac\.fj$'
    return bool(re.match(pattern, email))

def extract_student_id_from_email(email):
    """Extract student ID from email (e.g., 's12345678@student.usp.ac.fj' -> 'S12345678')"""
    if validate_student_email(email):
        return 'S' + email[1:9]  # Convert 's12345678' to 'S12345678'
    return None

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Handle student login with email
    if data.get('role') == 'student':
        if not data.get('email'):
            return jsonify({'message': 'Email is required for student login'}), 400
        
        # Validate student email format
        if not validate_student_email(data['email']):
            return jsonify({'message': 'Invalid student email format. Must be s[8 digits]@student.usp.ac.fj'}), 400

        # Extract student ID from email
        student_id = extract_student_id_from_email(data['email'])
        if not student_id:
            return jsonify({'message': 'Invalid student email format'}), 400

        # Verify student exists in both databases
        exists, message = User.verify_student_exists(student_id, data['email'])
        if not exists:
            return jsonify({'message': message}), 401
        
        user = User.query.filter_by(email=data['email']).first()
    else:
        # Handle other roles with username
        if not data.get('username'):
            return jsonify({'message': 'Username is required'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
    
    # Record login attempt
    login_attempt = LoginAttempt(
        user_id=user.id if user else None,
        ip_address=request.remote_addr,
        success=False
    )
    
    if not user:
        db.session.add(login_attempt)
        db.session.commit()
        return jsonify({'message': 'User not found'}), 401
    
    if not user.check_password(data['password']):
        db.session.add(login_attempt)
        db.session.commit()
        return jsonify({'message': 'Invalid password'}), 401
    
    if not user.is_active:
        db.session.add(login_attempt)
        db.session.commit()
        return jsonify({'message': 'Account is disabled'}), 401
    
    # Update last login and record successful attempt
    user.last_login = datetime.utcnow()
    login_attempt.success = True
    db.session.add(login_attempt)
    db.session.commit()
    
    # Generate JWT token
    token = jwt.encode({
        'user_id': user.id,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(seconds=3600)
    }, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
    
    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
    })

@auth_bp.route('/api/verify', methods=['GET'])
@token_required
def verify_token(current_user):
    return jsonify({
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'role': current_user.role
        }
    }) 