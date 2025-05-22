import os
import xml.etree.ElementTree as ET
from flask import (
    Flask, jsonify, request, send_from_directory, render_template,
    redirect, url_for, flash, abort, session
)
# from werkzeug.utils import secure_filename # Uncomment if you use it
from werkzeug.exceptions import HTTPException
from types import SimpleNamespace
from dotenv import load_dotenv
from functools import wraps
import datetime

# --- Load Environment Variables ---
APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)
DOTENV_PATH = os.path.join(PROJECT_ROOT, '.env')
load_dotenv(DOTENV_PATH)

app = Flask (
    __name__,
    template_folder="templates",
    static_folder="static"
)

# --- Application Configuration ---
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY_SAS', 'sas_default_insecure_secret_key_CHANGE_THIS_V5') # Ensure this is strong and unique
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 't']

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_FOLDER = os.path.join(BASE_DIR, 'xml_data')


# --- User Context Injection ---
@app.context_processor
def inject_user_and_globals():
    user_info = {"current_user": SimpleNamespace(username="Guest", user_type="Guest")}
    if 'email' in session and session.get('user_type') in ['staff', 'manager', 'admin']:
        user_info["current_user"] = SimpleNamespace(username=session['email'], user_type=session.get('user_type'))
    user_info['current_year'] = datetime.datetime.now().year
    return user_info


# --- Helper Functions ---
def get_data_from_xml(filename, list_element_name, item_element_name,
                      value_attribute=None, sub_item_map=None):
    xml_file_path = os.path.join(DATA_FOLDER, filename)
    data_list_for_flat = []
    data_dict_for_hierarchical = {}
    app.logger.debug(f"Attempting to parse XML file: {xml_file_path}")

    try:
        if not os.path.exists(xml_file_path):
            app.logger.error(f"XML data file not found at path: {xml_file_path}")
            return data_list_for_flat if sub_item_map is None else data_dict_for_hierarchical

        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        app.logger.debug(f"XML Root element for {filename}: <{root.tag}>")

        item_container = root
        if root.tag != list_element_name: 
            item_container = root.find(list_element_name)
            if item_container is None: 
                app.logger.warning(f"List element <{list_element_name}> not found directly under root <{root.tag}> in {filename}. Will search for <{item_element_name}> directly under root.")
                item_container = root 

        if item_container is None: 
            app.logger.error(f"Could not find item container <{list_element_name}> or suitable root for items in {filename}")
            return data_list_for_flat if sub_item_map is None else data_dict_for_hierarchical
        
        app.logger.debug(f"Using container <{item_container.tag}> to find <{item_element_name}> items in {filename}")

        if sub_item_map: 
            # Logic for hierarchical XML data (e.g., programs with nested subprograms)
            parent_id_tag_or_attr = sub_item_map['parent_id_tag_or_attr']
            parent_id_is_attribute = sub_item_map.get('parent_id_is_attribute', False)
            sub_item_list_tag = sub_item_map['sub_item_list_tag']
            sub_item_tag = sub_item_map['sub_item_tag']
            sub_item_value_attribute = sub_item_map.get('sub_item_value_attribute') 
            sub_item_text_from_element = sub_item_map.get('sub_item_text_from_element', not sub_item_value_attribute) # Default to text if attribute not specified

            parent_nodes_found = item_container.findall(item_element_name)
            app.logger.debug(f"Found {len(parent_nodes_found)} <{item_element_name}> parent nodes for hierarchical parsing.")

            for i, parent_node in enumerate(parent_nodes_found):
                parent_id_value = None
                if parent_id_is_attribute:
                    parent_id_value = parent_node.get(parent_id_tag_or_attr)
                else: 
                    parent_id_element = parent_node.find(parent_id_tag_or_attr)
                    if parent_id_element is not None and parent_id_element.text:
                        parent_id_value = parent_id_element.text.strip()
                
                # Fallback: if value_attribute is specified for the parent item_element_name itself
                # and parent_id_tag_or_attr didn't yield a value (e.g. key is an attribute of the parent item)
                if value_attribute and parent_id_value is None: 
                    parent_id_value = parent_node.get(value_attribute)

                if parent_id_value:
                    # app.logger.debug(f"  Parent item {i+1} Key: '{parent_id_value}'") # Can be noisy
                    current_sub_items_list = []
                    sub_items_container_node = parent_node.find(sub_item_list_tag)

                    if sub_items_container_node is not None:
                        sub_item_nodes_found = sub_items_container_node.findall(sub_item_tag)
                        for j, sub_item_node in enumerate(sub_item_nodes_found):
                            sub_text = None
                            if sub_item_value_attribute:
                                sub_text = sub_item_node.get(sub_item_value_attribute)
                            elif sub_item_text_from_element and sub_item_node.text:
                                sub_text = sub_item_node.text.strip()
                            # Fallback if neither specific attribute nor text_from_element is true, but node has text
                            elif sub_item_node.text and not sub_item_value_attribute and not sub_item_text_from_element:
                                sub_text = sub_item_node.text.strip()
                                
                            if sub_text:
                                current_sub_items_list.append(sub_text)
                    data_dict_for_hierarchical[parent_id_value] = current_sub_items_list
            return data_dict_for_hierarchical
        else: 
            # Logic for a flat list of items
            item_nodes_found = item_container.findall(item_element_name)
            app.logger.debug(f"Found {len(item_nodes_found)} <{item_element_name}> items for flat list under <{item_container.tag}>.")
            for i, item_node in enumerate(item_nodes_found):
                item_text = None
                if value_attribute: 
                    item_text = item_node.get(value_attribute)
                elif item_node.text: 
                    item_text = item_node.text.strip()

                if item_text:
                    data_list_for_flat.append(item_text)
                else:
                    app.logger.debug(f"  Item {i+1} <{item_element_name}> in {filename} has no text or attribute '{value_attribute}'.")
            return data_list_for_flat
    except ET.ParseError as e: 
        app.logger.error(f"XML ParseError in {xml_file_path}: {e}", exc_info=True)
    except Exception as e: 
        app.logger.error(f"An unexpected error occurred while parsing {xml_file_path}: {e}", exc_info=True)
    # Fallback return in case of any error during parsing
    return data_list_for_flat if sub_item_map is None else data_dict_for_hierarchical


