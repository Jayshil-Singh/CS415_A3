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
import requests
import re

# Import 'db' instance AND model classes from models.py
from models import (
    db, Student, Program, Student_Program, Student_Level, Campus, ProgramType,
    SubProgram, # Make sure SubProgram is imported
    GenderEnum, StudentLevelEnum, student_subprogram_association # Import association table if needed directly
)

# --- BASE_DIR and DATA_FOLDER ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_FOLDER = os.path.join(BASE_DIR, 'xml_data')

def generate_random_password(length=10):
    """
    Generate a secure random password for new students.
    Password will contain at least one uppercase letter, one lowercase letter,
    one number, and one special character.
    
    Args:
        length (int): Length of the password (default: 10)
    
    Returns:
        str: A random password meeting the security requirements
    """
    if length < 8:
        length = 8  # Minimum secure length
    
    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = "!@#$%^&*"
    
    # Ensure at least one character from each set
    password = [
        random.choice(lowercase),
        random.choice(uppercase),
        random.choice(digits),
        random.choice(special)
    ]
    
    # Fill the rest with random characters from all sets
    all_characters = lowercase + uppercase + digits + special
    for _ in range(length - 4):
        password.append(random.choice(all_characters))
    
    # Shuffle the password characters
    random.shuffle(password)
    
    return ''.join(password)

def get_next_student_id():
    """
    Generate the next available student ID in the format SXXXXXXXX.
    Returns a string in the format 'SXXXXXXXX' where X is a digit.
    """
    try:
        # Get the last student ID from the database
        last_student = Student.query.order_by(Student.StudentID.desc()).first()
        
        if last_student is None:
            # If no students exist, start with S10000001
            return 'S10000001'
            
        # Extract the numeric part and increment
        last_id = last_student.StudentID
        if not last_id.startswith('S') or not last_id[1:].isdigit():
            app.logger.error(f"Invalid last student ID format: {last_id}")
            return 'S10000001'  # Start fresh if last ID is invalid
            
        next_num = int(last_id[1:]) + 1
        if next_num <= 0:  # Additional validation
            app.logger.error(f"Invalid student ID number: {next_num}")
            return 'S10000001'
            
        # Ensure the number stays within 8 digits
        if next_num > 99999999:
            app.logger.error("Student ID counter has reached maximum value")
            raise ValueError("Student ID counter overflow")
            
        return f'S{next_num:08d}'  # Format with leading zeros
        
    except Exception as e:
        app.logger.error(f"Error generating next student ID: {e}")
        raise

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
    print(f"Warning: .env file not found at expected locations: {DOTENV_PATH} or {os.path.join(APP_DIR, '.env')}")

def get_data_from_xml(filename, list_element_name, item_element_name, value_attribute):
    """
    Load and parse data from XML files.
    
    Args:
        filename (str): Name of the XML file to read
        list_element_name (str): Name of the root element containing the list
        item_element_name (str): Name of individual item elements
        value_attribute (str): Name of the attribute to extract from each item
    
    Returns:
        list: List of values extracted from the XML file
    """
    try:
        xml_file_path = os.path.join(DATA_FOLDER, filename)
        if not os.path.exists(xml_file_path):
            app.logger.error(f"XML file not found: {xml_file_path}")
            return []
            
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        
        if root.tag != list_element_name:
            app.logger.error(f"Root element '{root.tag}' does not match expected '{list_element_name}' in {filename}")
            return []
            
        values = []
        for item in root.findall(item_element_name):
            value = item.get(value_attribute)
            if value:
                values.append(value)
                
        app.logger.debug(f"Loaded {len(values)} items from {filename}")
        return values
        
    except ET.ParseError as e:
        app.logger.error(f"XML parsing error in {filename}: {str(e)}")
        return []
    except Exception as e:
        app.logger.error(f"Error loading data from {filename}: {str(e)}")
        return []

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
app.config['LOGIN_SERVICE_URL'] = os.environ.get('LOGIN_SERVICE_URL', 'http://127.0.0.1:5002')

# Initialize the imported 'db' object (from models.py) with the app
db.init_app(app)

