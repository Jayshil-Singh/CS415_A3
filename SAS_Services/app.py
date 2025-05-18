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
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY_SAS', 'sas_default_insecure_secret_key_CHANGE_THIS_V5')
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 't']

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_FOLDER = os.path.join(BASE_DIR, 'xml_data')
# app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'profile_pictures_storage')
# app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}


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
            parent_id_tag_or_attr = sub_item_map['parent_id_tag_or_attr']
            parent_id_is_attribute = sub_item_map.get('parent_id_is_attribute', False)
            sub_item_list_tag = sub_item_map['sub_item_list_tag']
            sub_item_tag = sub_item_map['sub_item_tag']
            # How to get the text/value for the sub-item
            sub_item_value_attribute = sub_item_map.get('sub_item_value_attribute') 
            sub_item_text_from_element = sub_item_map.get('sub_item_text_from_element', not sub_item_value_attribute)


            parent_nodes_found = item_container.findall(item_element_name)
            app.logger.debug(f"Found {len(parent_nodes_found)} <{item_element_name}> parent nodes for hierarchical parsing.")

            for i, parent_node in enumerate(parent_nodes_found):
                parent_id_value = None
                if parent_id_is_attribute:
                    parent_id_value = parent_node.get(parent_id_tag_or_attr)
                else: # Get from child element text
                    parent_id_element = parent_node.find(parent_id_tag_or_attr)
                    if parent_id_element is not None and parent_id_element.text:
                        parent_id_value = parent_id_element.text.strip()
                
                # Fallback or primary: if value_attribute is specified for the parent item_element_name itself
                # This is useful if the key for the dictionary is an attribute of the item_element_name tag
                if value_attribute and parent_id_value is None: # Use if parent_id_tag_or_attr didn't yield a value
                    parent_id_value = parent_node.get(value_attribute)


                if parent_id_value:
                    app.logger.debug(f"  Parent item {i+1} Key: '{parent_id_value}'")
                    current_sub_items_list = []
                    sub_items_container_node = parent_node.find(sub_item_list_tag)

                    if sub_items_container_node is not None:
                        sub_item_nodes_found = sub_items_container_node.findall(sub_item_tag)
                        app.logger.debug(f"    Found {len(sub_item_nodes_found)} <{sub_item_tag}> sub-items in <{sub_items_container_node.tag}>")
                        for j, sub_item_node in enumerate(sub_item_nodes_found):
                            sub_text = None
                            if sub_item_value_attribute: # Prioritize attribute if specified
                                sub_text = sub_item_node.get(sub_item_value_attribute)
                            elif sub_item_text_from_element and sub_item_node.text: # Then check element text if flag is true
                                sub_text = sub_item_node.text.strip()
                            
                            if sub_text:
                                current_sub_items_list.append(sub_text)
                            # else:
                                # app.logger.debug(f"      Sub-item {j+1} <{sub_item_tag}> has no suitable text/attribute.")
                    # else:
                        # app.logger.debug(f"    No <{sub_item_list_tag}> container found for parent '{parent_id_value}'")
                    data_dict_for_hierarchical[parent_id_value] = current_sub_items_list
                # else:
                    # app.logger.debug(f"  Parent item {i+1} <{item_element_name}> missing key value via '{parent_id_tag_or_attr}' or '{value_attribute}'.")
            return data_dict_for_hierarchical
        else: 
            item_nodes_found = item_container.findall(item_element_name)
            app.logger.debug(f"Found {len(item_nodes_found)} <{item_element_name}> items for flat list under <{item_container.tag}>") # Corrected syntax
            for i, item_node in enumerate(item_nodes_found):
                item_text = None
                if value_attribute: 
                    item_text = item_node.get(value_attribute)
                elif item_node.text: 
                    item_text = item_node.text.strip()

                if item_text:
                    data_list_for_flat.append(item_text)
                # else:
                    # app.logger.debug(f"  Item {i+1} <{item_element_name}> has no text or attribute '{value_attribute}'.")
            return data_list_for_flat
    except ET.ParseError as e: 
        app.logger.error(f"XML ParseError in {xml_file_path}: {e}", exc_info=True)
    except Exception as e: 
        app.logger.error(f"An unexpected error occurred while parsing {xml_file_path}: {e}", exc_info=True)
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
    )

@app.route('/sas-staff/edit-student')
def sas_staff_edit_student():
    if session.get('user_type') != 'staff': abort(403)
    return render_template('SASStaff/editST.html')

# --- Error Handlers ---
def render_error_page(error, status_code):
    error_template = f"errors/{status_code}.html"
    # Fallback to generic error page if specific one doesn't exist OR if the specific one IS generic_http_error.html
    # This prevents a loop if generic_http_error.html itself is missing.
    specific_template_path = os.path.join(app.template_folder, error_template)
    generic_template_path = os.path.join(app.template_folder, "errors/generic_http_error.html")

    if not os.path.exists(specific_template_path) or error_template == "errors/generic_http_error.html":
        if os.path.exists(generic_template_path):
            error_template = "errors/generic_http_error.html"
        else: # Absolute fallback if generic_http_error.html is also missing
            app.logger.critical(f"CRITICAL: Fallback error template 'errors/generic_http_error.html' not found for status {status_code}. Original error: {error}", exc_info=True)
            return f"Internal Server Error ({status_code}). Critical error: Error page template missing.", status_code

    try:
        return render_template(error_template, error=error), status_code
    except Exception as e_render:
        app.logger.critical(f"CRITICAL: Error rendering error page '{error_template}' for status {status_code}. Original error: {error}. Render error: {e_render}", exc_info=True)
        return f"Internal Server Error ({status_code}). An additional error occurred while trying to display the error page.", status_code


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

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    status_code = e.code if hasattr(e, 'code') and e.code is not None else 500
    app.logger.warning(f"HTTP Exception (code {status_code}) at path: {request.path}. Description: {e.description}. Error: {e}")
    return render_error_page(e, status_code)

@app.errorhandler(Exception)
def handle_all_other_exceptions(e):
    if isinstance(e, HTTPException):
        # This ensures that abort(code) calls are handled by their respective error handlers (HTTPException or specific codes)
        # and then by render_error_page.
        # If an error occurs *within* an error handler that tries to render a template,
        # render_error_page's try-except will catch it.
        return e 
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
    if app.config['SECRET_KEY'] == 'sas_default_insecure_secret_key_CHANGE_THIS_V4': # Match updated default
        app.logger.warning("SECURITY WARNING: Flask SECRET_KEY is using the INSECURE default value.")
    app.logger.info(f"Debug mode: {app.debug}")
    app.logger.info(f"Template folder: {os.path.join(BASE_DIR, app.template_folder)}")
    app.logger.info(f"Static folder: {os.path.join(BASE_DIR, app.static_folder)}")
    app.logger.info(f"Data folder (for XMLs): {DATA_FOLDER}")
    
    sas_service_port = int(os.getenv("SAS_SERVICE_PORT", 5003))
    app.logger.info(f"Attempting to run on host 0.0.0.0 and port {sas_service_port}")
    app.run(host='0.0.0.0', port=sas_service_port)