# --- SAS/Admin Routes ---
@app.route('/', methods=['GET', 'POST'])
@app.route('/sas-login', methods=['GET', 'POST'])
def sas_login():
    if request.method == 'GET' and 'email' in session and session.get('user_type') in ['staff', 'manager', 'admin']:
        user_type = session.get('user_type')
        if user_type == 'staff': return redirect(url_for('sas_staff_home'))
        if user_type == 'manager': return redirect(url_for('sas_manager_home'))
        if user_type == 'admin': return redirect(url_for('super_admin_home'))

    if request.method == 'POST':
        username_input = request.form.get('username_field')
        password = request.form.get('password')
        sas_user_credentials = {
            "SS11203": ("sas_staff_home", "staff", "1234"),
            "SA11103": ("sas_manager_home", "manager", "4321"),
            "SU00001": ("super_admin_home", "admin", "super"),
        }
        if username_input in sas_user_credentials:
            redirect_route, user_type, correct_password = sas_user_credentials[username_input]
            if password == correct_password:
                session['email'] = username_input
                session['user_type'] = user_type
                flash(f"Login successful as {user_type.title()}.", "success")
                return redirect(url_for(redirect_route))
            else:
                flash("Invalid username or password.", "error")
        else:
            flash("Invalid username or password.", "error")
        return render_template('login.html') 
    return render_template('login.html')

@app.route("/sas-logout") 
def sas_logout():
    session.pop('email', None)
    session.pop('user_type', None)
    flash("You have been logged out.", "info")
    return redirect(url_for("sas_login"))

@app.route('/super-admin/home')
def super_admin_home():
    if session.get('user_type') != 'admin': abort(403)
    return render_template('SuperAdmin/SAdminHome.html')

@app.route('/super-admin/remove-staff')
def super_admin_remove_staff():
    if session.get('user_type') != 'admin': abort(403)
    return render_template('SuperAdmin/RemoveStaff.html')

@app.route('/sas-manager/home')
def sas_manager_home():
    if session.get('user_type') != 'manager': abort(403)
    return render_template('SASManager/homeSAS.html')

@app.route('/sas-staff/home')
def sas_staff_home():
    if session.get('user_type') != 'staff': abort(403)
    staff_username = session.get('email', "Staff User")
    navigation_links = {
        "navigateToRegister": url_for('sas_staff_register_student'),
        "navigateToEdit": url_for('sas_staff_edit_student'),
        "navigateToAllSTGrades": url_for('sas_staff_all_student_enrollments'), # Ensure this endpoint exists
        "navigateToGradeRecheck": url_for('sas_staff_grade_rechecks'),     # Ensure this endpoint exists
    }
    return render_template(
        'SASStaff/homeStaff.html',
        staff_name=staff_username, 
        navigation_links=navigation_links,
        show_nav_drawer_button=True 
    )

@app.route('/sas-staff/register-student')
def sas_staff_register_student():
    if session.get('user_type') != 'staff': abort(403)
    
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
        all_subprogrammes=all_subprogrammes_list,
        campuses=campuses_list
        # If you need a subprograms_map (e.g., program -> list of its subprograms), 
        # you would call get_data_from_xml with a properly configured sub_item_map argument
        # and pass that map to the template.
    )

