from flask import Flask, request, jsonify, send_from_directory
import os
import secrets # For generating secure random strings (like API keys)

app = Flask(__name__)

# --- Configuration ---
# In a real app, use environment variables or a config file
UPLOAD_FOLDER = 'profile_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# This is a placeholder. In a real app, store keys securely and validate properly.
VALID_API_KEYS = {"your_main_app_key_here": "MainApp"} # Simulate API key validation

# --- Ensure upload directory exists ---
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- Sample Data (Replace with Database) ---
# Using student_id as the key
student_profiles = {
    "s12345678": {
        "first_name": "Jane",
        "middle_name": "",
        "last_name": "Doe",
        "dob": "2003-05-15",
        "gender": "Female",
        "citizenship": "Fijian",
        "program": "Bachelor of Science",
        "student_level": "Undergraduate",
        "student_campus": "Laucala Campus, Suva, Fiji",
        "email": "s12345678@student.usp.ac.fj",
        "phone": "+679 123 4567",
        "address": {
            "street": "123 University Way", "city": "Suva", "state": "Central", "country": "Fiji", "postal_code": "0000"
        },
        "passport_visa": {
            "passport_number": "P123456", "visa_status": "Student Visa", "expiry_date": "2026-12-31"
        },
        "profile_pic_url": None # URL to the profile picture file
    }
    # Add more student profiles as needed
}

# --- Helper Functions ---
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def authenticate_request():
    """ Placeholder for API Key Authentication """
    api_key = request.headers.get('X-API-Key')
    if api_key and api_key in VALID_API_KEYS:
        return True
    return False

# --- API Endpoints ---
@app.route('/profile/<student_id>', methods=['GET'])
def get_profile(student_id):
    # --- Authentication ---
    # if not authenticate_request():
    #     return jsonify({"error": "Unauthorized"}), 401

    profile = student_profiles.get(student_id)
    if not profile:
        return jsonify({"error": "Student profile not found"}), 404
    return jsonify(profile)

@app.route('/profile/<student_id>/picture', methods=['POST'])
def upload_profile_picture(student_id):
    # --- Authentication ---
    # if not authenticate_request():
    #     return jsonify({"error": "Unauthorized"}), 401

    if student_id not in student_profiles:
        return jsonify({"error": "Student profile not found"}), 404

    if 'photo' not in request.files:
        return jsonify({"error": "No photo file part"}), 400
    file = request.files['photo']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        # Secure filename and create a unique name to avoid conflicts
        # Using student_id ensures each student has one picture, overwriting previous
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{student_id}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            # --- (Optional) Delete old picture if exists with different extension ---
            # You might want to find and delete any existing file for this student_id
            # e.g., if they upload a .png replacing a .jpg
            # ---
            file.save(filepath)
            # Update the profile data with the new URL (relative path for simplicity)
            profile_pic_url = f"/profile_pics/{filename}" # URL path served by get_profile_pic
            student_profiles[student_id]['profile_pic_url'] = profile_pic_url
            return jsonify({"message": "Profile picture updated successfully", "profile_pic_url": profile_pic_url}), 200
        except Exception as e:
             # Log the error e
            return jsonify({"error": "Could not save file"}), 500
    else:
        return jsonify({"error": "File type not allowed"}), 400

@app.route('/profile_pics/<filename>')
def get_profile_pic(filename):
     # Serves the uploaded pictures
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- Running the App ---
if __name__ == '__main__':
    # Use host='0.0.0.0' to make it accessible on your network
    # Use a proper WSGI server like Gunicorn in production
    app.run(debug=True, port=5001) # Run on a different port than main app