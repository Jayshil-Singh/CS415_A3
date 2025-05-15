# File: C:\Users\yashp\Documents\CS415\CS415_A3\main_app\run_main_app.py\main_app_packages\app.py
import os
import xml.etree.ElementTree as ET
from flask import (
    Flask, jsonify, request, send_from_directory, render_template,
    redirect, url_for, flash, abort, session # Added session import
)
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException # Correctly imported
from types import SimpleNamespace

app = Flask (
    __name__,
    # Assuming 'templates' and 'static' are direct subdirectories of 'main_app_packages'
    template_folder="templates",
    static_folder="static"
)

# --- Application Configuration ---
# CRITICAL SECURITY: Ensure this key is strong, random, and kept secret, ideally set via environment variable.
# The default provided here is INSECURE for production.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key_v6_CHANGE_THIS_NOW_TO_SOMETHING_STRONG')
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 't']

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER_PATH = os.path.join(BASE_DIR, 'profile_pictures_storage')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER_PATH
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

DATA_FOLDER = os.path.join(BASE_DIR, 'xml_data')


# --- User Context Injection ---
@app.context_processor
def inject_user():
    # Basic user injection based on session.
    # For a real app, use Flask-Login or similar for robust session management.
    if 'email' in session:
        # You might want to fetch more user details from a database here
        return {"current_user": SimpleNamespace(username=session['email'], user_type=session.get('user_type'))}
    return {"current_user": SimpleNamespace(username="Guest")} # Or specific default like "Student" if unauthenticated


# --- "Shivya's Code" Section (Modified) ---

# RECTIFICATION NOTE: Shivya's original login route at "/" is commented out
# to avoid conflict with Yash's "/" and "/login" routes.
# A single, unified login mechanism should be implemented.
#
# # ——— Login (entry point) - SHIVYA'S ORIGINAL - NOW COMMENTED OUT ———
# @app.route("/", methods=["GET", "POST"])
# def login_shivya_original(): # Renamed to avoid conflict, but effectively unused now
#     try:
#         error = None
#         if request.method == "POST":
#             email    = request.form.get("email", "").strip()
#             password = request.form.get("password", "")
#             # CRITICAL SECURITY FLAW: Hardcoded password and basic validation
#             if not email.lower().startswith("s") or not email.lower().endswith("@student.usp.ac.fj"):
#                 error = "Enter a valid S12345678@student.usp.ac.fj email"
#             elif password != "password123": # NEVER use hardcoded passwords in real applications
#                 error = "Invalid password"
#             else:
#                 # For a real login, you would set up a session here
#                 session['user_id'] = email # Example
#                 session['role'] = 'student' # Example
#                 return redirect(url_for("home")) # Assuming 'home' is the student dashboard
#         return render_template("login.html", error=error)
#     except Exception:
#         abort(500)


# ——— Homepage ———
@app.route("/home") # This might be intended as a student homepage
def home():
    # Add authentication check here if this is a protected route
    # For example: if 'user_id' not in session: return redirect(url_for('login'))
    return render_template("homepage.html")

# ——— Student Profile ———
@app.route("/profile") # This might be intended as a student profile page
def student_profile():
    # Add authentication check
    return render_template("studentProfile.html")

# ——— My Enrollment ———
@app.route("/myEnrollment")
def my_enrollment():
    # Add authentication check
    return render_template("myEnrollment.html")

# ——— Courses ———
@app.route("/courses")
def courses():
    # Add authentication check
    return render_template("courses.html")

# ——— Finance ———
@app.route("/finance")
def finance():
    # Add authentication check
    return render_template("finance.html")


# --- "Yash Code" Section (Modified for basic session and clarity) ---