@app.route('/sas-staff/edit-student')
def sas_staff_edit_student():
    if session.get('user_type') != 'staff':
        abort(403)

    # TODO: Fetch actual student data from your XML or database
    # This data should be a list of dictionaries/objects
    # Each item needs: id, first_name, last_name, (middle_name optional), campus
    students_overview_data = [
        { 'id': 'S12345678', 'first_name': 'John', 'middle_name': 'Michael', 'last_name': 'Doe', 'campus': 'Laucala' },
        { 'id': 'S87654321', 'first_name': 'Jane', 'middle_name': 'Elizabeth', 'last_name': 'Smith', 'campus': 'Laucala' },
        { 'id': 'S11223344', 'first_name': 'Peter', 'middle_name': 'James', 'last_name': 'Jones', 'campus': 'Solomon Islands' }
    ]
    # In a real app, you would also handle loading state or if students_overview_data is empty
    return render_template('SASStaff/editST.html', students=students_overview_data)

@app.route('/sas-staff/display-student/<student_id>')
def sas_staff_display_student(student_id):
    if session.get('user_type') != 'staff':
        abort(403)

    # TODO: Fetch all details for the specific student_id from your XML or database
    # This should return a single dictionary/object with all fields for that student
    # For example:
    student_details = None # Initialize
    all_students_raw_data = [ # This is just for example, you'd have a proper fetch function
         {'id': 'S12345678', 'first_name': 'John', 'middle_name': 'Michael', 'last_name': 'Doe', 'address': '123 Suva Point Rd, Suva', 'contact': '679-1234567', 'date_of_birth': '1999-08-21', 'gender': 'Male', 'citizenship': 'Fijian', 'subprogram': 'Software Engineering', 'program': 'Bachelor of Science', 'student_level': 'Undergraduate', 'campus': 'Laucala'},
         {'id': 'S87654321', 'first_name': 'Jane', 'middle_name': 'Elizabeth', 'last_name': 'Smith', 'address': '456 Marine Drive, Nasese', 'contact': '679-7654321', 'date_of_birth': '2000-03-10', 'gender': 'Female', 'citizenship': 'Regional', 'subprogram': 'Data Analytics', 'program': 'Bachelor of Commerce', 'student_level': 'Undergraduate', 'campus': 'Laucala'},
         {'id': 'S11223344', 'first_name': 'Peter', 'middle_name': 'James', 'last_name': 'Jones', 'address': '789 Laucala Bay Rd, Suva', 'contact': '679-1112222', 'date_of_birth': '1998-12-01', 'gender': 'Male', 'citizenship': 'Solomon Islander', 'subprogram': 'Information Systems', 'program': 'Bachelor of Science', 'student_level': 'Undergraduate', 'campus': 'Solomon Islands'}
    ]
    for s_data in all_students_raw_data:
        if s_data['id'] == student_id:
            student_details = s_data
            break

    if not student_details:
        # Optional: flash a message or handle more gracefully
        app.logger.warning(f"Student with ID {student_id} not found.")
        # You could redirect back to the list with an error or render displayST.html with a "not found" message
        # return redirect(url_for('sas_staff_edit_student')) # Example redirect

    # The student_details object will be passed to displayST.html
    return render_template('SASStaff/displayST.html', student=student_details)

@app.route('/sas-staff/grade-rechecks')
def sas_staff_grade_rechecks():
    if session.get('user_type') != 'staff': abort(403)
    recheck_applications = [ # Mock data
        {"student_id": "S11223344", "first_name": "Alice", "last_name": "Wonderland", "campus": "Laucala", "course_code": "CS111", "coordinator_name": "Dr. Elara Vance", "receipt_image_url": url_for('static', filename='images/mock_receipt1.png')},
        {"student_id": "S11000077", "first_name": "Bob", "last_name": "The Builder", "campus": "Lautoka", "course_code": "MA111", "coordinator_name": "Prof. Ian Field", "receipt_image_url": url_for('static', filename='images/mock_receipt2.png')}
    ]
    return render_template('SASStaff/gradeRE.html', applications=recheck_applications)

@app.route('/sas-staff/all-students-grades')
def sas_staff_all_student_enrollments():
    if session.get('user_type') != 'staff': abort(403)
    student_enrollments_data = [ # Mock data
        {"student_id": "S11223344", "full_name": "Alice Wonderland", "course_enrolled_in": "CS111 - Introduction to Computing", "campus": "Laucala" },
        {"student_id": "S11000077", "full_name": "Bob The Builder", "course_enrolled_in": "MA111 - Calculus I", "campus": "Lautoka"}
    ]
    for enrollment in student_enrollments_data:
        course_parts = enrollment["course_enrolled_in"].split(" - ")
        course_code = course_parts[0] if len(course_parts) > 0 else "UNKNOWN"
        enrollment["change_grade_action"] = f"change_grade('{enrollment['student_id']}', '{course_code}')"
    return render_template('SASStaff/allST.html', enrollments=student_enrollments_data)


