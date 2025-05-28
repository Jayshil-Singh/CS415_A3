from http.client import HTTPException
import os
import xml.etree.ElementTree as ET
from flask import (
    Flask, jsonify, request, send_from_directory, render_template,
    redirect, url_for, flash, abort, session
)
from werkzeug.security import generate_password_hash, check_password_hash # For passwords
from werkzeug.exceptions import HTTPException
from types import SimpleNamespace
from dotenv import load_dotenv
from functools import wraps
import datetime
import random
import string
import sqlite3

# Import 'db' instance AND model classes from models.py
from models import (
    db, Student, Program, Student_Program, Student_Level, Campus, ProgramType,
    SubProgram, # Make sure SubProgram is imported
    GenderEnum, StudentLevelEnum, student_subprogram_association # Import association table if needed directly
)

# --- Load Environment Variables ---
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(APP_DIR, '.env')):
    DOTENV_PATH = os.path.join(APP_DIR, '.env')
else:
    PROJECT_ROOT = os.path.dirname(APP_DIR) # Assumes .env is one level up if not in APP_DIR
    DOTENV_PATH = os.path.join(PROJECT_ROOT, '.env')

if os.path.exists(DOTENV_PATH):
    load_dotenv(DOTENV_PATH)
else:
    # Fallback if .env is truly not found, to prevent error on load_dotenv
    print(f"Warning: .env file not found at expected locations: {DOTENV_PATH} or {os.path.join(APP_DIR, '.env')}")


# Create Flask App
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
    instance_relative_config=True
)

# --- Application Configuration ---
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY_SAS', 'a_very_secure_default_key_!@#$_for_dev_only')
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 't']
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL_SAS', f"sqlite:///{os.path.join(app.instance_path, 'enrollment.db')}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the imported 'db' object (from models.py) with the app
db.init_app(app)

# --- BASE_DIR and DATA_FOLDER ---
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


def get_next_student_id():
    last_student = Student.query.order_by(Student.StudentID.desc()).first()
    if last_student and last_student.StudentID.startswith('S') and last_student.StudentID[1:].isdigit():
        last_num = int(last_student.StudentID[1:])
        next_num = last_num + 1
        return f"S{next_num:08d}"
    return "S00000000"

def generate_random_password(length_min=7, length_max=9):
    length = random.randint(length_min, length_max)
    characters = string.ascii_letters + string.digits + string.punctuation
    while True: # Ensure password meets complexity
        password = ''.join(random.choice(characters) for i in range(length))
        if (any(c.islower() for c in password) and
            any(c.isupper() for c in password) and
            any(c.isdigit() for c in password) and
            any(c in string.punctuation for c in password)):
            return password # Return only after complexity is met

