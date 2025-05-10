# File: C:\Users\yashp\Documents\CS415\CS415_A3\main_app\run_main_app.py\main_app_packages\routes.py
import os
from flask import jsonify, request, send_from_directory
# Assuming student_profiles and allowed_file are correctly importable.
# This might need adjustment based on your project's Python path setup.
# If 'profile_service' is a sibling to 'main_app', and 'CS415_A3' is the project root in PYTHONPATH:
# from profile_service.run_profile_service import student_profiles, allowed_file
# For now, keeping your existing import style.
from profile_service.run_profile_service import student_profiles
from profile_service.run_profile_service import allowed_file

# This line imports the 'app' instance from app.py in the current directory (.)
from .app import app

# --- Existing API Routes (Profile Management) ---
@app.route('/profile/<student_id>', methods=['GET'])
def get_profile(student_id):
    # --- Authentication (Placeholder) ---
    # if not authenticate_request():
    #     return jsonify({"error": "Unauthorized"}), 401

    profile = student_profiles.get(student_id)
    if not profile:
        return jsonify({"error": "Student profile not found"}), 404
    return jsonify(profile)

@app.route('/profile/<student_id>/picture', methods=['POST'])
def upload_profile_picture(student_id):
    # --- Authentication (Placeholder) ---
    # if not authenticate_request():
    #     return jsonify({"error": "Unauthorized"}), 401

    if student_id not in student_profiles:
        return jsonify({"error": "Student profile not found"}), 404

    if 'photo' not in request.files:
        return jsonify({"error": "No photo file part"}), 400
    file = request.files['photo']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename): # Ensure allowed_file uses app.config['ALLOWED_EXTENSIONS']
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{student_id}.{ext}"
        
        if 'UPLOAD_FOLDER' not in app.config or not app.config['UPLOAD_FOLDER']:
            return jsonify({"error": "UPLOAD_FOLDER not configured"}), 500
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(filepath)
            profile_pic_url = f"/profile_pics/{filename}"
            student_profiles[student_id]['profile_pic_url'] = profile_pic_url
            return jsonify({"message": "Profile picture updated successfully", "profile_pic_url": profile_pic_url}), 200
        except Exception as e:
            print(f"Error saving file: {e}")
            return jsonify({"error": "Could not save file"}), 500
    else:
        return jsonify({"error": "File type not allowed"}), 400
    
@app.route('/profile_pics/<filename>')
def get_profile_pic(filename):
    if 'UPLOAD_FOLDER' not in app.config or not app.config['UPLOAD_FOLDER']:
        return jsonify({"error": "UPLOAD_FOLDER not configured"}), 404
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- Add other routes as needed ---
