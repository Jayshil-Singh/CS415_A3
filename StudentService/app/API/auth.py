import re
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, render_template, request, jsonify, current_app

from app.Core.model import db, User, LoginAttempt

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '').split()
        if len(auth) != 2 or auth[0].lower() != 'bearer':
            return jsonify({'message': 'Token missing or malformed'}), 401

        token = auth[1]
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            user = User.query.get(payload['user_id'])
            if not user:
                raise RuntimeError()
        except Exception:
            return jsonify({'message': 'Invalid or expired token'}), 401

        return f(user, *args, **kwargs)
    return decorated

@auth_bp.route('/login', methods=['GET'])
def login():
    """
    Render the login page (GET /login).
    """
    return render_template('login.html')

@auth_bp.route('/api/login', methods=['POST'])
def login_post():
    """
    Handle JSON login (POST /api/login).
    Expects { role, password, email/username } in the JSON body.
    Returns a JWT on success.
    """
    data = request.get_json() or {}
    role = data.get('role')
    pw   = data.get('password')

    if role not in ('student', 'sas_manager', 'admin') or not pw:
        return jsonify({'message': 'Missing or invalid fields'}), 400

    # lookup by email for students, username for others
    if role == 'student':
        email = data.get('email', '')
        if not re.match(r'^s\d{8}@student\.usp\.ac\.fj$', email):
            return jsonify({'message': 'Invalid student email format'}), 400
        user = User.query.filter_by(email=email).first()
    else:
        user = User.query.filter_by(username=data.get('username')).first()

    # record the attempt
    attempt = LoginAttempt(
        user_id    = user.id if user else None,
        ip_address = request.remote_addr,
        success    = False
    )
    db.session.add(attempt)

    # validate credentials
    if not user or not user.check_password(pw) or not user.is_active:
        db.session.commit()
        return jsonify({'message': 'Invalid credentials'}), 401

    # success! update last_login and mark attempt
    user.last_login = datetime.utcnow()
    attempt.success  = True
    db.session.add(user)
    db.session.commit()

    # issue JWT
    token = jwt.encode({
        'user_id': user.id,
        'role':    user.role,
        'exp':     datetime.utcnow() +
                   timedelta(seconds=current_app.config['JWT_ACCESS_TOKEN_EXPIRES'])
    }, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

    return jsonify({
        'token': token,
        'user': {
            'id':       user.id,
            'username': user.username,
            'email':    user.email,
            'role':     user.role
        }
    })

@auth_bp.route('/api/verify', methods=['GET'])
@token_required
def verify(user):
    """
    Verify JWT and return user info (GET /api/verify).
    """
    return jsonify({
        'user': {
            'id':       user.id,
            'username': user.username,
            'email':    user.email,
            'role':     user.role
        }
    })
