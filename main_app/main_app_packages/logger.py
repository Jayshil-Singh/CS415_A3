import logging
import logging.handlers
import os
import json
from datetime import datetime
from functools import wraps
import traceback
from flask import request, current_app, g, has_request_context
import uuid
import time

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
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure file handler
    file_handler = logging.FileHandler(os.path.join(log_dir, 'app.log'))
    file_handler.setLevel(logging.INFO)
    
    # Configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configure Flask logger
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)

def log_request(logger_func):
    """Log request details"""
    if not has_request_context():
        return
        
    request_id = str(uuid.uuid4())
    g.request_id = request_id
    
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'level': 'INFO',
        'message': f'Request: {request.method} {request.path}',
        'module': 'logger',
        'function': 'log_request',
        'line': 112,
        'request_id': request_id,
        'method': request.method,
        'path': request.path,
        'remote_addr': request.remote_addr,
        'user_agent': request.user_agent.string,
        'headers': dict(request.headers)
    }
    
    logger_func(json.dumps(log_data))

def log_response(response):
    """Log response details"""
    if not has_request_context():
        return
        
    request_id = getattr(g, 'request_id', None)
    if not request_id:
        return
        
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'level': 'INFO',
        'message': f'Response: {response.status_code}',
        'module': 'logger',
        'function': 'log_response',
        'line': 120,
        'request_id': request_id,
        'status_code': response.status_code,
        'headers': dict(response.headers)
    }
    
    logging.info(json.dumps(log_data))

def log_error(error):
    """Log error details"""
    if not has_request_context():
        return
        
    request_id = getattr(g, 'request_id', None)
    if not request_id:
        return
        
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'level': 'ERROR',
        'message': f'Error occurred: {str(error)}',
        'module': 'logger',
        'function': 'log_error',
        'line': 90,
        'request_id': request_id,
        'exception': {
            'type': type(error).__name__,
            'message': str(error),
            'traceback': error.__traceback__.tb_frame.f_code.co_filename
        }
    }
    
    logging.error(json.dumps(log_data))

def request_logger(logger_func):
    """Decorator to log request and response"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Log request
            log_request(logger_func)
            
            try:
                # Execute the route function
                response = f(*args, **kwargs)
                
                # Log response
                if response is not None:
                    log_response(response)
                    
                return response
            except Exception as e:
                # Log error
                log_error(e)
                raise
                
        return decorated_function
    return decorator 