# Hardcoded credentials for staff and admin
STAFF_CREDENTIALS = {
    'SA11103': {  # SAS Manager
        'password': '4321',
        'role': 'sas_manager',
        'username': 'SAS Manager'
    },
    'SS11203': {  # SAS Staff
        'password': '1234',
        'role': 'sas_staff',
        'username': 'SAS Staff'
    },
    'SUPERADMIN': {  # Super Admin
        'password': 'super',
        'role': 'admin',
        'username': 'Super Admin'
    }
}

def validate_staff_id(staff_id):
    """Validate staff ID format"""
    staff_pattern = r'^SS\d{5}$'
    manager_pattern = r'^SA\d{5}$'
    return bool(re.match(staff_pattern, staff_id)) or bool(re.match(manager_pattern, staff_id))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session:
            return render_template('login.html')
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('user_type') not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- User Context Injection ---
@app.context_processor
def inject_user_and_globals():
    user_info = {"current_user": SimpleNamespace(username="Guest", user_type="Guest")}
    if 'email' in session and session.get('user_type'):
        user_info["current_user"] = SimpleNamespace(
            username=session['email'],
            user_type=session.get('user_type')
        )
    user_info['current_year'] = datetime.datetime.now().year
    return user_info

@app.route('/')
def index():
    if 'user_type' in session:
        if session['user_type'] == 'admin':
            return redirect(url_for('super_admin_home'))
        elif session['user_type'] == 'sas_manager':
            return redirect(url_for('sas_manager_home'))
        elif session['user_type'] == 'sas_staff':
            return redirect(url_for('sas_staff_home'))
    return render_template('login.html')

@app.route('/sas-login', methods=['GET', 'POST'])
def sas_login():
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password = request.form.get('password')
        
        if not identifier or not password:
            flash('Please provide both staff ID and password', 'error')
            return render_template('login.html')
        
        # Clean and validate staff ID
        staff_id = identifier.upper()
        if not validate_staff_id(staff_id) and staff_id != 'SUPERADMIN':
            flash('Invalid staff ID format', 'error')
            return render_template('login.html')
        
        # Check credentials
        if staff_id not in STAFF_CREDENTIALS:
            flash('Staff ID not found', 'error')
            return render_template('login.html')
            
        staff_data = STAFF_CREDENTIALS[staff_id]
        if password != staff_data['password']:
            flash('Invalid password', 'error')
            return render_template('login.html')
        
        # Set session data
        session['user_id'] = staff_id
        session['user_type'] = staff_data['role']
        session['username'] = staff_data['username']
        
        # Redirect based on role
        if staff_data['role'] == 'admin':
            return redirect(url_for('super_admin_home'))
        elif staff_data['role'] == 'sas_manager':
            return redirect(url_for('sas_manager_home'))
        else:
            return redirect(url_for('sas_staff_home'))
    
    return render_template('login.html')

@app.route("/sas-logout")
def sas_logout():
    session.clear()
    return render_template('login.html')

@app.route('/super-admin/home')
@login_required
@role_required('admin')
def super_admin_home():
    return render_template('SuperAdmin/SAdminHome.html')

@app.route('/super-admin/remove-staff')
@login_required
@role_required('admin')
def super_admin_remove_staff():
    return render_template('SuperAdmin/RemoveStaff.html')

@app.route('/sas-manager/home')
@login_required
@role_required('sas_manager')
def sas_manager_home():
    return render_template('SASManager/homeSAS.html')

@app.route('/sas-staff/home')
@login_required
@role_required('sas_staff')
def sas_staff_home():
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

