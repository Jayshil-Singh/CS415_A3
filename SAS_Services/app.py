import os
import xml.etree.ElementTree as ET
from flask import (
    Flask, jsonify, request, send_from_directory, render_template,
    redirect, url_for, flash, abort, session
)
from werkzeug.utils import secure_filename # Kept for potential future use
from werkzeug.exceptions import HTTPException
from types import SimpleNamespace
from dotenv import load_dotenv
from functools import wraps

# --- Load Environment Variables from root .env file ---
# This assumes your app.py is in a subdirectory (e.g., SAS_Services)
# and the .env file is in the project root (parent directory).
APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)
DOTENV_PATH = os.path.join(PROJECT_ROOT, '.env')
load_dotenv(DOTENV_PATH)

app = Flask (
    __name__,
    template_folder="templates", # Should be 'SAS_Services/templates/'
    static_folder="static"      # Should be 'SAS_Services/static/'
)

# --- Application Configuration ---
# IMPORTANT: Set FLASK_SECRET_KEY_SAS in your .env file for security!
# Use a strong, random key. The default here is INSECURE.
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY_SAS', 'sas_services_strong_secret_key_CHANGE_THIS_V2_DEFAULT_INSECURE')
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 't']

BASE_DIR = os.path.abspath(os.path.dirname(__file__)) # This is SAS_Services directory
DATA_FOLDER = os.path.join(BASE_DIR, 'xml_data') # XML files should be in 'SAS_Services/xml_data/'

# --- API Key for Service-to-Service Authentication (Kept for potential future SAS APIs) ---
# Ensure APP_API_KEY is set in your .env file if you plan to use this.
EXPECTED_API_KEY = os.getenv("APP_API_KEY")

# --- API Key Authentication Decorator ---
def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not EXPECTED_API_KEY:
            app.logger.error("API Key (APP_API_KEY) not configured for the service. API protected routes will fail.")
            # For security, don't reveal that the key is missing to the client.
            return jsonify({"error": "Service access denied or misconfigured"}), 500 # Or 401

        provided_key = request.headers.get('X-API-Key')
        if provided_key and provided_key == EXPECTED_API_KEY:
            return f(*args, **kwargs)
        else:
            app.logger.warning(f"Unauthorized API key attempt. Provided key: '{provided_key}'")
            return jsonify({"error": "Unauthorized - Invalid or missing API Key"}), 401
    return decorated_function

# --- User Context Injection ---
# This makes 'current_user' available in all templates.
@app.context_processor
def inject_user():
    if 'email' in session and session.get('user_type') in ['staff', 'manager', 'admin']:
        # 'email' in session stores the username (e.g., SS11203)
        return {"current_user": SimpleNamespace(username=session['email'], user_type=session.get('user_type'))}
    return {"current_user": SimpleNamespace(username="Guest")} # For unauthenticated users on login page


# --- Helper Functions ---
def get_data_from_xml(filename, list_element_name, item_element_name,
                      value_attribute=None,
                      sub_item_map=None):
    xml_file_path = os.path.join(DATA_FOLDER, filename)
    data = []
    data_dict = {} # Used if sub_item_map is provided for hierarchical data
    app.logger.debug(f"Attempting to parse XML file: {xml_file_path}")

    try:
        if not os.path.exists(xml_file_path):
            app.logger.error(f"XML data file not found at path: {xml_file_path}")
            return data if sub_item_map is None else data_dict

        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        app.logger.debug(f"XML Root element for {filename}: <{root.tag}>")

        # Find the main container for the items
        item_container = root
        if root.tag != list_element_name: # If root is not the list itself
            item_container = root.find(list_element_name)
            if item_container is None: # If list_element_name not found under root
                app.logger.warning(f"List element <{list_element_name}> not found directly under root <{root.tag}> in {filename}. Will search for <{item_element_name}> directly under root.")
                item_container = root # Fallback to searching items directly under root

        if item_container is None: # Should not happen if XML is structured as expected or with fallback
            app.logger.error(f"Could not find item container <{list_element_name}> or suitable root for items in {filename}")
            return data if sub_item_map is None else data_dict

        app.logger.debug(f"Using container <{item_container.tag}> to find <{item_element_name}> items in {filename}")

        if sub_item_map: # Logic for hierarchical XML data
            # ... (Detailed sub_item_map logic as previously provided) ...
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
        else: # Logic for a flat list of items
            item_nodes_found = item_container.findall(item_element_name)
            app.logger.debug(f"Found {len(item_nodes_found)} <{item_element_name}> items in {filename} under <{item_container.tag}>")
            for i, item_node in enumerate(item_nodes_found):
                item_text = None
                if value_attribute: # Get text from an attribute of the item
                    item_text = item_node.get(value_attribute)
                elif item_node.text: # Get text directly from the item's content
                    item_text = item_node.text.strip()

                if item_text:
                    data.append(item_text)
                    app.logger.debug(f"  Item {i+1}: {item_text}")
                else:
                    app.logger.debug(f"  Item {i+1} <{item_element_name}> has no text or attribute '{value_attribute}'.")
            return data
    except ET.ParseError as e: # Specific error for XML parsing issues
        app.logger.error(f"XML ParseError in {xml_file_path}: {e}", exc_info=True)
    except Exception as e: # Catch any other unexpected errors during parsing
        app.logger.error(f"An unexpected error occurred while parsing {xml_file_path}: {e}", exc_info=True)
    # Return empty list/dict if errors occur, to prevent app crash
    return data if sub_item_map is None else data_dict

