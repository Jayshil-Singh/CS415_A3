from flask import Blueprint, request, jsonify, current_app, render_template
from ..auth import token_required
from ..error_handlers import error_handler, AuthorizationError, ResourceNotFoundError, ValidationError, ServiceUnavailableError
import requests

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@main_bp.route('/student_profile/<student_id>', methods=['GET'])
@token_required
@error_handler
def get_profile(current_user, student_id):
    if current_user['user_id'] != student_id:
        raise AuthorizationError("You are not authorized to view this profile")
        
    try:
        resp = requests.get(f"{current_app.config['PROFILE_SERVICE_URL']}/profile/{student_id}")
        if resp.status_code == 200:
            profile_data = resp.json()
            return render_template('profile_details.html', profile_data=profile_data, current_user=current_user)
        elif resp.status_code == 404:
            raise ResourceNotFoundError("Profile not found")
        else:
            raise ServiceUnavailableError("Profile service returned an error")
    except requests.exceptions.ConnectionError:
        raise ServiceUnavailableError("Profile service is not available")
    except Exception as e:
        raise ServiceUnavailableError(f"Error accessing profile service: {str(e)}")

@main_bp.route('/profile/<student_id>/picture', methods=['POST'])
@token_required
@error_handler
def upload_profile_picture(current_user, student_id):
    if current_user['user_id'] != student_id:
        raise AuthorizationError("You are not authorized to update this profile")
        
    if 'photo' not in request.files:
        raise ValidationError("No photo file provided")
        
    file = request.files['photo']
    if not file or not file.filename:
        raise ValidationError("No selected file")
        
    # Validate file type
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    if not file.filename.lower().endswith(tuple(allowed_extensions)):
        raise ValidationError(f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}")
        
    try:
        files = {'photo': (file.filename, file.stream, file.mimetype)}
        resp = requests.post(f"{current_app.config['PROFILE_SERVICE_URL']}/profile/{student_id}/picture", files=files)
        
        if resp.status_code == 200:
            return jsonify({"message": "Profile picture updated successfully"}), 200
        elif resp.status_code == 404:
            raise ResourceNotFoundError("Profile not found")
        else:
            raise ServiceUnavailableError("Profile service returned an error")
    except requests.exceptions.ConnectionError:
        raise ServiceUnavailableError("Profile service is not available")
    except Exception as e:
        raise ServiceUnavailableError(f"Error uploading profile picture: {str(e)}")

@main_bp.route('/profile_pics/<filename>')
@token_required
@error_handler
def get_profile_pic(current_user, filename):
    try:
        resp = requests.get(f"{current_app.config['PROFILE_SERVICE_URL']}/profile_pics/{filename}", stream=True)
        if resp.status_code == 200:
            return (resp.content, resp.status_code, resp.headers.items())
        elif resp.status_code == 404:
            raise ResourceNotFoundError("Profile picture not found")
        else:
            raise ServiceUnavailableError("Profile service returned an error")
    except requests.exceptions.ConnectionError:
        raise ServiceUnavailableError("Profile service is not available")
    except Exception as e:
        raise ServiceUnavailableError(f"Error retrieving profile picture: {str(e)}")

@main_bp.route('/api/search')
@token_required
@error_handler
def search(current_user):
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        raise ValidationError("Search query must be at least 2 characters long")
        
    try:
        # Search in profile service
        profile_resp = requests.get(
            f"{current_app.config['PROFILE_SERVICE_URL']}/search",
            params={'q': query}
        )
        
        results = []
        if profile_resp.status_code == 200:
            results.extend(profile_resp.json())
            
        return jsonify(results)
    except requests.exceptions.ConnectionError:
        raise ServiceUnavailableError("Search service is not available")
    except Exception as e:
        raise ServiceUnavailableError(f"Error performing search: {str(e)}") 