def validate_student_registration_data(form_data):
    """
    Validate student registration form data.
    Returns (is_valid, error_message)
    """
    required_fields = [
        'firstName', 'lastName', 'contact', 'dateOfBirth', 'gender',
        'citizenship', 'address', 'program', 'studentLevel', 'campus', 'programType',
        'passportNumber'  # Added passport number as required field
    ]
    
    # Check required fields
    for field in required_fields:
        if not form_data.get(field):
            return False, f"{field.capitalize()} is required."
    
    # Validate passport number format (basic validation)
    passport_number = form_data.get('passportNumber')
    if not re.match(r'^[A-Z0-9]{8,9}$', passport_number):
        return False, "Invalid passport number format. Must be 8-9 alphanumeric characters."

    # Validate visa expiry date if visa status is provided and not N/A
    visa_status = form_data.get('visaStatus', '').strip()
    visa_expiry = form_data.get('visaExpiry', '').strip()
    
    if visa_status and visa_status.upper() != 'N/A':
        if not visa_expiry:
            return False, "Visa expiry date is required when visa status is provided."
        try:
            expiry_date = datetime.datetime.strptime(visa_expiry, '%Y-%m-%d').date()
            if expiry_date < datetime.date.today():
                return False, "Visa expiry date cannot be in the past."
        except ValueError:
            return False, "Invalid visa expiry date format."
    
    # Validate contact number (simple validation)
    contact = form_data.get('contact')
    if not re.match(r'^\+?[\d\s-]{8,}$', contact):
        return False, "Invalid contact number format."
    
    # Validate date of birth
    try:
        dob = datetime.datetime.strptime(form_data.get('dateOfBirth'), '%Y-%m-%d').date()
        today = datetime.date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 15:
            return False, "Student must be at least 15 years old."
        if age > 100:
            return False, "Invalid date of birth."
    except ValueError:
        return False, "Invalid date format for date of birth."
    
    # Validate program type and level combinations
    student_level = form_data.get('studentLevel').lower()
    program_type = form_data.get('programType')
    
    if program_type in ['Single Major', 'Double Major'] and 'bachelor' not in student_level:
        return False, "Single/Double Major is only applicable for Bachelor level students."
    
    non_bachelor_levels = ['certificate', 'diploma', 'master', 'postgraduate diploma']
    if any(level in student_level for level in non_bachelor_levels) and program_type != 'Prescribed Program':
        return False, f"For {student_level.title()}, Program Type must be 'Prescribed Program'."
    
    # Validate subprogram requirements for Bachelor level
    if 'bachelor' in student_level:
        if program_type == 'Single Major' and not form_data.get('subprogram1'):
            return False, "Subprogram 1 is required for Single Major at Bachelor level."
        if program_type == 'Double Major':
            if not form_data.get('subprogram1') or not form_data.get('subprogram2'):
                return False, "Both subprograms are required for Double Major at Bachelor level."
            if form_data.get('subprogram1') == form_data.get('subprogram2'):
                return False, "Subprogram 1 and Subprogram 2 cannot be the same."
    
    return True, ""

@app.route('/sas-staff/register-student', methods=['GET', 'POST'])
@login_required
@role_required('sas_staff')
def sas_staff_register_student():
    # Load XML data
    try:
        programs_for_dropdown = get_data_from_xml(
            filename='programs.xml',
            list_element_name='programs',
            item_element_name='program',
            value_attribute='programName'
        )
        all_subprogrammes = get_data_from_xml(
            filename='subprogrammes.xml',
            list_element_name='subprograms',
            item_element_name='subprogram',
            value_attribute='subprogramName'
        )
        campuses = get_data_from_xml(
            filename='campuses.xml',
            list_element_name='campuses',
            item_element_name='campus',
            value_attribute='campusName'
        )
        program_type_names = [pt.ProgramTypeName for pt in ProgramType.query.all()]
        
        app.logger.debug(f"Loaded data - Programs: {len(programs_for_dropdown)}, Subprograms: {len(all_subprogrammes)}, Campuses: {len(campuses)}")
    except Exception as e:
        app.logger.error(f"Error loading XML data: {e}")
        programs_for_dropdown = []
        all_subprogrammes = []
        campuses = []
        program_type_names = []

    if request.method == 'POST':
        try:
            # Validate form data
            is_valid, error_message = validate_student_registration_data(request.form)
            if not is_valid:
                flash(error_message, "error")
                return render_template('SASStaff/registerST.html',
                                    programs=programs_for_dropdown,
                                    all_subprogrammes=all_subprogrammes,
                                    campuses=campuses,
                                    all_program_types=program_type_names,
                                    form_data=request.form)

            # --- Form Data Retrieval ---
            first_name = request.form.get('firstName')
            middle_name = request.form.get('middleName') or None
            last_name = request.form.get('lastName')
            contact = request.form.get('contact')
            dob_str = request.form.get('dateOfBirth')
            gender_str = request.form.get('gender')
            citizenship = request.form.get('citizenship')
            address = request.form.get('address')
            passport_number = request.form.get('passportNumber')
            visa_status = request.form.get('visaStatus', 'N/A').strip()
            visa_expiry_str = request.form.get('visaExpiry')
            
            selected_program_name = request.form.get('program')
            student_level_str = request.form.get('studentLevel')
            selected_campus_name = request.form.get('campus')
            selected_program_type_name = request.form.get('programType')
            subprogram1_name = request.form.get('subprogram1')
            subprogram2_name = request.form.get('subprogram2')

            date_of_birth = datetime.datetime.strptime(dob_str, '%Y-%m-%d').date()
            visa_expiry_date = None
            if visa_status and visa_status.upper() != 'N/A' and visa_expiry_str:
                visa_expiry_date = datetime.datetime.strptime(visa_expiry_str, '%Y-%m-%d').date()
            
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
                'CampusID': campus_obj.CampusID,
                'PassportNumber': passport_number,
                'VisaStatus': visa_status,
                'VisaExpiryDate': visa_expiry_date
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
                            programs=programs_for_dropdown,
                            all_subprogrammes=all_subprogrammes,
                            campuses=campuses,
                            all_program_types=program_type_names,
                            form_data=request.form)

    new_student_credentials = session.pop('new_student_credentials', None)
    return render_template(
        'SASStaff/registerST.html',
        programs=programs_for_dropdown,
        all_subprogrammes=all_subprogrammes,
        campuses=campuses,
        all_program_types=program_type_names,
        new_student_credentials=new_student_credentials,
        form_data={}
    )