# --- SAS/Admin Routes ---
@app.route('/')
def index():
    # This route renders login.html.
    # CRITICAL: Ensure login.html uses url_for('sas_login') in its form action.
    # Example in login.html: <form action="{{ url_for('sas_login') }}" method="post">
    return render_template('login.html')

@app.route('/sas-login', methods=['GET', 'POST'])
def sas_login():
    # If user is already logged in and is a valid SAS user, redirect them to their respective home page
    if 'email' in session and session.get('user_type') in ['staff', 'manager', 'admin']:
        user_type = session.get('user_type')
        if user_type == 'staff':
            return redirect(url_for('sas_staff_home'))
        elif user_type == 'manager':
            return redirect(url_for('sas_manager_home'))
        elif user_type == 'admin':
            return redirect(url_for('super_admin_home'))

    if request.method == 'POST':
        # 'username_field' should match the 'name' attribute of the username input in login.html
        username_input = request.form.get('username_field') # Or 'email' if that's the field name in your HTML
        password = request.form.get('password')

        # Updated credentials for SAS Staff, Manager, and Admin
        # CRITICAL SECURITY FLAW: Store hashed passwords in a database for production!
        # This is for demonstration purposes ONLY.
        sas_user_credentials = {
            # Username: (redirect_route_function_name, user_type_for_session, correct_password)
            "SS11203": ("sas_staff_home", "staff", "1234"),
            "SA11103": ("sas_manager_home", "manager", "4321"),
            "SU00001": ("super_admin_home", "admin", "super"), # Example Super Admin
        }

        if username_input in sas_user_credentials:
            redirect_route, user_type, correct_password = sas_user_credentials[username_input]
            if password == correct_password:
                session['email'] = username_input # Store the username (e.g., SS11203) in session
                session['user_type'] = user_type
                flash(f"Successfully logged in as {user_type.title()} ({username_input}).", "success")
                return redirect(url_for(redirect_route))
            else:
                flash("Invalid username or password. Please try again.", "error")
        else:
            flash("Invalid username or password. Please try again.", "error")
        
        # On failed login attempt, re-render the login page with the error message
        return render_template('login.html') 

    # For GET request (or if root '/' renders login.html), just show the login page
    return render_template('login.html')

# --- Logout ---
@app.route("/sas-logout") 
def sas_logout():
    session.pop('email', None)      # Remove username from session
    session.pop('user_type', None)  # Remove user type from session
    # session.clear() # Alternatively, clear the entire session
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("sas_login")) # Redirect to SAS login page


# --- SAS Specific Routes (Authorization enforced within each route) ---
@app.route('/sas-manager/home')
def sas_manager_home():
    if session.get('user_type') != 'manager':
        abort(403) # Forbidden access
    return render_template('SASManager/homeSAS.html')

@app.route('/sas-staff/home')
def sas_staff_home():
    if session.get('user_type') != 'staff':
        abort(403)
    staff_username = session.get('email', "Staff") # 'email' in session stores the username like SS11203

    navigation_links = {
        "navigateToRegister": url_for('sas_staff_register_student'),
        "navigateToEdit": url_for('sas_staff_edit_student'),
        # Add other navigation links for staff as needed
    }
    return render_template(
        'SASStaff/homeStaff.html',
        staff_name=staff_username, 
        navigation_links=navigation_links
    )

@app.route('/sas-staff/register-student')
def sas_staff_register_student():
    if session.get('user_type') != 'staff':
        abort(403)
    # Fetch data from XML files for dropdowns or other form elements
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
    app.logger.debug(f"Programs loaded for registerST.html: {programs_list}")
    app.logger.debug(f"All subprogrammes loaded for registerST.html: {all_subprogrammes_list}")
    app.logger.debug(f"Campuses loaded for registerST.html: {campuses_list}")

    return render_template(
        'SASStaff/registerST.html',
        programs=programs_list,
        subprograms_map={}, # This might need actual data if subprograms depend on selected program
        all_subprogrammes=all_subprogrammes_list,
        campuses=campuses_list
    )

@app.route('/sas-staff/edit-student')
def sas_staff_edit_student():
    if session.get('user_type') != 'staff':
        abort(403)
    # Add logic here to fetch student data if needed for editing
    return render_template('SASStaff/editST.html')

