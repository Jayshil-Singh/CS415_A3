import logging
import logging.handlers
import os
import json
from datetime import datetime
from functools import wraps
from flask import request, current_app, g, session
from .logger import StructuredLogFormatter
from .audit_excel import AuditExcelExporter

class AuditLogger:
    """Audit logging system for tracking service interactions and operations"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the audit logger with the application"""
        # Create audit logs directory
        log_dir = os.path.join(app.root_path, 'logs', 'audit')
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure audit file handler
        audit_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, 'audit.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10
        )
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(StructuredLogFormatter())
        
        # Create audit logger
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(audit_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
        
        # Store logger in app context
        app.audit_logger = self.logger
        
        # Initialize Excel exporter
        self.excel_exporter = AuditExcelExporter(app)

def audit_log(action, service=None, resource=None, status='success', details=None):
    """Log an audit event"""
    if not current_app.audit_logger:
        return
        
    # Get user information if available
    user_id = session.get('user_id') if session else None
    username = session.get('username') if session else None
    
    # Build audit record
    audit_record = {
        'timestamp': datetime.utcnow().isoformat(),
        'action': action,
        'service': service,
        'resource': resource,
        'status': status,
        'user_id': user_id,
        'username': username,
        'ip_address': request.remote_addr,
        'request_id': g.request_id if hasattr(g, 'request_id') else None,
        'user_agent': request.user_agent.string if request.user_agent else None
    }
    
    # Add request details
    if request:
        audit_record.update({
            'method': request.method,
            'path': request.path,
            'endpoint': request.endpoint,
            'query_params': dict(request.args)
        })
        
        # Add request body for non-GET requests
        if request.method != 'GET' and request.is_json:
            audit_record['request_body'] = request.get_json()
    
    # Add additional details
    if details:
        audit_record['details'] = details
    
    # Log to file
    current_app.audit_logger.info(
        f"Audit: {action} - {service} - {resource}",
        extra=audit_record
    )
    
    # Export to Excel
    if hasattr(current_app, 'audit_excel_exporter'):
        current_app.audit_excel_exporter.export_log(audit_record)

def audit_service(service_name):
    """Decorator for auditing service interactions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get resource from kwargs or args
            resource = kwargs.get('resource_id') or kwargs.get('id') or args[0] if args else None
            
            try:
                # Call the service function
                result = f(*args, **kwargs)
                
                # Log successful service interaction
                audit_log(
                    action=f.__name__,
                    service=service_name,
                    resource=str(resource),
                    status='success',
                    details={'result': result} if result else None
                )
                
                return result
            except Exception as e:
                # Log failed service interaction
                audit_log(
                    action=f.__name__,
                    service=service_name,
                    resource=str(resource),
                    status='error',
                    details={
                        'error': str(e),
                        'error_type': e.__class__.__name__
                    }
                )
                raise
        
        return decorated_function
    return decorator

def audit_operation(operation_type):
    """Decorator for auditing specific operations"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get resource from kwargs or args
            resource = kwargs.get('resource_id') or kwargs.get('id') or args[0] if args else None
            
            try:
                # Call the operation function
                result = f(*args, **kwargs)
                
                # Log successful operation
                audit_log(
                    action=operation_type,
                    service=f.__module__.split('.')[-1],
                    resource=str(resource),
                    status='success',
                    details={'result': result} if result else None
                )
                
                return result
            except Exception as e:
                # Log failed operation
                audit_log(
                    action=operation_type,
                    service=f.__module__.split('.')[-1],
                    resource=str(resource),
                    status='error',
                    details={
                        'error': str(e),
                        'error_type': e.__class__.__name__
                    }
                )
                raise
        
        return decorated_function
    return decorator 