# --- Helper Functions ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_data_from_xml(filename, list_element_name, item_element_name,
                      value_attribute=None,
                      sub_item_map=None): # sub_item_map is for hierarchical data
    xml_file_path = os.path.join(DATA_FOLDER, filename)
    data = []
    data_dict = {} # Only used if sub_item_map is provided
    app.logger.debug(f"Attempting to parse XML file: {xml_file_path}")

    try:
        if not os.path.exists(xml_file_path):
            app.logger.error(f"XML data file not found at path: {xml_file_path}")
            return data if sub_item_map is None else data_dict

        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        app.logger.debug(f"XML Root element for {filename}: <{root.tag}>")

        item_container = root
        if root.tag != list_element_name:
            item_container = root.find(list_element_name)
            if item_container is None:
                app.logger.warning(f"List element <{list_element_name}> not found directly under root <{root.tag}> in {filename}. Will search for <{item_element_name}> under root.")
                item_container = root

        if item_container is None:
            app.logger.error(f"Could not find item container <{list_element_name}> or root for items in {filename}")
            return data if sub_item_map is None else data_dict

        app.logger.debug(f"Using container <{item_container.tag}> to find <{item_element_name}> items in {filename}")

        if sub_item_map:
            parent_id_tag_or_attr = sub_item_map['parent_id_tag_or_attr']
            parent_id_is_attribute = sub_item_map.get('parent_id_is_attribute', False)
            sub_item_list_tag = sub_item_map['sub_item_list_tag']
            sub_item_tag = sub_item_map['sub_item_tag']
            sub_item_value_attribute = sub_item_map.get('sub_item_value_attribute')

            parent_nodes_found = item_container.findall(item_element_name)
            app.logger.debug(f"Found {len(parent_nodes_found)} <{item_element_name}> parent nodes under <{item_container.tag}> in {filename}")

            for i, parent_node in enumerate(parent_nodes_found):
                parent_id = None
                if parent_id_is_attribute:
                    parent_id = parent_node.get(parent_id_tag_or_attr)
                else:
                    parent_id_element = parent_node.find(parent_id_tag_or_attr)
                    if parent_id_element is not None and parent_id_element.text:
                        parent_id = parent_id_element.text.strip()

                if parent_id:
                    app.logger.debug(f"  Parent item {i+1} ID ('{parent_id_tag_or_attr}'): {parent_id}")
                    sub_items_list = []
                    sub_items_container = parent_node.find(sub_item_list_tag)
                    if sub_items_container is not None:
                        sub_item_nodes_found = sub_items_container.findall(sub_item_tag)
                        app.logger.debug(f"    Found {len(sub_item_nodes_found)} <{sub_item_tag}> sub-items in <{sub_item_list_tag}>")
                        for j, sub_item_node in enumerate(sub_item_nodes_found):
                            sub_text = None
                            if sub_item_value_attribute:
                                sub_text = sub_item_node.get(sub_item_value_attribute)
                            elif sub_item_node.text:
                                sub_text = sub_item_node.text.strip()

                            if sub_text:
                                sub_items_list.append(sub_text)
                                app.logger.debug(f"      Sub-item {j+1}: {sub_text}")
                            else:
                                app.logger.debug(f"      Sub-item {j+1} <{sub_item_tag}> has no text/attribute '{sub_item_value_attribute}'.")
                    else:
                        app.logger.debug(f"    No <{sub_item_list_tag}> container found for parent ID {parent_id}")
                    data_dict[parent_id] = sub_items_list
                else:
                    app.logger.debug(f"  Parent item {i+1} <{item_element_name}> missing ID via '{parent_id_tag_or_attr}' (is_attribute={parent_id_is_attribute}).")
            return data_dict
        else:
            item_nodes_found = item_container.findall(item_element_name)
            app.logger.debug(f"Found {len(item_nodes_found)} <{item_element_name}> items in {filename} under <{item_container.tag}>")
            for i, item_node in enumerate(item_nodes_found):
                item_text = None
                if value_attribute:
                    item_text = item_node.get(value_attribute)
                elif item_node.text:
                    item_text = item_node.text.strip()

                if item_text:
                    data.append(item_text)
                    app.logger.debug(f"  Item {i+1}: {item_text}")
                else:
                    app.logger.debug(f"  Item {i+1} <{item_element_name}> has no text or attribute '{value_attribute}'.")
            return data
    except Exception as e:
        app.logger.error(f"An unexpected error occurred while parsing {xml_file_path}: {e}", exc_info=True)
    return data if sub_item_map is None else data_dict


# --- Import Profile Service Data ---
# IMPORTANT: This data is in-memory and will be lost on app restart.
# For a real application, use a database.
try:
    # Assuming profile_service is a module you have locally.
    # This structure implies 'run_profile_service.py' exists within a 'profile_service' package.
    from profile_service.run_profile_service import student_profiles
