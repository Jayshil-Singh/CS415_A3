import os
from flask import app, jsonify, request, send_from_directory

from profile_service.run_profile_service import allowed_file


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

    # Check if the post request has the file part
    if 'photo' not in request.files:
        return jsonify({"error": "No photo file part"}), 400
    file = request.files['photo']

    # If the user does not select a file, the browser submits an empty file without a filename.
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        # Create a predictable filename using student_id
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{student_id}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            file.save(filepath)
            # Update the profile data with the new URL
            profile_pic_url = f"/profile_pics/{filename}" # Relative URL path
            student_profiles[student_id]['profile_pic_url'] = profile_pic_url
            return jsonify({"message": "Profile picture updated successfully", "profile_pic_url": profile_pic_url}), 200
        except Exception as e:
            # Log the error e in a real app
            return jsonify({"error": "Could not save file"}), 500
    else:
        return jsonify({"error": "File type not allowed"}), 400
    
# Needs: from flask import send_from_directory
# Needs: import os
@app.route('/profile_pics/<filename>')
def get_profile_pic(filename):
    # Serves the uploaded pictures from the configured UPLOAD_FOLDER
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)