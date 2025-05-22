from flask import jsonify, render_template, current_app, request
import traceback
from functools import wraps
from .logger import log_error
from werkzeug.exceptions import HTTPException

class CustomError(Exception):
    """Base class for custom exceptions"""
    def __init__(self, message, status_code=500, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status'] = 'error'
        return rv

class AuthenticationError(CustomError):
    """Raised when authentication fails"""
    def __init__(self, message="Authentication failed", payload=None):
        super().__init__(message, status_code=401, payload=payload)

class AuthorizationError(CustomError):
    """Raised when user is not authorized to access a resource"""
    def __init__(self, message="Not authorized to access this resource", payload=None):
        super().__init__(message, status_code=403, payload=payload)

class ResourceNotFoundError(CustomError):
    """Raised when a requested resource is not found"""
    def __init__(self, message="Resource not found", payload=None):
        super().__init__(message, status_code=404, payload=payload)

class ValidationError(CustomError):
    """Raised when input validation fails"""
    def __init__(self, message="Validation failed", payload=None):
        super().__init__(message, status_code=400, payload=payload)

class ServiceUnavailableError(CustomError):
    """Raised when a required service is unavailable"""
    def __init__(self, message="Service temporarily unavailable", payload=None):
        super().__init__(message, status_code=503, payload=payload)

def handle_error(error):
    """Handle custom errors"""
    if isinstance(error, HTTPException):
        response = {
            'error': error.name,
            'message': error.description,
            'status_code': error.code
        }
    else:
        response = {
            'error': 'Internal Server Error',
            'message': str(error),
            'status_code': 500
        }
    
    log_error(error)
    
    if request.is_json:
        return jsonify(response), response['status_code']
    return render_template('error.html', error=response), response['status_code']

def handle_500_error(error):
    """Handle 500 errors"""
    log_error(error)
    if request.is_json:
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500
    return render_template('error.html', error={
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'status_code': 500
    }), 500

def handle_404_error(error):
    """Handle 404 errors"""
    log_error(error)
    if request.is_json:
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status_code': 404
        }), 404
    return render_template('404.html'), 404

def error_handler(f):
    """Decorator for handling exceptions in route handlers"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except CustomError as e:
            return handle_error(e)
        except Exception as e:
            return handle_500_error(e)
    return decorated_function 