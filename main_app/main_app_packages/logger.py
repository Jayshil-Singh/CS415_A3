import logging
import logging.handlers
import os
import json
from datetime import datetime
from functools import wraps
import traceback
from flask import request, current_app, g

class StructuredLogFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    def format(self, record):
        # Create base log record
        log_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add request information if available
        if hasattr(g, 'request_id'):
            log_record['request_id'] = g.request_id
            
        # Add exception information if available
        if record.exc_info:
            log_record['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
            
        # Add extra fields if available
        if hasattr(record, 'extra'):
            log_record.update(record.extra)
            
        return json.dumps(log_record)

def setup_logger(app):
    """Configure logging for the application"""
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(app.root_path, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure file handlers
    error_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, 'error.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredLogFormatter())
    
    access_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, 'access.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(StructuredLogFormatter())
    
    # Configure console handler for development
    if app.debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(StructuredLogFormatter())
        app.logger.addHandler(console_handler)
    
    # Add handlers to app logger
    app.logger.addHandler(error_handler)
    app.logger.addHandler(access_handler)
    app.logger.setLevel(logging.INFO)

def log_error(error, context=None):
    """Log an error with additional context"""
    extra = {
        'error_type': error.__class__.__name__,
        'error_message': str(error),
        'context': context or {}
    }
    
    if hasattr(error, 'status_code'):
        extra['status_code'] = error.status_code
        
    if hasattr(error, 'payload'):
        extra['payload'] = error.payload
        
    current_app.logger.error(
        f"Error occurred: {str(error)}",
        exc_info=True,
        extra=extra
    )

def log_request():
    """Log request information"""
    extra = {
        'method': request.method,
        'path': request.path,
        'remote_addr': request.remote_addr,
        'user_agent': request.user_agent.string,
        'referrer': request.referrer,
        'query_params': dict(request.args),
        'request_id': g.request_id
    }
    
    # Log request body for non-GET requests
    if request.method != 'GET' and request.is_json:
        extra['request_body'] = request.get_json()
    
    current_app.logger.info(
        f"Request: {request.method} {request.path}",
        extra=extra
    )

def log_response(response):
    """Log response information"""
    extra = {
        'status_code': response.status_code,
        'request_id': g.request_id
    }
    
    # Log response body for error responses
    if response.status_code >= 400 and response.is_json:
        extra['response_body'] = response.get_json()
    
    current_app.logger.info(
        f"Response: {response.status_code}",
        extra=extra
    )

def request_logger(f):
    """Decorator to log request and response information"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Generate request ID
        g.request_id = os.urandom(8).hex()
        
        # Log request
        log_request()
        
        try:
            response = f(*args, **kwargs)
            # Log response
            log_response(response)
            return response
        except Exception as e:
            # Log error
            log_error(e, {
                'request_id': g.request_id,
                'endpoint': request.endpoint,
                'args': args,
                'kwargs': kwargs
            })
            raise
    
    return decorated_function 