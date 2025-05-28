from flask import Blueprint, send_file, jsonify, current_app
from ..auth import login_required, admin_required
import os

audit_bp = Blueprint('audit', __name__, url_prefix='/audit')

@audit_bp.route('/download/latest', methods=['GET'])
@login_required
@admin_required
def download_latest_audit_logs():
    """Download the latest audit log Excel file"""
    try:
        latest_file = current_app.audit_excel_exporter.get_latest_export()
        if not latest_file or not os.path.exists(latest_file):
            return jsonify({
                'status': 'error',
                'message': 'No audit logs available'
            }), 404
            
        return send_file(
            latest_file,
            as_attachment=True,
            download_name=os.path.basename(latest_file),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error downloading audit logs: {str(e)}'
        }), 500

@audit_bp.route('/list', methods=['GET'])
@login_required
@admin_required
def list_audit_logs():
    """List all available audit log Excel files"""
    try:
        files = current_app.audit_excel_exporter.get_all_exports()
        return jsonify({
            'status': 'success',
            'files': [
                {
                    'filename': os.path.basename(f),
                    'path': f,
                    'size': os.path.getsize(f),
                    'created': os.path.getctime(f)
                }
                for f in files
            ]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error listing audit logs: {str(e)}'
        }), 500

@audit_bp.route('/download/<filename>', methods=['GET'])
@login_required
@admin_required
def download_audit_log(filename):
    """Download a specific audit log Excel file"""
    try:
        file_path = os.path.join(
            current_app.audit_excel_exporter.export_dir,
            filename
        )
        
        if not os.path.exists(file_path):
            return jsonify({
                'status': 'error',
                'message': 'File not found'
            }), 404
            
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error downloading audit log: {str(e)}'
        }), 500 