@app.route('/super-admin/home')
def super_admin_home():
    if session.get('user_type') != 'admin':
        abort(403)
    return render_template('SuperAdmin/SAdminHome.html')

@app.route('/super-admin/remove-staff')
def super_admin_remove_staff():
    if session.get('user_type') != 'admin':
        abort(403)
    # Add logic here to list staff for removal, or process removal
    return render_template('SuperAdmin/RemoveStaff.html')


# --- Error Handlers ---
# CRITICAL: Ensure you have templates named 403.html, 404.html, 500.html, 
# and generic_http_error.html in a 'SAS_Services/templates/errors/' subdirectory.

@app.errorhandler(403) # Handles abort(403)
def handle_403(e):
    app.logger.warning(f"Forbidden (403) access attempt to {request.path}. User type: {session.get('user_type')}. Username: {session.get('email')}. Error details: {e}")
    return render_template("errors/403.html", error=e), 403

@app.errorhandler(404) # Handles 404 Not Found errors
def handle_404(e):
    app.logger.warning(f"Resource not found (404) at path: {request.path}. Error details: {e}")
    return render_template("errors/404.html", error=e), 404

@app.errorhandler(500) # Handles direct 500 errors or abort(500)
def handle_500(e):
    app.logger.error(f"Internal Server Error (500) at path: {request.path}. Error details: {e}", exc_info=True) # Log full traceback for 500s
    return render_template("errors/500.html", error=e), 500

@app.errorhandler(HTTPException) # Generic handler for other HTTP exceptions (like abort(400), etc.)
def handle_http_exception(e):
    app.logger.warning(f"HTTP Exception (code {e.code}) at path: {request.path}. Description: {e.description}. Error details: {e}")
    # You can have specific templates for other common HTTP errors if needed
    if e.code == 403: 
        return render_template("errors/403.html", error=e), 403
    if e.code == 404:
        return render_template("errors/404.html", error=e), 404
    if e.code == 500: # Should ideally be caught by the specific @app.errorhandler(500)
        return render_template("errors/500.html", error=e), 500
    return render_template("errors/generic_http_error.html", error=e), e.code

@app.errorhandler(Exception) # Catch-all for any other uncaught Python exceptions (non-HTTP)
def handle_all_other_exceptions(e):
    # This will catch non-HTTPExceptions (like the BuildError if it wasn't caught by Flask's debug page)
    if isinstance(e, HTTPException):
        # If it's already an HTTPException, let its specific handler (or handle_http_exception) deal with it.
        # This ensures that abort(code) calls are handled by their respective error handlers.
        return e 
    
    app.logger.error(f"Unhandled Non-HTTP Exception at path: {request.path}. Error: {e}", exc_info=True) # Log full traceback
    return render_template("errors/500.html", error=e), 500 # Show a generic 500 page


# --- Main Execution Block ---
if __name__ == '__main__':
    # Create data folder if it doesn't exist
    if not os.path.exists(DATA_FOLDER):
        try:
            os.makedirs(DATA_FOLDER, exist_ok=True)
            app.logger.info(f"Created DATA_FOLDER at {DATA_FOLDER}. Place XML files here.")
        except OSError as e:
            app.logger.error(f"Could not create DATA_FOLDER at {DATA_FOLDER}: {e}")


    app.logger.info(f"Flask App '{app.name}' (SAS_Services - Admin/Staff Focused) starting...")
    if EXPECTED_API_KEY:
        app.logger.info(f"Service API Key (APP_API_KEY) loaded: Yes")
    else:
        app.logger.warning("Service API Key (APP_API_KEY) not found in environment. API protected routes will fail if any are used.")
    
    # Check if the default insecure secret key is being used
    default_secret_key = 'sas_services_strong_secret_key_CHANGE_THIS_V2_DEFAULT_INSECURE'
    if app.config['SECRET_KEY'] == default_secret_key:
        app.logger.warning("Flask Secret Key for SAS sessions is using the INSECURE default. Please set FLASK_SECRET_KEY_SAS in your .env file.")
    else:
        app.logger.info("Flask Secret Key for SAS sessions loaded from environment.")

    app.logger.info(f"Debug mode: {app.debug}")
    app.logger.info(f"Template folder: {os.path.join(BASE_DIR, 'templates')}")
    app.logger.info(f"Static folder: {os.path.join(BASE_DIR, 'static')}")
    app.logger.info(f"Data folder (for XMLs): {DATA_FOLDER}")
    
    # Get port from environment variable or use default 5003
    sas_service_port = int(os.getenv("SAS_SERVICE_PORT", 5003))
    app.logger.info(f"Attempting to run on host 0.0.0.0 and port {sas_service_port}")
    
    # app.run() automatically uses app.debug for the debug parameter.
    # Setting host='0.0.0.0' makes the server accessible externally (be careful in untrusted networks).
    app.run(host='0.0.0.0', port=sas_service_port)