def register_student_in_service_db(student_data):
    """Helper function to register student in StudentService database"""
    target_db = os.path.join('StudentService', 'instance', 'studentservice.db')
    connection = None
    try:
        connection = sqlite3.connect(target_db)
        cursor = connection.cursor()
        
        # Insert into Student table
        cursor.execute("""
            INSERT INTO Student (
                StudentID, FirstName, MiddleName, LastName,
                Contact, Email, DateOfBirth, Gender,
                Citizenship, Address, PasswordHash, CampusID
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student_data['StudentID'],
            student_data['FirstName'],
            student_data['MiddleName'],
            student_data['LastName'],
            student_data['Contact'],
            student_data['Email'],
            student_data['DateOfBirth'],
            student_data['Gender'].value,
            student_data['Citizenship'],
            student_data['Address'],
            student_data['PasswordHash'],
            student_data['CampusID']
        ))
        
        connection.commit()
        return True
    except Exception as e:
        if connection:
            connection.rollback()
        app.logger.error(f"Error registering student in StudentService DB: {e}", exc_info=True)
        raise
    finally:
        if connection:
            connection.close()

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
            if password == correct_password: # In real app, use check_password_hash
                session['email'] = username_input
                session['user_type'] = user_type
                flash(f"Login successful as {user_type.title()}.", "success")
                return redirect(url_for(redirect_route))
            else:
                flash("Invalid username or password.", "error")
        else:
            flash("Invalid username or password.", "error")
        return render_template('login.html', form_data=request.form) # Pass form_data back
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
        "navigateToAllSTGrades": url_for('sas_staff_all_student_enrollments'),
        "navigateToGradeRecheck": url_for('sas_staff_grade_rechecks'),
    }
    return render_template(
        'SASStaff/homeStaff.html',
        staff_name=staff_username,
        navigation_links=navigation_links,
        show_nav_drawer_button=True
    )


@app.route('/sas-staff/register-student', methods=['GET', 'POST'])
def sas_staff_register_student():
    if session.get('user_type') != 'staff': abort(403)

    programs_for_dropdown_xml = get_data_from_xml(filename='programs.xml', list_element_name='programs', item_element_name='program', value_attribute='programName')
    all_subprogrammes_list_xml = get_data_from_xml(filename='subprogrammes.xml', list_element_name='subprograms', item_element_name='subprogram', value_attribute='subprogramName')
    campuses_from_xml = get_data_from_xml(filename='campuses.xml', list_element_name='campuses', item_element_name='campus', value_attribute='campusName')
    program_type_names = [pt.ProgramTypeName for pt in ProgramType.query.all()]

    if request.method == 'POST':
        try:
            # --- Form Data Retrieval ---
            first_name = request.form.get('firstName')
            middle_name = request.form.get('middleName') or None
            last_name = request.form.get('lastName')
            contact = request.form.get('contact')
            dob_str = request.form.get('dateOfBirth')
            gender_str = request.form.get('gender')
            citizenship = request.form.get('citizenship')
            address = request.form.get('address')
            selected_program_name = request.form.get('program')
            student_level_str = request.form.get('studentLevel')
            selected_campus_name = request.form.get('campus')
            selected_program_type_name = request.form.get('programType')
            subprogram1_name = request.form.get('subprogram1')
            subprogram2_name = request.form.get('subprogram2')

            date_of_birth = datetime.datetime.strptime(dob_str, '%Y-%m-%d').date()
            gender = GenderEnum(gender_str)
            student_level_enum_val = StudentLevelEnum(student_level_str)
            
            student_id = get_next_student_id()
            raw_password = generate_random_password()
            password_hash_val = generate_password_hash(raw_password)
            email = f"s{student_id[1:]}@student.usp.ac.fj"

            program_obj = Program.query.filter(db.func.lower(Program.ProgramName) == db.func.lower(selected_program_name)).first()
            if not program_obj: raise ValueError(f"Program '{selected_program_name}' not found.")
            
            campus_obj = Campus.query.filter_by(CampusName=selected_campus_name).first()
            if not campus_obj: raise ValueError(f"Campus '{selected_campus_name}' not found.")

            program_type_obj = ProgramType.query.filter_by(ProgramTypeName=selected_program_type_name).first()
            if not program_type_obj: raise ValueError(f"Program Type '{selected_program_type_name}' not found.")

            # Create Student object for both databases
            student_data = {
                'StudentID': student_id,
                'FirstName': first_name,
                'MiddleName': middle_name,
                'LastName': last_name,
                'Contact': contact,
                'Email': email,
                'DateOfBirth': date_of_birth,
                'Gender': gender,
                'Citizenship': citizenship,
                'Address': address,
                'PasswordHash': password_hash_val,
                'CampusID': campus_obj.CampusID
            }

            # Create Student in main database
            new_student = Student(**student_data)
            db.session.add(new_student)

            # Create Student_Program link
            new_student_program = Student_Program(
                StudentID=student_id,
                ProgramID=program_obj.ProgramID,
                ProgramTypeID=program_type_obj.ProgramTypeID
            )
            db.session.add(new_student_program)

            # Create Student_Level link
            new_student_level = Student_Level(StudentID=student_id, StudentLevel=student_level_enum_val)
            db.session.add(new_student_level)

            # Handle Subprogram Enrollment
            if student_level_enum_val == StudentLevelEnum.BACHELOR:
                selected_subprograms_for_student = []
                if selected_program_type_name == "Single Major" and subprogram1_name:
                    sp1 = SubProgram.query.filter_by(SubProgramName=subprogram1_name).first()
                    if sp1: selected_subprograms_for_student.append(sp1)
                elif selected_program_type_name == "Double Major":
                    if subprogram1_name:
                        sp1 = SubProgram.query.filter_by(SubProgramName=subprogram1_name).first()
                        if sp1: selected_subprograms_for_student.append(sp1)
                    if subprogram2_name:
                        sp2 = SubProgram.query.filter_by(SubProgramName=subprogram2_name).first()
                        if sp2 and (not sp1 or sp1.SubProgramID != sp2.SubProgramID):
                            selected_subprograms_for_student.append(sp2)
                
                for sub_prog_obj in selected_subprograms_for_student:
                    new_student.enrolled_subprograms.append(sub_prog_obj)

            # Register in StudentService database
            register_student_in_service_db(student_data)
            
            # Commit changes to main database
            db.session.commit()
            
            app.logger.info(f"Registered student {student_id} in both databases")
            session['new_student_credentials'] = {'student_id': student_id, 'email': email, 'password': raw_password}
            return redirect(url_for('sas_staff_register_student'))

        except ValueError as ve:
            db.session.rollback()
            flash(f"Invalid data: {str(ve)}", "error")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Registration error: {e}", exc_info=True)
            flash("An unexpected error occurred during registration.", "error")
        
        return render_template('SASStaff/registerST.html',
                            programs=programs_for_dropdown_xml,
                            all_subprogrammes=all_subprogrammes_list_xml,
                            campuses=campuses_from_xml,
                            all_program_types=program_type_names,
                            form_data=request.form,
                            new_student_credentials=None)

    new_student_credentials = session.pop('new_student_credentials', None)
    return render_template(
        'SASStaff/registerST.html',
        programs=programs_for_dropdown_xml,
        all_subprogrammes=all_subprogrammes_list_xml,
        campuses=campuses_from_xml,
        all_program_types=program_type_names,
        new_student_credentials=new_student_credentials,
        form_data={}
    )

@app.route('/sas-staff/edit-student')
def sas_staff_edit_student():
    if session.get('user_type') != 'staff':
        abort(403)
    students_overview_data = []
    try:
        all_students_from_db = Student.query.order_by(Student.StudentID).all()
        for s_db in all_students_from_db:
            full_name_parts = [s_db.FirstName]
            if s_db.MiddleName:
                full_name_parts.append(s_db.MiddleName)
            full_name_parts.append(s_db.LastName)
            full_name = " ".join(filter(None, full_name_parts))
            
            # For Campus, we will use Address as a placeholder for now
            # TODO: Implement proper Campus data (e.g., add a Campus field to Student model or join)
            campus_display = s_db.Address if s_db.Address else "N/A"

            students_overview_data.append({
                'id': s_db.StudentID,
                'full_name': full_name,
                'campus': campus_display # This is currently student's address
            })
    except Exception as e:
        app.logger.error(f"Error fetching students for overview: {e}", exc_info=True)
        flash("Could not load student records.", "error")
    return render_template('SASStaff/editST.html', students=students_overview_data)

@app.route('/sas-staff/display-student/<student_id>')
def sas_staff_display_student(student_id):
    if session.get('user_type') != 'staff': abort(403)
    
    student_details_obj = db.session.get(Student, student_id)
    if not student_details_obj:
        flash(f"Student with ID {student_id} not found.", "error")
        return redirect(url_for('sas_staff_edit_student'))

    program_name = "N/A"
    program_type_name = "N/A"
    student_program_link = Student_Program.query.filter_by(StudentID=student_id).first()
    if student_program_link:
        if student_program_link.program: program_name = student_program_link.program.ProgramName
        if student_program_link.program_type: program_type_name = student_program_link.program_type.ProgramTypeName
            
    student_level_value = "N/A"
    student_level_link = Student_Level.query.filter_by(StudentID=student_id).first()
    if student_level_link and student_level_link.StudentLevel: student_level_value = student_level_link.StudentLevel.value
        
    current_campus_name = student_details_obj.campus.CampusName if student_details_obj.campus else "N/A"

    # Get current enrolled subprograms
    enrolled_subprogram_names = [sp.SubProgramName for sp in student_details_obj.enrolled_subprograms]
    current_subprogram1_name = enrolled_subprogram_names[0] if len(enrolled_subprogram_names) > 0 else ""
    current_subprogram2_name = enrolled_subprogram_names[1] if len(enrolled_subprogram_names) > 1 else ""


    # Data for edit mode dropdowns
    all_program_names = [p.ProgramName for p in Program.query.order_by(Program.ProgramName).all()]
    all_student_level_values = [level.value for level in StudentLevelEnum]
    all_gender_values = [gender.value for gender in GenderEnum]
    all_campus_names = [c.CampusName for c in Campus.query.order_by(Campus.CampusName).all()]
    all_program_type_names = [pt.ProgramTypeName for pt in ProgramType.query.order_by(ProgramType.ProgramTypeName).all()]
    all_subprogrammes_for_dropdown = [sp.SubProgramName for sp in SubProgram.query.order_by(SubProgram.SubProgramName).all()]


    display_data = {
        'id': student_details_obj.StudentID,
        'first_name': student_details_obj.FirstName, 'middle_name': student_details_obj.MiddleName or '', 'last_name': student_details_obj.LastName,
        'address': student_details_obj.Address, 'contact': student_details_obj.Contact,
        'date_of_birth': student_details_obj.DateOfBirth.strftime('%Y-%m-%d') if student_details_obj.DateOfBirth else '',
        'gender': student_details_obj.Gender.value if student_details_obj.Gender else '',
        'citizenship': student_details_obj.Citizenship, 'program_name': program_name,
        'student_level': student_level_value, 'email': student_details_obj.Email,
        'campus_name': current_campus_name, 'program_type_name': program_type_name,
        'subprogram1': current_subprogram1_name, # Pass current subprogram1 name
        'subprogram2': current_subprogram2_name  # Pass current subprogram2 name
    }
    return render_template('SASStaff/displayST.html', 
                           student=display_data,
                           all_programs=all_program_names, all_student_levels=all_student_level_values,
                           all_genders=all_gender_values, all_campuses=all_campus_names,
                           all_program_types=all_program_type_names,
                           all_subprogrammes=all_subprogrammes_for_dropdown)


@app.route('/sas-staff/update-student/<student_id>', methods=['POST'])
def sas_staff_update_student(student_id):
    if session.get('user_type') != 'staff':
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    student_to_update = db.session.get(Student, student_id)
    if not student_to_update:
        return jsonify({"success": False, "message": "Student not found"}), 404

    try:
        data = request.form 
        app.logger.debug(f"Updating student {student_id} with form data: {data}")

        # --- Server-side validation of academic rules ---
        new_level_str = data.get('studentLevel')
        new_program_type_name = data.get('programTypeName')
        new_program_name = data.get('programName')
        subprogram1_form_name = data.get('subprogram1')
        subprogram2_form_name = data.get('subprogram2')

        if not all([new_level_str, new_program_type_name, new_program_name]): # Basic check
             return jsonify({"success": False, "message": "Student Level, Program Type, and Program are required."}), 400

        new_level_enum = StudentLevelEnum(new_level_str) # Will raise ValueError if invalid

        # Rule 1: If Program Type is Single/Double Major, Student Level must be Bachelor.
        if (new_program_type_name == "Single Major" or new_program_type_name == "Double Major") and \
           not new_level_str.lower().includes("bachelor"): # Check if 'bachelor' is part of the string
            return jsonify({"success": False, "message": "Single/Double Major is only applicable for Bachelor level students."}), 400

        # Rule 2: If Student Level is Cert, Dip, Master, PG Dip, Program Type must be Prescribed.
        non_bachelor_prescribed_levels = ["Certificate", "Diploma", "Master", "Postgraduate Diploma"]
        if new_level_str in non_bachelor_prescribed_levels and new_program_type_name != "Prescribed Program":
            return jsonify({"success": False, "message": f"For {new_level_str}, Program Type must be 'Prescribed Program'."}), 400
        
        # Rule 3: Subprogram requirements for Bachelor level
        if new_level_str.lower().includes("bachelor"):
            if new_program_type_name == "Single Major" and not subprogram1_form_name:
                return jsonify({"success": False, "message": "Subprogram 1 is required for Single Major at Bachelor level."}), 400
            if new_program_type_name == "Double Major" and (not subprogram1_form_name or not subprogram2_form_name):
                return jsonify({"success": False, "message": "Subprogram 1 and Subprogram 2 are required for Double Major at Bachelor level."}), 400
            if new_program_type_name == "Double Major" and subprogram1_form_name == subprogram2_form_name and subprogram1_form_name:
                 return jsonify({"success": False, "message": "Subprogram 1 and Subprogram 2 cannot be the same."}), 400
        elif new_program_type_name != "Prescribed Program" and (subprogram1_form_name or subprogram2_form_name):
            # If not bachelor and not prescribed, subprograms should not be set (or this rule needs refinement)
            app.logger.warning(f"Subprograms provided for non-Bachelor/non-Prescribed type for student {student_id}")


        # Rule 4: Program Name prefix validation
        prog_name_lower = new_program_name.lower()
        level_lower = new_level_str.lower()
        prefix_ok = True
        if level_lower == "certificate" and not prog_name_lower.startsWith("certificate in "): prefix_ok = False
        elif level_lower == "diploma" and not prog_name_lower.startsWith("diploma in "): prefix_ok = False
        elif level_lower.includes("bachelor") and not (prog_name_lower.startsWith("bachelor of ") or prog_name_lower.startsWith("bachelor in ")): prefix_ok = False
        elif level_lower.includes("master") and not (prog_name_lower.startsWith("masters in ") or prog_name_lower.startsWith("master of ")): prefix_ok = False
        elif level_lower == "postgraduate diploma" and not prog_name_lower.startsWith("postgraduate diploma in "): prefix_ok = False
        
        if not prefix_ok:
            return jsonify({"success": False, "message": f"Program name '{new_program_name}' does not match the expected prefix for '{new_level_str}' level."}), 400
        # --- End Server-side validation ---


        # Update Student table fields
        student_to_update.FirstName = data.get('firstName', student_to_update.FirstName)
        student_to_update.MiddleName = data.get('middleName', student_to_update.MiddleName) or None
        student_to_update.LastName = data.get('lastName', student_to_update.LastName)
        student_to_update.Contact = data.get('contact', student_to_update.Contact)
        student_to_update.Email = data.get('email', student_to_update.Email)
        if data.get('dateOfBirth'): student_to_update.DateOfBirth = datetime.datetime.strptime(data.get('dateOfBirth'), '%Y-%m-%d').date()
        if data.get('gender'): student_to_update.Gender = GenderEnum(data.get('gender'))
        student_to_update.Citizenship = data.get('citizenship', student_to_update.Citizenship)
        student_to_update.Address = data.get('address', student_to_update.Address)

        selected_campus_name = data.get('campusName')
        if selected_campus_name:
            campus_obj = Campus.query.filter_by(CampusName=selected_campus_name).first()
            if campus_obj: student_to_update.CampusID = campus_obj.CampusID
            else: app.logger.warning(f"Campus '{selected_campus_name}' not found during update for {student_id}")
        
        student_program_link = Student_Program.query.filter_by(StudentID=student_id).first()
        if not student_program_link: # Should not happen for an existing student with a program
            app.logger.error(f"CRITICAL: Student_Program link missing for student {student_id} during update.")
            # Potentially create it if absolutely necessary, but this indicates a data integrity issue.
            # For now, we'll assume it exists or the update for program/type will be skipped.
        
        if student_program_link:
            if new_program_name:
                new_program_obj = Program.query.filter(db.func.lower(Program.ProgramName) == db.func.lower(new_program_name)).first()
                if new_program_obj: student_program_link.ProgramID = new_program_obj.ProgramID
                else: app.logger.warning(f"Program '{new_program_name}' not found during update for {student_id}")

            if new_program_type_name:
                new_program_type_obj = ProgramType.query.filter_by(ProgramTypeName=new_program_type_name).first()
                if new_program_type_obj: student_program_link.ProgramTypeID = new_program_type_obj.ProgramTypeID
                else: app.logger.warning(f"ProgramType '{new_program_type_name}' not found during update for {student_id}")

        if new_student_level_str: # Already validated to be a valid enum string
            student_level_link = Student_Level.query.filter_by(StudentID=student_id).first()
            if student_level_link: student_level_link.StudentLevel = new_level_enum
            else: db.session.add(Student_Level(StudentID=student_id, StudentLevel=new_level_enum))
        
        # Update Subprograms: Clear existing and add new ones based on form
        student_to_update.enrolled_subprograms.clear() # Remove all current subprogram associations
        
        if new_level_str.lower().includes("bachelor"):
            subprograms_to_add_names = []
            if new_program_type_name == "Single Major" and subprogram1_form_name:
                subprograms_to_add_names.append(subprogram1_form_name)
            elif new_program_type_name == "Double Major":
                if subprogram1_form_name: subprograms_to_add_names.append(subprogram1_form_name)
                if subprogram2_form_name and subprogram2_form_name != subprogram1_form_name: # Avoid duplicate
                    subprograms_to_add_names.append(subprogram2_form_name)
            
            for sp_name in subprograms_to_add_names:
                sub_prog_obj = SubProgram.query.filter_by(SubProgramName=sp_name).first()
                if sub_prog_obj:
                    student_to_update.enrolled_subprograms.append(sub_prog_obj)
                else:
                    app.logger.warning(f"Subprogram '{sp_name}' selected in form not found in DB for student {student_id}")

        db.session.commit()
        app.logger.info(f"Student {student_id} updated successfully.")
        return jsonify({"success": True, "message": "Student details updated successfully."})

    except ValueError as ve: # For date/enum conversion errors during data.get or StudentLevelEnum()
        db.session.rollback()
        app.logger.error(f"ValueError updating student {student_id}: {ve}", exc_info=False)
        return jsonify({"success": False, "message": f"Invalid data format: {str(ve)}"}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating student {student_id}: {e}", exc_info=True)
        return jsonify({"success": False, "message": "An unexpected error occurred while updating."}), 500

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
# ... (your existing error handlers: render_error_page, handle_403, etc.) ...
@app.errorhandler(403)
def handle_403(e):
    app.logger.warning(f"Forbidden (403) access attempt to {request.path}. User: {session.get('email')}, Type: {session.get('user_type')}. Error: {e}")
    # return render_error_page(e, 403) # Make sure render_error_page is defined or use simple response
    return "Access Forbidden", 403


@app.errorhandler(404)
def handle_404(e):
    app.logger.warning(f"Not Found (404) at path: {request.path}. Error: {e}")
    # return render_error_page(e, 404)
    return "Page Not Found", 404

@app.errorhandler(500)
def handle_500(e):
    db.session.rollback() # Rollback session on internal server errors
    app.logger.error(f"Internal Server Error (500) at path: {request.path}. Error: {e}", exc_info=True)
    # return render_error_page(e, 500)
    return "Internal Server Error", 500

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    status_code = e.code if hasattr(e, 'code') and e.code is not None else 500
    app.logger.warning(f"HTTP Exception (code {status_code}) at path: {request.path}. Description: {e.description}. Error: {e}")
    # return render_error_page(e, status_code)
    return f"HTTP Error {status_code}: {e.name}", status_code

@app.errorhandler(Exception)
def handle_all_other_exceptions(e):
    if isinstance(e, HTTPException):
        return e # Let specific HTTP handlers or default Werkzeug handler take over
    db.session.rollback()
    app.logger.error(f"Unhandled Non-HTTP Exception at path: {request.path}. Error: {e}", exc_info=True)
    # return render_error_page(e, 500)
    return "An unexpected error occurred", 500


# --- Main Execution Block ---
if __name__ == '__main__':
    if not os.path.exists(app.instance_path):
        try:
            os.makedirs(app.instance_path)
            app.logger.info(f"Created instance folder at {app.instance_path}")
        except OSError as e_mkdir:
            app.logger.error(f"Could not create instance folder: {e_mkdir}")

    app.logger.info(f"Flask App '{app.name}' (SAS_Services) starting...")
    if app.config['SECRET_KEY'] == 'sas_default_insecure_secret_key_CHANGE_THIS_V5':
        app.logger.warning("SECURITY WARNING: Flask SECRET_KEY is using the INSECURE default value.")
    app.logger.info(f"Debug mode: {app.debug}")
    app.logger.info(f"Template folder: {app.template_folder}") # Corrected to use app attribute
    app.logger.info(f"Static folder: {app.static_folder}")   # Corrected
    app.logger.info(f"Data folder (for XMLs): {DATA_FOLDER}")
    app.logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    sas_service_port = int(os.getenv("SAS_SERVICE_PORT", 5006))
    app.run(host='0.0.0.0', port=sas_service_port)