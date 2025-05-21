import os
import pandas as pd
from datetime import datetime
from threading import Lock
from flask import current_app
import json

class AuditExcelExporter:
    """Handles real-time export of audit logs to Excel"""
    
    def __init__(self, app=None):
        self.app = app
        self.lock = Lock()
        self.current_file = None
        self.last_export_time = None
        self.export_interval = 300  # 5 minutes
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the Excel exporter with the application"""
        # Create export directory
        self.export_dir = os.path.join(app.root_path, 'exports', 'audit')
        os.makedirs(self.export_dir, exist_ok=True)
        
        # Create initial Excel file
        self._create_new_excel_file()
        
        # Store exporter in app context
        app.audit_excel_exporter = self
    
    def _create_new_excel_file(self):
        """Create a new Excel file with headers"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.current_file = os.path.join(self.export_dir, f'audit_logs_{timestamp}.xlsx')
        
        # Create DataFrame with headers
        df = pd.DataFrame(columns=[
            'timestamp', 'action', 'service', 'resource', 'status',
            'user_id', 'username', 'ip_address', 'request_id',
            'user_agent', 'method', 'path', 'endpoint',
            'query_params', 'request_body', 'details'
        ])
        
        # Save to Excel
        df.to_excel(self.current_file, index=False, engine='openpyxl')
        self.last_export_time = datetime.now()
    
    def _should_create_new_file(self):
        """Check if a new Excel file should be created"""
        if not self.last_export_time:
            return True
            
        time_diff = (datetime.now() - self.last_export_time).total_seconds()
        return time_diff >= self.export_interval
    
    def export_log(self, log_record):
        """Export a single log record to Excel"""
        with self.lock:
            try:
                # Check if we need a new file
                if self._should_create_new_file():
                    self._create_new_excel_file()
                
                # Convert log record to DataFrame row
                row_data = {
                    'timestamp': log_record.get('timestamp'),
                    'action': log_record.get('action'),
                    'service': log_record.get('service'),
                    'resource': log_record.get('resource'),
                    'status': log_record.get('status'),
                    'user_id': log_record.get('user_id'),
                    'username': log_record.get('username'),
                    'ip_address': log_record.get('ip_address'),
                    'request_id': log_record.get('request_id'),
                    'user_agent': log_record.get('user_agent'),
                    'method': log_record.get('method'),
                    'path': log_record.get('path'),
                    'endpoint': log_record.get('endpoint'),
                    'query_params': json.dumps(log_record.get('query_params', {})),
                    'request_body': json.dumps(log_record.get('request_body', {})),
                    'details': json.dumps(log_record.get('details', {}))
                }
                
                # Read existing Excel file
                df = pd.read_excel(self.current_file)
                
                # Append new row
                df = pd.concat([df, pd.DataFrame([row_data])], ignore_index=True)
                
                # Save back to Excel
                df.to_excel(self.current_file, index=False, engine='openpyxl')
                
                # Update last export time
                self.last_export_time = datetime.now()
                
            except Exception as e:
                current_app.logger.error(f"Error exporting audit log to Excel: {str(e)}")
    
    def get_latest_export(self):
        """Get the path to the latest export file"""
        return self.current_file
    
    def get_all_exports(self):
        """Get a list of all export files"""
        return sorted([
            os.path.join(self.export_dir, f)
            for f in os.listdir(self.export_dir)
            if f.startswith('audit_logs_') and f.endswith('.xlsx')
        ], reverse=True) 