@app.route('/sas-staff/edit-student')
@login_required
@role_required('sas_staff')
def sas_staff_edit_student():
    students_overview_data = []
    try:
        all_students_from_db = Student.query.order_by(Student.StudentID).all()
        for s_db in all_students_from_db:
            full_name_parts = [s_db.FirstName]
            if s_db.MiddleName:
                full_name_parts.append(s_db.MiddleName)
            full_name_parts.append(s_db.LastName)
            full_name = " ".join(filter(None, full_name_parts))
            
            campus_display = s_db.Address if s_db.Address else "N/A"

            students_overview_data.append({
                'id': s_db.StudentID,
                'full_name': full_name,
                'campus': campus_display
            })
    except Exception as e:
        app.logger.error(f"Error fetching students for overview: {e}", exc_info=True)
        flash("Could not load student records.", "error")
    return render_template('SASStaff/editST.html', students=students_overview_data)

@app.route('/sas-staff/display-student/<student_id>')
@login_required
@role_required('sas_staff')
def sas_staff_display_student(student_id):
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
        'subprogram1': current_subprogram1_name,
        'subprogram2': current_subprogram2_name,
        'passport_number': student_details_obj.PassportNumber or '',
        'visa_status': student_details_obj.VisaStatus or 'N/A',
        'visa_expiry': student_details_obj.VisaExpiryDate.strftime('%Y-%m-%d') if student_details_obj.VisaExpiryDate else ''
    }
    return render_template('SASStaff/displayST.html', 
                           student=display_data,
                           all_programs=all_program_names, all_student_levels=all_student_level_values,
                           all_genders=all_gender_values, all_campuses=all_campus_names,
                           all_program_types=all_program_type_names,
                           all_subprogrammes=all_subprogrammes_for_dropdown)

def update_student_in_service_db(student_data):
    """
    Update student information in the StudentService database.
    
    Args:
        student_data (dict): Dictionary containing student information to update
    """
    try:
        # Get the path to the StudentService database
        student_service_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                             'StudentService', 'instance', 'studentservice.db')
        
        if not os.path.exists(student_service_db_path):
            app.logger.error(f"StudentService database not found at: {student_service_db_path}")
            raise FileNotFoundError("StudentService database not found")

        # Connect to the StudentService database
        conn = sqlite3.connect(student_service_db_path)
        cursor = conn.cursor()

        # Update student data
        cursor.execute("""
            UPDATE Student 
            SET FirstName = ?,
                MiddleName = ?,
                LastName = ?,
                Contact = ?,
                Email = ?,
                DateOfBirth = ?,
                Gender = ?,
                Citizenship = ?,
                Address = ?,
                CampusID = ?,
                PassportNumber = ?,
                VisaStatus = ?,
                VisaExpiryDate = ?
            WHERE StudentID = ?
        """, (
            student_data['FirstName'],
            student_data['MiddleName'],
            student_data['LastName'],
            student_data['Contact'],
            student_data['Email'],
            student_data['DateOfBirth'].isoformat() if student_data['DateOfBirth'] else None,
            student_data['Gender'].value if student_data['Gender'] else None,
            student_data['Citizenship'],
            student_data['Address'],
            student_data['CampusID'],
            student_data['PassportNumber'],
            student_data['VisaStatus'],
            student_data['VisaExpiryDate'].isoformat() if student_data['VisaExpiryDate'] else None,
            student_data['StudentID']
        ))

        # Commit the changes and close the connection
        conn.commit()
        conn.close()
        
        app.logger.info(f"Successfully updated student {student_data['StudentID']} in StudentService database")
        
    except sqlite3.Error as e:
        app.logger.error(f"Database error while updating student in StudentService: {e}")
        raise
    except Exception as e:
        app.logger.error(f"Error updating student in StudentService database: {e}")
        raise

