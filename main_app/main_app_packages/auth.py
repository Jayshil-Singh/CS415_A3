from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, session
from functools import wraps
import requests
from .error_handlers import AuthenticationError, AuthorizationError, error_handler, ValidationError, ServiceUnavailableError
# from .models import User # Assuming you have a User model
# from . import db # Assuming you have db from __init__.py

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']
        elif 'token' in session:
            token = session['token']
            
        if not token:
            raise AuthenticationError("Token is missing")
            
        try:
            # Verify token with login service
            verify_url = f"{current_app.config['LOGIN_SERVICE_URL']}/verify"
            resp = requests.get(
                verify_url,
                headers={'Authorization': token}
            )
            
            if resp.status_code == 200:
                current_user = resp.json()
                return f(current_user, *args, **kwargs)
            else:
                raise AuthenticationError("Invalid token")
                
        except requests.exceptions.ConnectionError:
            raise ServiceUnavailableError("Login service is not available")
        except Exception as e:
            raise AuthenticationError(f"Error verifying token: {str(e)}")
            
    return decorated

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                raise AuthenticationError("Invalid token format")
        
        if not token:
            raise AuthenticationError("Token is missing")
            
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")
            
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                raise AuthenticationError("Invalid token format")
        
        if not token:
            raise AuthenticationError("Token is missing")
            
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data
            
            if not current_user.get('is_admin', False):
                raise AuthorizationError("Admin privileges required")
                
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")
            
        return f(*args, **kwargs)
    return decorated

@auth_bp.route('/login', methods=['GET', 'POST'])
@error_handler
def login():
    # Redirect to login service's login page
    return redirect(current_app.config['LOGIN_SERVICE_URL'])

@auth_bp.route('/callback')
@error_handler
def callback():
    # Handle login callback from login service
    token = request.args.get('token')
    if not token:
        raise AuthenticationError("No token received from login service")
    
    try:
        # Verify token with login service
        verify_url = f"{current_app.config['LOGIN_SERVICE_URL']}/verify"
        resp = requests.get(
            verify_url,
            headers={'Authorization': token}
        )
        
        if resp.status_code != 200:
            raise AuthenticationError("Invalid token received from login service")
            
        # Store token in session
        session['token'] = token
        session['user'] = resp.json()
        
        # Redirect to profile service
        return redirect(current_app.config['PROFILE_SERVICE_URL'])
        
    except requests.exceptions.ConnectionError:
        raise ServiceUnavailableError("Login service is not available")
    except Exception as e:
        raise AuthenticationError(f"Error during callback: {str(e)}")

@auth_bp.route('/logout')
@error_handler
def logout():
    session.clear()
    return redirect(url_for('main.index'))

@auth_bp.route('/verify', methods=['GET'])
@token_required
def verify_token(current_user):
    return jsonify({
        'status': 'success',
        'message': 'Token is valid',
        'user': current_user
    })

# Remember to register this blueprint in __init__.py if you use it.