# --- Error Handlers ---
def render_error_page(error, status_code):
    error_template = f"errors/{status_code}.html"
    specific_template_path = os.path.join(app.template_folder, error_template)
    generic_template_path = os.path.join(app.template_folder, "errors/generic_http_error.html")

    final_template_to_render = error_template
    if not os.path.exists(specific_template_path):
        if os.path.exists(generic_template_path):
            final_template_to_render = "errors/generic_http_error.html"
        else:
            app.logger.critical(f"CRITICAL: Fallback error template 'errors/generic_http_error.html' AND specific '{error_template}' not found for status {status_code}. Original error: {error}", exc_info=True)
            return f"Internal Server Error ({status_code}). Critical error: Error page template missing.", status_code
    try:
        return render_template(final_template_to_render, error=error), status_code
    except Exception as e_render:
        app.logger.critical(f"CRITICAL: Error rendering error page '{final_template_to_render}' for status {status_code}. Original error: {error}. Render error: {e_render}", exc_info=True)
        # Avoid rendering another template here to prevent loops if base.html has issues
        return f"Internal Server Error ({status_code}). An additional error occurred while trying to display the error page. Please check server logs.", status_code

@app.errorhandler(403)
def handle_403(e):
    app.logger.warning(f"Forbidden (403) access attempt to {request.path}. User: {session.get('email')}, Type: {session.get('user_type')}. Error: {e}")
    return render_error_page(e, 403)

@app.errorhandler(404)
def handle_404(e): 
    app.logger.warning(f"Not Found (404) at path: {request.path}. Error: {e}")
    return render_error_page(e, 404)

@app.errorhandler(500)
def handle_500(e):
    app.logger.error(f"Internal Server Error (500) at path: {request.path}. Error: {e}", exc_info=True)
    return render_error_page(e, 500)

@app.errorhandler(HTTPException) # Catches other HTTP errors
def handle_http_exception(e):
    status_code = e.code if hasattr(e, 'code') and e.code is not None else 500
    # Avoid re-triggering specific handlers if they are already defined for this code
    if status_code in [403, 404, 500] and app.error_handler_spec[None].get(status_code):
         # If a specific handler (like @app.errorhandler(404)) exists, let it handle it.
         # This check might need refinement based on Flask version or if using blueprints.
         # For simplicity, we can let render_error_page handle the fallback.
         pass # Or just call render_error_page directly
    app.logger.warning(f"HTTP Exception (code {status_code}) at path: {request.path}. Description: {e.description}. Error: {e}")
    return render_error_page(e, status_code)

@app.errorhandler(Exception) # Catch-all for non-HTTP exceptions
def handle_all_other_exceptions(e):
    if isinstance(e, HTTPException): # Should have been caught by HTTPException or specific code handlers
        return e # Let Werkzeug/Flask handle it further if it's already an HTTPException
    app.logger.error(f"Unhandled Non-HTTP Exception at path: {request.path}. Error: {e}", exc_info=True)
    return render_error_page(e, 500)


# --- Main Execution Block ---
if __name__ == '__main__':
    if not os.path.exists(DATA_FOLDER):
        try:
            os.makedirs(DATA_FOLDER, exist_ok=True)
            app.logger.info(f"Created DATA_FOLDER at {DATA_FOLDER}")
        except OSError as e:
            app.logger.error(f"Could not create DATA_FOLDER: {e}")

    app.logger.info(f"Flask App '{app.name}' (SAS_Services) starting...")
    if app.config['SECRET_KEY'] == 'sas_default_insecure_secret_key_CHANGE_THIS_V5':
        app.logger.warning("SECURITY WARNING: Flask SECRET_KEY is using the INSECURE default value.")
    app.logger.info(f"Debug mode: {app.debug}")
    app.logger.info(f"Template folder: {os.path.join(BASE_DIR, app.template_folder)}")
    app.logger.info(f"Static folder: {os.path.join(BASE_DIR, app.static_folder)}")
    app.logger.info(f"Data folder (for XMLs): {DATA_FOLDER}")
    
    sas_service_port = int(os.getenv("SAS_SERVICE_PORT", 5003))
    app.logger.info(f"Attempting to run on host 0.0.0.0 and port {sas_service_port}")
    app.run(host='0.0.0.0', port=sas_service_port)