@app.route('/sas-staff/update-student/<student_id>', methods=['POST'])
@login_required
@role_required('sas_staff')
def sas_staff_update_student(student_id):
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

        if not all([new_level_str, new_program_type_name, new_program_name]):
             return jsonify({"success": False, "message": "Student Level, Program Type, and Program are required."}), 400

        new_level_enum = StudentLevelEnum(new_level_str)

        # Rule 1: If Program Type is Single/Double Major, Student Level must be Bachelor.
        if (new_program_type_name == "Single Major" or new_program_type_name == "Double Major") and \
           "bachelor" not in new_level_str.lower():
            return jsonify({"success": False, "message": "Single/Double Major is only applicable for Bachelor level students."}), 400

        # Rule 2: If Student Level is Cert, Dip, Master, PG Dip, Program Type must be Prescribed.
        non_bachelor_prescribed_levels = ["Certificate", "Diploma", "Master", "Postgraduate Diploma"]
        if new_level_str in non_bachelor_prescribed_levels and new_program_type_name != "Prescribed Program":
            return jsonify({"success": False, "message": f"For {new_level_str}, Program Type must be 'Prescribed Program'."}), 400
        
        # Rule 3: Subprogram requirements for Bachelor level
        if "bachelor" in new_level_str.lower():
            if new_program_type_name == "Single Major" and not subprogram1_form_name:
                return jsonify({"success": False, "message": "Subprogram 1 is required for Single Major at Bachelor level."}), 400
            if new_program_type_name == "Double Major" and (not subprogram1_form_name or not subprogram2_form_name):
                return jsonify({"success": False, "message": "Subprogram 1 and Subprogram 2 are required for Double Major at Bachelor level."}), 400
            if new_program_type_name == "Double Major" and subprogram1_form_name == subprogram2_form_name and subprogram1_form_name:
                 return jsonify({"success": False, "message": "Subprogram 1 and Subprogram 2 cannot be the same."}), 400

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
        
        # Update passport and visa information
        student_to_update.PassportNumber = data.get('passportNumber', student_to_update.PassportNumber)
        visa_status = data.get('visaStatus', '').strip()
        student_to_update.VisaStatus = None if visa_status.upper() == 'N/A' else visa_status
        
        visa_expiry = data.get('visaExpiry', '').strip()
        if visa_expiry and visa_status.upper() != 'N/A':
            student_to_update.VisaExpiryDate = datetime.datetime.strptime(visa_expiry, '%Y-%m-%d').date()
        else:
            student_to_update.VisaExpiryDate = None

        selected_campus_name = data.get('campusName')
        if selected_campus_name:
            campus_obj = Campus.query.filter_by(CampusName=selected_campus_name).first()
            if campus_obj: student_to_update.CampusID = campus_obj.CampusID
            else: app.logger.warning(f"Campus '{selected_campus_name}' not found during update for {student_id}")
        
        student_program_link = Student_Program.query.filter_by(StudentID=student_id).first()
        if not student_program_link:
            app.logger.error(f"CRITICAL: Student_Program link missing for student {student_id} during update.")
        
        if student_program_link:
            if new_program_name:
                new_program_obj = Program.query.filter(db.func.lower(Program.ProgramName) == db.func.lower(new_program_name)).first()
                if new_program_obj: student_program_link.ProgramID = new_program_obj.ProgramID
                else: app.logger.warning(f"Program '{new_program_name}' not found during update for {student_id}")

            if new_program_type_name:
                new_program_type_obj = ProgramType.query.filter_by(ProgramTypeName=new_program_type_name).first()
                if new_program_type_obj: student_program_link.ProgramTypeID = new_program_type_obj.ProgramTypeID
                else: app.logger.warning(f"ProgramType '{new_program_type_name}' not found during update for {student_id}")

        if new_level_str:
            student_level_link = Student_Level.query.filter_by(StudentID=student_id).first()
            if student_level_link: student_level_link.StudentLevel = new_level_enum
            else: db.session.add(Student_Level(StudentID=student_id, StudentLevel=new_level_enum))
        
        # Update Subprograms
        student_to_update.enrolled_subprograms.clear()
        
        if "bachelor" in new_level_str.lower():
            subprograms_to_add_names = []
            if new_program_type_name == "Single Major" and subprogram1_form_name:
                subprograms_to_add_names.append(subprogram1_form_name)
            elif new_program_type_name == "Double Major":
                if subprogram1_form_name: subprograms_to_add_names.append(subprogram1_form_name)
                if subprogram2_form_name and subprogram2_form_name != subprogram1_form_name:
                    subprograms_to_add_names.append(subprogram2_form_name)
            
            for sp_name in subprograms_to_add_names:
                sub_prog_obj = SubProgram.query.filter_by(SubProgramName=sp_name).first()
                if sub_prog_obj:
                    student_to_update.enrolled_subprograms.append(sub_prog_obj)
                else:
                    app.logger.warning(f"Subprogram '{sp_name}' selected in form not found in DB for student {student_id}")

        # Prepare data for StudentService database update
        student_service_data = {
            'StudentID': student_to_update.StudentID,
            'FirstName': student_to_update.FirstName,
            'MiddleName': student_to_update.MiddleName,
            'LastName': student_to_update.LastName,
            'Contact': student_to_update.Contact,
            'Email': student_to_update.Email,
            'DateOfBirth': student_to_update.DateOfBirth,
            'Gender': student_to_update.Gender,
            'Citizenship': student_to_update.Citizenship,
            'Address': student_to_update.Address,
            'CampusID': student_to_update.CampusID,
            'PassportNumber': student_to_update.PassportNumber,
            'VisaStatus': student_to_update.VisaStatus,
            'VisaExpiryDate': student_to_update.VisaExpiryDate
        }

        # Update both databases
        db.session.commit()
        update_student_in_service_db(student_service_data)
        
        app.logger.info(f"Student {student_id} updated successfully in both databases.")
        return jsonify({"success": True, "message": "Student details updated successfully in both databases."})

    except ValueError as ve:
        db.session.rollback()
        app.logger.error(f"ValueError updating student {student_id}: {ve}", exc_info=False)
        return jsonify({"success": False, "message": f"Invalid data format: {str(ve)}"}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating student {student_id}: {e}", exc_info=True)
        return jsonify({"success": False, "message": "An unexpected error occurred while updating."}), 500

@app.route('/sas-staff/grade-rechecks')
@login_required
@role_required('sas_staff')
def sas_staff_grade_rechecks():
    recheck_applications = [ # Mock data
        {"student_id": "S11223344", "first_name": "Alice", "last_name": "Wonderland", "campus": "Laucala", "course_code": "CS111", "coordinator_name": "Dr. Elara Vance", "receipt_image_url": url_for('static', filename='images/mock_receipt1.png')},
        {"student_id": "S11000077", "first_name": "Bob", "last_name": "The Builder", "campus": "Lautoka", "course_code": "MA111", "coordinator_name": "Prof. Ian Field", "receipt_image_url": url_for('static', filename='images/mock_receipt2.png')}
    ]
    return render_template('SASStaff/gradeRE.html', applications=recheck_applications)

@app.route('/sas-staff/all-students-grades')
@login_required
@role_required('sas_staff')
def sas_staff_all_student_enrollments():
    student_enrollments_data = [ # Mock data
        {"student_id": "S11223344", "full_name": "Alice Wonderland", "course_enrolled_in": "CS111 - Introduction to Computing", "campus": "Laucala" },
        {"student_id": "S11000077", "full_name": "Bob The Builder", "course_enrolled_in": "MA111 - Calculus I", "campus": "Lautoka"}
    ]
    for enrollment in student_enrollments_data:
        course_parts = enrollment["course_enrolled_in"].split(" - ")
        course_code = course_parts[0] if len(course_parts) > 0 else "UNKNOWN"
        enrollment["change_grade_action"] = f"change_grade('{enrollment['student_id']}', '{course_code}')"
    return render_template('SASStaff/allST.html', enrollments=student_enrollments_data)

def register_student_in_service_db(student_data):
    """
    Register a student in the StudentService database.
    
    Args:
        student_data (dict): Dictionary containing student information
    """
    try:
        # Get the path to the StudentService database
        student_service_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                             'StudentService', 'instance', 'studentservice.db')
        
        if not os.path.exists(student_service_db_path):
            app.logger.error(f"StudentService database not found at: {student_service_db_path}")
            raise FileNotFoundError("StudentService database not found")

        # Connect to the StudentService database
        conn = sqlite3.connect(student_service_db_path)
        cursor = conn.cursor()

        # Create Student table if it doesn't exist (matching the schema from enrollment.db)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Student (
                StudentID VARCHAR(9) PRIMARY KEY,
                FirstName VARCHAR(100) NOT NULL,
                MiddleName VARCHAR(100),
                LastName VARCHAR(100) NOT NULL,
                Contact VARCHAR(20) NOT NULL,
                Email VARCHAR(120) UNIQUE NOT NULL,
                DateOfBirth DATE NOT NULL,
                Gender VARCHAR(20) NOT NULL,
                Citizenship VARCHAR(100) NOT NULL,
                Address VARCHAR(255) NOT NULL,
                PasswordHash VARCHAR(128) NOT NULL,
                CampusID INTEGER,
                PassportNumber VARCHAR(20),
                VisaStatus VARCHAR(50),
                VisaExpiryDate DATE
            )
        """)

        # Insert student data
        cursor.execute("""
            INSERT INTO Student (
                StudentID, FirstName, MiddleName, LastName, Contact, Email,
                DateOfBirth, Gender, Citizenship, Address, PasswordHash, CampusID,
                PassportNumber, VisaStatus, VisaExpiryDate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student_data['StudentID'],
            student_data['FirstName'],
            student_data['MiddleName'],
            student_data['LastName'],
            student_data['Contact'],
            student_data['Email'],
            student_data['DateOfBirth'].isoformat(),
            student_data['Gender'].value,
            student_data['Citizenship'],
            student_data['Address'],
            student_data['PasswordHash'],
            student_data['CampusID'],
            student_data['PassportNumber'],
            student_data['VisaStatus'] if student_data['VisaStatus'] != 'N/A' else None,
            student_data['VisaExpiryDate'].isoformat() if student_data.get('VisaExpiryDate') else None
        ))

        # Commit the changes and close the connection
        conn.commit()
        conn.close()
        
        app.logger.info(f"Successfully registered student {student_data['StudentID']} in StudentService database")
        
    except sqlite3.IntegrityError as e:
        app.logger.error(f"Database integrity error while registering student in StudentService: {e}")
        raise ValueError(f"Student with ID {student_data['StudentID']} or email {student_data['Email']} already exists in StudentService database")
    except Exception as e:
        app.logger.error(f"Error registering student in StudentService database: {e}")
        raise

