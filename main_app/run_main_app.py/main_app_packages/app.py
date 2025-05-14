# File: C:\Users\yashp\Documents\CS415\CS415_A3\main_app\run_main_app.py\main_app_packages\app.py
import os
import xml.etree.ElementTree as ET
from flask import Flask, jsonify, request, send_from_directory, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key_v6_change_this_now')
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 't']

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER_PATH = os.path.join(BASE_DIR, 'profile_pictures_storage')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER_PATH
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

DATA_FOLDER = os.path.join(BASE_DIR, 'xml_data')

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

        # Determine the actual container for items if list_element_name is not the root
        item_container = root
        if root.tag != list_element_name:
            item_container = root.find(list_element_name)
            if item_container is None:
                app.logger.warning(f"List element <{list_element_name}> not found directly under root <{root.tag}> in {filename}. Will search for <{item_element_name}> under root.")
                item_container = root # Fallback to searching item_element_name directly under root

        if item_container is None: # Should not happen if fallback to root works, but good check
            app.logger.error(f"Could not find item container <{list_element_name}> or root for items in {filename}")
            return data if sub_item_map is None else data_dict

        app.logger.debug(f"Using container <{item_container.tag}> to find <{item_element_name}> items in {filename}")
        
        if sub_item_map: 
            # Logic for hierarchical data (e.g., a future structured subprogrammes.xml)
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
            # Logic for flat list data
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
try:
    from profile_service.run_profile_service import student_profiles
except ImportError:
    app.logger.warning("Could not import 'student_profiles' from profile_service. Using dummy data.")
    student_profiles = {'s12345': {'firstName': 'Test', 'lastName': 'User', 'profile_pic_url': None}}

# --- Routes ---
# (Login, Profile API, SASManager, other SASStaff, SuperAdmin routes remain the same)
@app.route('/')
def index(): return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email == "staff@example.com" and password == "password": return redirect(url_for('sas_staff_home')) 
        elif email == "manager@example.com" and password == "password": return redirect(url_for('sas_manager_home'))
        elif email == "admin@example.com" and password == "password": return redirect(url_for('super_admin_home'))
        else:
            flash("Invalid email or password. Please try again.", "error")
            return render_template('login.html', error="Invalid email or password")
    return render_template('login.html')

@app.route('/profile/<student_id>', methods=['GET'])
def get_profile(student_id):
    profile = student_profiles.get(student_id)
    if not profile: return jsonify({"error": "Student profile not found"}), 404
    return jsonify(profile)

@app.route('/profile/<student_id>/picture', methods=['POST'])
def upload_profile_picture(student_id):
    if student_id not in student_profiles: return jsonify({"error": "Student profile not found"}), 404
    if 'photo' not in request.files: return jsonify({"error": "No photo file part"}), 400
    file = request.files['photo']
    if file.filename == '': return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"{student_id}.{ext}")
        if not app.config['UPLOAD_FOLDER']:
            app.logger.error("UPLOAD_FOLDER not configured.")
            return jsonify({"error": "File upload path not configured"}), 500
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(filepath)
            profile_pic_url = url_for('get_profile_pic', filename=filename, _external=True)
            student_profiles[student_id]['profile_pic_url'] = profile_pic_url
            return jsonify({"message": "Profile picture updated successfully", "profile_pic_url": profile_pic_url}), 200
        except Exception as e:
            app.logger.error(f"Error saving file {filename}: {e}")
            return jsonify({"error": "Could not save file"}), 500
    return jsonify({"error": "File type not allowed"}), 400

@app.route('/profile_pics/<filename>')
def get_profile_pic(filename):
    if not app.config['UPLOAD_FOLDER']:
        app.logger.error("UPLOAD_FOLDER not configured.")
        return jsonify({"error": "File upload path not configured"}), 404
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/sas-manager/home')
def sas_manager_home(): return render_template('SASManager/homeSAS.html')
@app.route('/sas-staff/home')
def sas_staff_home(): return render_template('SASStaff/homeStaff.html')
@app.route('/sas-staff/edit-student')
def sas_staff_edit_student(): return render_template('SASStaff/editST.html')

@app.route('/sas-staff/register-student')
def sas_staff_register_student():
    programs_list = get_data_from_xml(
        filename='programs.xml', 
        list_element_name='programs',
        item_element_name='program',
        value_attribute='programName'
    )
    
    # Correctly parse the flat list of subprogrammes from subprogrammes.xml
    all_subprogrammes_list = get_data_from_xml(
        filename='subprogrammes.xml',
        list_element_name='subprograms',    # The root tag <subprograms>
        item_element_name='subprogram',   # Each <subprogram ... /> tag
        value_attribute='subprogramName'  # Get value from the 'subprogramName' attribute
    )
    
    campuses_list = get_data_from_xml(
        filename='campuses.xml', 
        list_element_name='campuses', 
        item_element_name='campus',
        value_attribute='campusName' # Assuming 'campusName', adjust if different
    )
    
    app.logger.debug(f"Final Programs loaded for template: {programs_list}")
    # For now, subprograms_map will be empty as the XML is flat.
    # The JavaScript will need to be adapted, or the XML structure for subprogrammes changed.
    app.logger.debug(f"Flat list of all subprogrammes loaded: {all_subprogrammes_list}")
    app.logger.debug(f"Final Campuses loaded for template: {campuses_list}")

    return render_template(
        'SASStaff/registerST.html', 
        programs=programs_list, 
        # Pass the flat list for now; JS needs to handle this or XML needs to change for dependent dropdown
        subprograms_map={}, # Or pass all_subprogrammes_list and adapt JS
        all_subprogrammes=all_subprogrammes_list, # New variable for the flat list
        campuses=campuses_list
    )

@app.route('/super-admin/home')
def super_admin_home(): return render_template('SuperAdmin/SAdminHome.html')
@app.route('/super-admin/remove-staff')
def super_admin_remove_staff(): return render_template('SuperAdmin/RemoveStaff.html')

# --- Main Execution Block ---
if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        app.logger.info(f"Created UPLOAD_FOLDER at {app.config['UPLOAD_FOLDER']}")
    if not os.path.exists(DATA_FOLDER): 
        os.makedirs(DATA_FOLDER, exist_ok=True)
        app.logger.info(f"Created DATA_FOLDER at {DATA_FOLDER}. Place XML files here.")
    app.logger.info(f"Data folder (for XMLs) is {DATA_FOLDER}")    
    app.run(host='0.0.0.0', port=5000)