except ImportError:
    app.logger.warning("Could not import 'student_profiles' from profile_service. Using dummy data.")
    student_profiles = {'s12345': {'firstName': 'Test', 'lastName': 'User', 'profile_pic_url': None}}


# --- Routes (Yash's version, with basic session handling) ---
@app.route('/') # Main entry point, shows login
def index():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login(): # This is now the primary login route
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # CRITICAL SECURITY FLAW: Never use hardcoded passwords in a real application!
        # Implement proper password hashing and user database.
        # The following is for demonstration of different roles ONLY.
        user_type_redirects = {
            ("staff@example.com", "password"): ("sas_staff_home", "staff"),
            ("manager@example.com", "password"): ("sas_manager_home", "manager"),
            ("admin@example.com", "password"): ("super_admin_home", "admin"),
            # Add Shivya's student login here if desired, e.g.:
            # (student_email_from_form, "password123"): ("home", "student")
            # This would require modifying the logic to check student email format first.
        }

        user_creds = (email, password)
        if user_creds in user_type_redirects:
            redirect_route, user_type = user_type_redirects[user_creds]
            session['email'] = email
            session['user_type'] = user_type
            flash(f"Successfully logged in as {user_type}.", "success")
            return redirect(url_for(redirect_route))
        # Check for Shivya's original student login logic (example integration)
        elif email and email.lower().startswith("s") and email.lower().endswith("@student.usp.ac.fj") and password == "password123":
            session['email'] = email
            session['user_type'] = 'student'
            flash("Successfully logged in as student.", "success")
            return redirect(url_for("home")) # 'home' is student dashboard
        else:
            flash("Invalid email or password. Please try again.", "error")
            # No need to also pass error to render_template if using flash
            return render_template('login.html')
    return render_template('login.html')

# --- Logout ---
@app.route("/logout")
def logout():
    session.pop('email', None)
    session.pop('user_type', None)
    # session.clear() # Alternatively, clear the entire session
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route('/profile/<student_id>', methods=['GET'])
def get_profile_api(student_id): # Renamed to avoid conflict with student_profile view function
    # This should ideally fetch from a persistent database
    profile = student_profiles.get(student_id)
    if not profile:
        return jsonify({"error": "Student profile not found"}), 404
    return jsonify(profile)

@app.route('/profile/<student_id>/picture', methods=['POST'])
def upload_profile_picture(student_id):
    # Authentication and Authorization needed: who can upload pictures for whom?
    if student_id not in student_profiles: # Check against your data source
        return jsonify({"error": "Student profile not found"}), 404

    if 'photo' not in request.files:
        return jsonify({"error": "No photo file part"}), 400
    file = request.files['photo']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"{student_id}.{ext}") # Good use of secure_filename

        if not app.config['UPLOAD_FOLDER']:
            app.logger.error("UPLOAD_FOLDER not configured.")
            return jsonify({"error": "File upload path not configured"}), 500

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(filepath)
            # IMPORTANT: Storing profile_pic_url in an in-memory dict is not persistent.
            profile_pic_url = url_for('get_profile_pic', filename=filename, _external=True)
            if student_id in student_profiles: # Ensure student exists before updating
                 student_profiles[student_id]['profile_pic_url'] = profile_pic_url
            # In a real app: Update database record for student_id with profile_pic_url
            return jsonify({"message": "Profile picture updated successfully", "profile_pic_url": profile_pic_url}), 200
        except Exception as e:
            app.logger.error(f"Error saving file {filename}: {e}", exc_info=True)
            return jsonify({"error": "Could not save file"}), 500
    return jsonify({"error": "File type not allowed"}), 400

@app.route('/profile_pics/<filename>')
def get_profile_pic(filename):
    if not app.config['UPLOAD_FOLDER']:
        app.logger.error("UPLOAD_FOLDER not configured.")
        # Return a 404 for resource not found if path is not configured or file doesn't exist
        abort(404)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# --- SAS Specific Routes ---
# These routes should ideally have authentication decorators (e.g., @login_required, @roles_required('manager'))

@app.route('/sas-manager/home')
def sas_manager_home():
    # if session.get('user_type') != 'manager': abort(403) # Example authorization
    return render_template('SASManager/homeSAS.html')