# --- Error Handlers ---
@app.errorhandler(403)
def handle_403(e):
    app.logger.warning(f"Forbidden (403) access attempt to {request.path}. User: {session.get('email')}, Type: {session.get('user_type')}. Error: {e}")
    return render_template('errors/403.html', error=e), 403

@app.errorhandler(404)
def handle_404(e):
    app.logger.warning(f"Not Found (404) at path: {request.path}. Error: {e}")
    return render_template('errors/404.html', error=e), 404

@app.errorhandler(500)
def handle_500(e):
    db.session.rollback() # Rollback session on internal server errors
    app.logger.error(f"Internal Server Error (500) at path: {request.path}. Error: {e}", exc_info=True)
    return render_template('errors/500.html', error=e), 500

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    status_code = e.code if hasattr(e, 'code') and e.code is not None else 500
    app.logger.warning(f"HTTP Exception (code {status_code}) at path: {request.path}. Description: {e.description}. Error: {e}")
    return render_template('errors/generic_http_error.html', error=e, status_code=status_code), status_code

@app.errorhandler(Exception)
def handle_all_other_exceptions(e):
    if isinstance(e, HTTPException):
        return e # Let specific HTTP handlers or default Werkzeug handler take over
    db.session.rollback()
    app.logger.error(f"Unhandled Non-HTTP Exception at path: {request.path}. Error: {e}", exc_info=True)
    return render_template('errors/500.html', error=e), 500


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