@app.route('/sas-staff/home')
def sas_staff_home():
    # if session.get('user_type') != 'staff': abort(403) # Example authorization
    return render_template('SASStaff/homeStaff.html')

@app.route('/sas-staff/edit-student')
def sas_staff_edit_student():
    # if session.get('user_type') != 'staff': abort(403)
    return render_template('SASStaff/editST.html')

@app.route('/sas-staff/register-student')
def sas_staff_register_student():
    # if session.get('user_type') != 'staff': abort(403)
    programs_list = get_data_from_xml(
        filename='programs.xml',
        list_element_name='programs',
        item_element_name='program',
        value_attribute='programName'
    )
    all_subprogrammes_list = get_data_from_xml(
        filename='subprogrammes.xml',
        list_element_name='subprograms',
        item_element_name='subprogram',
        value_attribute='subprogramName'
    )
    campuses_list = get_data_from_xml(
        filename='campuses.xml',
        list_element_name='campuses',
        item_element_name='campus',
        value_attribute='campusName'
    )
    app.logger.debug(f"Final Programs loaded for template: {programs_list}")
    app.logger.debug(f"Flat list of all subprogrammes loaded: {all_subprogrammes_list}")
    app.logger.debug(f"Final Campuses loaded for template: {campuses_list}")

    return render_template(
        'SASStaff/registerST.html',
        programs=programs_list,
        subprograms_map={}, # As per original, JS might need adaptation
        all_subprogrammes=all_subprogrammes_list,
        campuses=campuses_list
    )

@app.route('/super-admin/home')
def super_admin_home():
    # if session.get('user_type') != 'admin': abort(403)
    return render_template('SuperAdmin/SAdminHome.html')

@app.route('/super-admin/remove-staff')
def super_admin_remove_staff():
    # if session.get('user_type') != 'admin': abort(403)
    return render_template('SuperAdmin/RemoveStaff.html')


# --- Error Handlers ---
@app.errorhandler(404)
def handle_404(e):
    app.logger.warning(f"Handling 404 error for path: {request.path}. Error: {e}")
    return render_template("errors/404.html"), 404

@app.errorhandler(500)
def handle_500(e):
    app.logger.error(f"Handling 500 error for path: {request.path}. Error: {e}", exc_info=True)
    return render_template("errors/500.html"), 500

@app.errorhandler(HTTPException) # More specific for HTTP errors
def handle_http_exception(e):
    # This will handle errors raised by abort(code) or other HTTPExceptions
    app.logger.warning(f"Handling HTTPException code {e.code} for path: {request.path}. Description: {e.description}")
    if e.code == 404:
        return render_template("errors/404.html"), 404
    if e.code == 500: # Should be caught by handle_500 if it's a direct 500
        return render_template("errors/500.html"), 500
    # You can add more specific templates for other HTTP error codes e.g. 403.html
    # For now, a generic error page or the error's own description
    return render_template("errors/generic_http_error.html", error=e), e.code

@app.errorhandler(Exception) # Catch-all for any other uncaught Python exceptions
def handle_all_other_exceptions(e):
    # This should not catch HTTPErrors if handle_http_exception is defined before it.
    # However, explicit check is safer.
    if isinstance(e, HTTPException):
        return e # Let the HTTPException handler do its job.
    
    # For any non-HTTP exception, log it and show a generic 500 error page.
    app.logger.error(f"Unhandled Exception for path: {request.path}. Error: {e}", exc_info=True)
    return render_template("errors/500.html"), 500


# --- Main Execution Block ---
if __name__ == '__main__':
    # Create upload and data folders if they don't exist at startup
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        app.logger.info(f"Created UPLOAD_FOLDER at {app.config['UPLOAD_FOLDER']}")
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER, exist_ok=True)
        app.logger.info(f"Created DATA_FOLDER at {DATA_FOLDER}. Place XML files here.")

    app.logger.info(f"Flask App '{__name__}' starting...")
    app.logger.info(f"Debug mode: {app.debug}")
    app.logger.info(f"Template folder: {app.template_folder}")
    app.logger.info(f"Static folder: {app.static_folder}")
    app.logger.info(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    app.logger.info(f"Data folder (for XMLs): {DATA_FOLDER}")
    
    app.run(host='0.0.0.0', port=5000) # debug=app.debug is implicitly handled