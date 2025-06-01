from http.client import HTTPException
import os
import xml.etree.ElementTree as ET
from flask import (
    Flask, jsonify, request, send_from_directory, render_template,
    redirect, url_for, flash, abort, session, send_file
)
from werkzeug.security import generate_password_hash, check_password_hash # For passwords
from werkzeug.exceptions import HTTPException
from types import SimpleNamespace
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime, date
import random
import string
import sqlite3
import requests
import re
from werkzeug.utils import secure_filename

# Import 'db' instance AND model classes from models.py
from models import (
    db, Student, Program, Student_Program, Student_Level, Campus, ProgramType,
    SubProgram, # Make sure SubProgram is imported
    GenderEnum, StudentLevelEnum, student_subprogram_association, # Import association table if needed directly
    BirthCertificate, ValidID, AcademicTranscript, Addressing_Student, # Import new models
    Emergency_Contact # Import new model
)

# --- BASE_DIR and DATA_FOLDER ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_FOLDER = os.path.join(BASE_DIR, 'xml_data')

# Document upload configuration
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'instance', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {
    'birth_certificate': {'pdf', 'docx'},
    'valid_id': {'pdf', 'docx', 'jpg', 'jpeg', 'png'},
    'academic_transcript': {'pdf', 'docx'}
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

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
    user_info['current_year'] = datetime.now().year
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
    """Validate student registration form data"""
    errors = []
    
    # Required fields
    required_fields = [
        'firstName', 'lastName', 'dateOfBirth', 'gender', 'citizenship',
        'passportNumber', 'address', 'contact', 'studentLevel', 'program',
        'programType', 'campus', 'province', 'country'
    ]
    
    # Check for missing required fields
    for field in required_fields:
        if not form_data.get(field):
            errors.append(f"{field} is required")
    
    # Validate date format
    if form_data.get('dateOfBirth'):
        try:
            datetime.strptime(form_data['dateOfBirth'], '%Y-%m-%d')
        except ValueError:
            errors.append("Invalid date format for Date of Birth")
        
    # Validate contact number format (simple check for now)
    if form_data.get('contact') and not re.match(r'^\d{3}-\d{7}$', form_data['contact']):
        errors.append("Contact number must be in format: XXX-XXXXXXX")
    
    return errors

@app.route('/sas-staff/register-student', methods=['GET', 'POST'])
@login_required
@role_required('sas_staff')
def sas_staff_register_student():
    try:
        # Load XML data
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
            errors = validate_student_registration_data(request.form)
            if errors:
                flash(", ".join(errors), "error")
                return render_template('SASStaff/registerST.html',
                                    programs=programs_for_dropdown,
                                    all_subprogrammes=all_subprogrammes,
                                    campuses=campuses,
                                    all_program_types=program_type_names,
                                    form_data=request.form)

            # --- Form Data Retrieval ---
            form_data = request.form
            first_name = form_data.get('firstName')
            middle_name = form_data.get('middleName') or None
            last_name = form_data.get('lastName')
            contact = form_data.get('contact')
            dob_str = form_data.get('dateOfBirth')
            gender_str = form_data.get('gender')
            citizenship = form_data.get('citizenship')
            address = form_data.get('address')
            passport_number = form_data.get('passportNumber')
            visa_status = form_data.get('visaStatus', 'N/A').strip()
            visa_expiry_str = form_data.get('visaExpiry')
            
            selected_program_name = form_data.get('program')
            student_level_str = form_data.get('studentLevel')
            selected_campus_name = form_data.get('campus')
            selected_program_type_name = form_data.get('programType')
            subprogram1_name = form_data.get('subprogram1')
            subprogram2_name = form_data.get('subprogram2')

            date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
            visa_expiry_date = None
            if visa_status and visa_status.upper() != 'N/A' and visa_expiry_str:
                visa_expiry_date = datetime.strptime(visa_expiry_str, '%Y-%m-%d').date()
            
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
                'VisaExpiryDate': visa_expiry_date,
                'Province': "Rewa",
                'Country': "Fiji",
                'ZipCode': ""
            }

            # Create Student in main database
            new_student = Student(**{k: v for k, v in student_data.items() if k not in ['Province', 'Country', 'ZipCode']})
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

            # Create address record
            new_address = Addressing_Student(
                StudentID=student_id,
                Province=student_data['Province'],
                Country=student_data['Country'],
                ZipCode=student_data['ZipCode']
            )
            db.session.add(new_address)

            # Register in StudentService database
            register_student_in_service_db(student_data)
            
            # Commit changes to main database
            db.session.commit()
            
            # Handle document uploads
            try:
                # Create upload folder for student if it doesn't exist
                student_folder = os.path.join(UPLOAD_FOLDER, str(student_id))
                os.makedirs(student_folder, exist_ok=True)

                # Process birth certificate
                if 'birth_certificate' in request.files:
                    file = request.files['birth_certificate']
                    if file and file.filename and allowed_file(file.filename, 'birth_certificate'):
                        doc_folder = os.path.join(student_folder, 'birth_certificate')
                        os.makedirs(doc_folder, exist_ok=True)
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(doc_folder, filename)
                        file.save(file_path)
                        new_doc = BirthCertificate(
                            student_id=student_id,
                            filename=filename,
                            file_path=file_path,
                            verified=False
                        )
                        db.session.add(new_doc)

                # Process valid ID
                if 'valid_id' in request.files:
                    file = request.files['valid_id']
                    id_type = request.form.get('id_type')
                    if file and file.filename and allowed_file(file.filename, 'valid_id'):
                        doc_folder = os.path.join(student_folder, 'valid_id')
                        os.makedirs(doc_folder, exist_ok=True)
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(doc_folder, filename)
                        file.save(file_path)
                        new_doc = ValidID(
                            student_id=student_id,
                            filename=filename,
                            file_path=file_path,
                            id_type=id_type,
                            verified=False
                        )
                        db.session.add(new_doc)

                db.session.commit()
                flash(f"Student {student_id} registered successfully! Their password is: {raw_password}", "success")
                return redirect(url_for('sas_staff_display_student', student_id=student_id))

            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error during document upload: {e}")
                flash("Error during document upload. Please try again.", "error")
                return render_template('SASStaff/registerST.html',
                                    programs=programs_for_dropdown,
                                    all_subprogrammes=all_subprogrammes,
                                    campuses=campuses,
                                    all_program_types=program_type_names,
                                    form_data=request.form)

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error during student registration: {e}")
            flash("Error during student registration. Please try again.", "error")
            return render_template('SASStaff/registerST.html',
                                programs=programs_for_dropdown,
                                all_subprogrammes=all_subprogrammes,
                                campuses=campuses,
                                all_program_types=program_type_names,
                                form_data=request.form)

    # GET request - display registration form
    return render_template('SASStaff/registerST.html',
                         programs=programs_for_dropdown,
                         all_subprogrammes=all_subprogrammes,
                         campuses=campuses,
                         all_program_types=program_type_names)

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

    # Get document data and emergency contact from enrollment database
    birth_certificate_data = None
    valid_id_data = None
    academic_transcript_data = None
    emergency_contact_data = None
    
    try:
        # Get emergency contact using SQLAlchemy ORM
        emergency_contact = Emergency_Contact.query.filter_by(StudentID=student_id).first()
        if emergency_contact:
            emergency_contact_data = {
                'FirstName': emergency_contact.FirstName,
                'MiddleName': emergency_contact.MiddleName,
                'LastName': emergency_contact.LastName,
                'Relationship': emergency_contact.Relationship,
                'ContactPhone': emergency_contact.ContactPhone
            }
        
        # Get document data
        birth_cert = BirthCertificate.query.filter_by(student_id=student_id).first()
        if birth_cert:
            birth_certificate_data = {
                'DocumentID': birth_cert.id,
                'FileName': birth_cert.filename,
                'FilePath': birth_cert.file_path,
                'VerificationStatus': 'Verified' if birth_cert.verified else 'Pending',
                'UploadDate': birth_cert.upload_date
            }
        
        valid_id = ValidID.query.filter_by(student_id=student_id).first()
        if valid_id:
            valid_id_data = {
                'DocumentID': valid_id.id,
                'FileName': valid_id.filename,
                'FilePath': valid_id.file_path,
                'VerificationStatus': 'Verified' if valid_id.verified else 'Pending',
                'UploadDate': valid_id.upload_date,
                'IDType': valid_id.id_type
            }
        
        transcript = AcademicTranscript.query.filter_by(student_id=student_id).first()
        if transcript:
            academic_transcript_data = {
                'DocumentID': transcript.id,
                'FileName': transcript.filename,
                'FilePath': transcript.file_path,
                'VerificationStatus': 'Verified' if transcript.verified else 'Pending',
                'UploadDate': transcript.upload_date,
                'TranscriptType': transcript.year_level
            }
            
    except Exception as e:
        app.logger.error(f"Error fetching document data: {e}", exc_info=True)
        
    # Add debug logging
    app.logger.debug(f"Document data retrieved - Birth Certificate: {birth_certificate_data}, Valid ID: {valid_id_data}, Academic Transcript: {academic_transcript_data}")
    app.logger.debug(f"Emergency contact data retrieved: {emergency_contact_data}")

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
        'visa_expiry': student_details_obj.VisaExpiryDate.strftime('%Y-%m-%d') if student_details_obj.VisaExpiryDate else '',
        'address_info': student_details_obj.address_info.to_dict() if student_details_obj.address_info else None,
        'birth_certificate': birth_certificate_data,
        'valid_id': valid_id_data,
        'academic_transcript': academic_transcript_data,
        'emergency_contact': emergency_contact_data
    }
    return render_template('SASStaff/displayST.html', 
                           student=display_data,
                           all_programs=all_program_names, all_student_levels=all_student_level_values,
                           all_genders=all_gender_values, all_campuses=all_campus_names,
                           all_program_types=all_program_type_names,
                           all_subprogrammes=all_subprogrammes_for_dropdown)

def update_student_in_service_db(student_data):
    """Update student information in the StudentService database."""
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

        # Create Emergency_Contact table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Emergency_Contact (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                StudentID VARCHAR(20) NOT NULL,
                FirstName VARCHAR(100) NOT NULL,
                MiddleName VARCHAR(100),
                LastName VARCHAR(100) NOT NULL,
                Relationship VARCHAR(50) NOT NULL,
                ContactPhone VARCHAR(20) NOT NULL,
                FOREIGN KEY (StudentID) REFERENCES Student(StudentID) ON DELETE CASCADE
            )
        """)

        # Update student details
        cursor.execute("""
            UPDATE Student 
            SET FirstName=?, MiddleName=?, LastName=?, DateOfBirth=?, Gender=?, 
                Citizenship=?, Contact=?, Email=?, Address=?, PassportNumber=?, 
                VisaStatus=?, VisaExpiryDate=?
            WHERE StudentID=?
        """, (
            student_data['FirstName'], student_data['MiddleName'], student_data['LastName'],
            student_data['DateOfBirth'], student_data['Gender'], student_data['Citizenship'],
            student_data['Contact'], student_data['Email'], student_data['Address'],
            student_data['PassportNumber'], student_data['VisaStatus'], student_data['VisaExpiryDate'],
            student_data['StudentID']
        ))

        # Update or insert address info
        cursor.execute("""
            INSERT OR REPLACE INTO Addressing_Student (StudentID, Province, Country, ZipCode)
            VALUES (?, ?, ?, ?)
        """, (
            student_data['StudentID'], student_data['Province'],
            student_data['Country'], student_data['ZipCode']
        ))

        # Update or insert emergency contact info
        if 'EmergencyContact' in student_data:
            ec = student_data['EmergencyContact']
            cursor.execute("""
                INSERT OR REPLACE INTO Emergency_Contact 
                (StudentID, FirstName, MiddleName, LastName, Relationship, ContactPhone)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                student_data['StudentID'], ec['FirstName'], ec['MiddleName'],
                ec['LastName'], ec['Relationship'], ec['ContactPhone']
            ))

        conn.commit()
        app.logger.info(f"Successfully updated student {student_data['StudentID']} in StudentService database")
        
    except Exception as e:
        app.logger.error(f"Error updating student in StudentService database: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

@app.route('/sas-staff/update-student/<student_id>', methods=['POST'])
@login_required
@role_required('sas_staff')
def update_student(student_id):
    try:
        student = Student.query.get_or_404(student_id)
        
        # Update student details
        student.FirstName = request.form.get('firstName', student.FirstName)
        student.MiddleName = request.form.get('middleName', student.MiddleName)
        student.LastName = request.form.get('lastName', student.LastName)
        student.DateOfBirth = datetime.strptime(request.form['dateOfBirth'], '%Y-%m-%d').date() if request.form.get('dateOfBirth') else student.DateOfBirth
        student.Gender = GenderEnum(request.form.get('gender', student.Gender.value if student.Gender else None))
        student.Citizenship = request.form.get('citizenship', student.Citizenship)
        student.Contact = request.form.get('contact', student.Contact)
        student.Email = request.form.get('email', student.Email)
        student.Address = request.form.get('address', student.Address)
        student.PassportNumber = request.form.get('passportNumber', student.PassportNumber)
        student.VisaStatus = request.form.get('visaStatus', student.VisaStatus)
        student.VisaExpiryDate = datetime.strptime(request.form['visaExpiry'], '%Y-%m-%d').date() if request.form.get('visaExpiry') else student.VisaExpiryDate

        # Update address information
        address_info = student.address_info or Addressing_Student(StudentID=student_id)
        address_info.Province = request.form.get('province', address_info.Province if address_info else None)
        address_info.Country = request.form.get('country', address_info.Country if address_info else None)
        address_info.ZipCode = request.form.get('zipcode', address_info.ZipCode if address_info else None)
        
        if not student.address_info:
            db.session.add(address_info)
            student.address_info = address_info

        # Update emergency contact information
        emergency_contact = student.emergency_contact or Emergency_Contact(StudentID=student_id)
        emergency_contact.FirstName = request.form.get('emergencyFirstName', emergency_contact.FirstName if emergency_contact else None)
        emergency_contact.MiddleName = request.form.get('emergencyMiddleName', emergency_contact.MiddleName if emergency_contact else None)
        emergency_contact.LastName = request.form.get('emergencyLastName', emergency_contact.LastName if emergency_contact else None)
        emergency_contact.Relationship = request.form.get('emergencyRelationship', emergency_contact.Relationship if emergency_contact else None)
        emergency_contact.ContactPhone = request.form.get('emergencyContactPhone', emergency_contact.ContactPhone if emergency_contact else None)
        
        if not student.emergency_contact:
            db.session.add(emergency_contact)
            student.emergency_contact = emergency_contact

        db.session.commit()

        # Update student in StudentService database
        student_data = {
            'StudentID': student_id,
            'FirstName': student.FirstName,
            'MiddleName': student.MiddleName,
            'LastName': student.LastName,
            'DateOfBirth': student.DateOfBirth.strftime('%Y-%m-%d') if student.DateOfBirth else None,
            'Gender': student.Gender.value if student.Gender else None,
            'Citizenship': student.Citizenship,
            'Contact': student.Contact,
            'Email': student.Email,
            'Address': student.Address,
            'PassportNumber': student.PassportNumber,
            'VisaStatus': student.VisaStatus,
            'VisaExpiryDate': student.VisaExpiryDate.strftime('%Y-%m-%d') if student.VisaExpiryDate else None,
            'Province': address_info.Province,
            'Country': address_info.Country,
            'ZipCode': address_info.ZipCode,
            'EmergencyContact': {
                'FirstName': emergency_contact.FirstName,
                'MiddleName': emergency_contact.MiddleName,
                'LastName': emergency_contact.LastName,
                'Relationship': emergency_contact.Relationship,
                'ContactPhone': emergency_contact.ContactPhone
            }
        }
        
        update_student_in_service_db(student_data)

        return jsonify({'status': 'success', 'message': 'Student details updated successfully'})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating student: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Error updating student: {str(e)}'}), 500

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
    conn = None
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

        # Begin transaction
        conn.execute('BEGIN TRANSACTION')

        # Create Student table if it doesn't exist
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

        # Create Addressing_Student table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Addressing_Student (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                StudentID VARCHAR(20) NOT NULL,
                Province VARCHAR(100) NOT NULL,
                Country VARCHAR(100) NOT NULL,
                ZipCode VARCHAR(20),
                FOREIGN KEY (StudentID) REFERENCES Student(StudentID) ON DELETE CASCADE
            )
        """)

        # Create document tables if they don't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS BirthCertificate (
                DocumentID INTEGER PRIMARY KEY AUTOINCREMENT,
                StudentID VARCHAR(50) REFERENCES Student(StudentID) ON DELETE CASCADE,
                FileName VARCHAR(255) NOT NULL,
                FilePath VARCHAR(512) NOT NULL,
                UploadDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                VerificationStatus VARCHAR(20) DEFAULT 'Pending'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ValidID (
                DocumentID INTEGER PRIMARY KEY AUTOINCREMENT,
                StudentID VARCHAR(50) REFERENCES Student(StudentID) ON DELETE CASCADE,
                FileName VARCHAR(255) NOT NULL,
                FilePath VARCHAR(512) NOT NULL,
                UploadDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                VerificationStatus VARCHAR(20) DEFAULT 'Pending',
                IDType VARCHAR(50) NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS AcademicTranscript (
                DocumentID INTEGER PRIMARY KEY AUTOINCREMENT,
                StudentID VARCHAR(50) REFERENCES Student(StudentID) ON DELETE CASCADE,
                FileName VARCHAR(255) NOT NULL,
                FilePath VARCHAR(512) NOT NULL,
                UploadDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                VerificationStatus VARCHAR(20) DEFAULT 'Pending',
                YearLevel VARCHAR(20) NOT NULL
            )
        """)

        # Insert student data
        cursor.execute("""
            INSERT INTO Student (
                StudentID, FirstName, MiddleName, LastName, Contact, Email,
                DateOfBirth, Gender, Citizenship, Address, PasswordHash,
                CampusID, PassportNumber, VisaStatus, VisaExpiryDate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student_data['StudentID'],
            student_data['FirstName'],
            student_data['MiddleName'],
            student_data['LastName'],
            student_data['Contact'],
            student_data['Email'],
            student_data['DateOfBirth'].isoformat() if student_data['DateOfBirth'] else None,
            student_data['Gender'].value if student_data['Gender'] else None,
            student_data['Citizenship'],
            student_data['Address'],
            student_data['PasswordHash'],
            student_data['CampusID'],
            student_data['PassportNumber'],
            student_data['VisaStatus'],
            student_data['VisaExpiryDate'].isoformat() if student_data['VisaExpiryDate'] else None
        ))

        # Insert address data
        cursor.execute("""
            INSERT INTO Addressing_Student (StudentID, Province, Country, ZipCode)
            VALUES (?, ?, ?, ?)
        """, (
            student_data['StudentID'],
            student_data['Province'],
            student_data['Country'],
            student_data['ZipCode']
        ))

        # Insert document data if provided
        if 'birth_certificate' in student_data:
            cursor.execute("""
                INSERT INTO BirthCertificate (StudentID, FileName, FilePath, VerificationStatus)
                VALUES (?, ?, ?, ?)
            """, (
                student_data['StudentID'],
                student_data['birth_certificate']['filename'],
                student_data['birth_certificate']['file_path'],
                'Verified' if student_data['birth_certificate']['verified'] else 'Pending'
            ))

        if 'valid_id' in student_data:
            cursor.execute("""
                INSERT INTO ValidID (StudentID, FileName, FilePath, VerificationStatus, IDType)
                VALUES (?, ?, ?, ?, ?)
            """, (
                student_data['StudentID'],
                student_data['valid_id']['filename'],
                student_data['valid_id']['file_path'],
                'Verified' if student_data['valid_id']['verified'] else 'Pending',
                student_data['valid_id']['id_type']
            ))

        if 'academic_transcript' in student_data:
            cursor.execute("""
                INSERT INTO AcademicTranscript (StudentID, FileName, FilePath, VerificationStatus, YearLevel)
                VALUES (?, ?, ?, ?, ?)
            """, (
                student_data['StudentID'],
                student_data['academic_transcript']['filename'],
                student_data['academic_transcript']['file_path'],
                'Verified' if student_data['academic_transcript']['verified'] else 'Pending',
                student_data['academic_transcript']['year_level']
            ))

        # Commit transaction
        conn.commit()
        app.logger.info(f"Registered student {student_data['StudentID']} in StudentService database")

    except Exception as e:
        if conn:
            conn.rollback()
        app.logger.error(f"Error registering student in StudentService database: {e}")
        raise
    finally:
        if conn:
            conn.close()

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

def allowed_file(filename, doc_type):
    """Check if the file extension is allowed for the document type and size is within limits."""
    if '.' not in filename:
        return False
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in ALLOWED_EXTENSIONS[doc_type]

def validate_file_size(file):
    """Validate that the file size is within the allowed limit."""
    file.seek(0, 2)  # Seek to end of file
    size = file.tell()  # Get current position (file size)
    file.seek(0)  # Reset file pointer to beginning
    return size <= MAX_FILE_SIZE

@app.route('/sas-staff/upload-document/<student_id>', methods=['POST'])
@login_required
@role_required('sas_staff')
def upload_document(student_id):
    try:
        app.logger.info(f"Starting document upload for student {student_id}")
        app.logger.debug(f"Request files: {request.files}")
        app.logger.debug(f"Request form data: {request.form}")
        
        student = Student.query.get_or_404(student_id)
        
        # Check if any files were uploaded
        if not request.files:
            app.logger.error("No files found in request")
            return jsonify({'status': 'error', 'message': 'No files uploaded'}), 400

        # Create upload folder for student if it doesn't exist
        student_folder = os.path.join(UPLOAD_FOLDER, str(student_id))
        os.makedirs(student_folder, exist_ok=True)
        app.logger.info(f"Created/verified student folder at {student_folder}")

        # Process each document type
        if 'birth_certificate' in request.files:
            file = request.files['birth_certificate']
            app.logger.info(f"Processing birth certificate: {file.filename}")
            
            if file and file.filename:
                if not allowed_file(file.filename, 'birth_certificate'):
                    app.logger.error(f"Invalid file type for birth certificate: {file.filename}")
                    return jsonify({'status': 'error', 'message': 'Invalid file type for birth certificate'}), 400
                
                if not validate_file_size(file):
                    app.logger.error(f"File size exceeds limit for birth certificate: {file.filename}")
                    return jsonify({'status': 'error', 'message': 'Birth certificate file size exceeds 5MB limit'}), 400

                # Create document folder
                doc_folder = os.path.join(student_folder, 'birth_certificate')
                os.makedirs(doc_folder, exist_ok=True)

                # Save file
                filename = secure_filename(file.filename)
                file_path = os.path.join(doc_folder, filename)
                file.save(file_path)
                app.logger.info(f"Saved birth certificate to {file_path}")

                # Remove existing birth certificate if any
                existing_doc = BirthCertificate.query.filter_by(student_id=student_id).first()
                if existing_doc:
                    if os.path.exists(existing_doc.file_path):
                        os.remove(existing_doc.file_path)
                    db.session.delete(existing_doc)
                    app.logger.info("Removed existing birth certificate")

                # Create new document
                new_doc = BirthCertificate(
                    student_id=student_id,
                    filename=filename,
                    file_path=file_path,
                    verified=False
                )
                db.session.add(new_doc)
                app.logger.info("Added new birth certificate to database")

        if 'valid_id' in request.files:
            file = request.files['valid_id']
            id_type = request.form.get('id_type')
            app.logger.info(f"Processing valid ID: {file.filename}, type: {id_type}")
            
            if not id_type:
                app.logger.error("ID type not provided")
                return jsonify({'status': 'error', 'message': 'ID type is required'}), 400

            if file and file.filename:
                if not allowed_file(file.filename, 'valid_id'):
                    app.logger.error(f"Invalid file type for valid ID: {file.filename}")
                    return jsonify({'status': 'error', 'message': 'Invalid file type for valid ID'}), 400

                if not validate_file_size(file):
                    app.logger.error(f"File size exceeds limit for valid ID: {file.filename}")
                    return jsonify({'status': 'error', 'message': 'Valid ID file size exceeds 5MB limit'}), 400

                # Create document folder
                doc_folder = os.path.join(student_folder, 'valid_id')
                os.makedirs(doc_folder, exist_ok=True)

                # Save file
                filename = secure_filename(file.filename)
                file_path = os.path.join(doc_folder, filename)
                file.save(file_path)
                app.logger.info(f"Saved valid ID to {file_path}")

                # Remove existing valid ID if any
                existing_doc = ValidID.query.filter_by(student_id=student_id).first()
                if existing_doc:
                    if os.path.exists(existing_doc.file_path):
                        os.remove(existing_doc.file_path)
                    db.session.delete(existing_doc)
                    app.logger.info("Removed existing valid ID")

                # Create new document
                new_doc = ValidID(
                    student_id=student_id,
                    filename=filename,
                    file_path=file_path,
                    id_type=id_type,
                    verified=False
                )
                db.session.add(new_doc)
                app.logger.info("Added new valid ID to database")

        if 'academic_transcript' in request.files:
            file = request.files['academic_transcript']
            transcript_type = request.form.get('transcript_type')
            app.logger.info(f"Processing academic transcript: {file.filename}, type: {transcript_type}")
            
            if not transcript_type:
                app.logger.error("Transcript type not provided")
                return jsonify({'status': 'error', 'message': 'Transcript type is required'}), 400

            if file and file.filename:
                if not allowed_file(file.filename, 'academic_transcript'):
                    app.logger.error(f"Invalid file type for academic transcript: {file.filename}")
                    return jsonify({'status': 'error', 'message': 'Invalid file type for academic transcript'}), 400

                if not validate_file_size(file):
                    app.logger.error(f"File size exceeds limit for academic transcript: {file.filename}")
                    return jsonify({'status': 'error', 'message': 'Academic transcript file size exceeds 5MB limit'}), 400

                # Create document folder
                doc_folder = os.path.join(student_folder, 'academic_transcript')
                os.makedirs(doc_folder, exist_ok=True)

                # Save file
                filename = secure_filename(file.filename)
                file_path = os.path.join(doc_folder, filename)
                file.save(file_path)
                app.logger.info(f"Saved academic transcript to {file_path}")

                # Remove existing transcript if any
                existing_doc = AcademicTranscript.query.filter_by(student_id=student_id).first()
                if existing_doc:
                    if os.path.exists(existing_doc.file_path):
                        os.remove(existing_doc.file_path)
                    db.session.delete(existing_doc)
                    app.logger.info("Removed existing academic transcript")

                # Create new document
                new_doc = AcademicTranscript(
                    student_id=student_id,
                    filename=filename,
                    file_path=file_path,
                    year_level=transcript_type,
                    verified=False
                )
                db.session.add(new_doc)
                app.logger.info("Added new academic transcript to database")

        # Commit changes to database
        try:
            db.session.commit()
            app.logger.info("Successfully committed changes to enrollment database")
        except Exception as e:
            app.logger.error(f"Error committing to enrollment database: {str(e)}")
            db.session.rollback()
            raise

        # Update documents in StudentService database
        try:
            update_student_documents_in_service_db(student_id)
            app.logger.info("Successfully synchronized documents with StudentService database")
        except Exception as e:
            app.logger.error(f"Error synchronizing with StudentService database: {str(e)}")
            raise

        return jsonify({'status': 'success', 'message': 'Documents uploaded successfully'})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error uploading documents: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': f'Error uploading documents: {str(e)}'}), 500

def update_student_documents_in_service_db(student_id):
    """
    Update student documents in the StudentService database.
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

        # Create tables if they don't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS BirthCertificate (
                DocumentID INTEGER PRIMARY KEY AUTOINCREMENT,
                StudentID VARCHAR(50) REFERENCES Student(StudentID) ON DELETE CASCADE,
                FileName VARCHAR(255) NOT NULL,
                FilePath VARCHAR(512) NOT NULL,
                UploadDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                VerificationStatus VARCHAR(20) DEFAULT 'Pending'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ValidID (
                DocumentID INTEGER PRIMARY KEY AUTOINCREMENT,
                StudentID VARCHAR(50) REFERENCES Student(StudentID) ON DELETE CASCADE,
                FileName VARCHAR(255) NOT NULL,
                FilePath VARCHAR(512) NOT NULL,
                UploadDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                VerificationStatus VARCHAR(20) DEFAULT 'Pending',
                IDType VARCHAR(50) NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS AcademicTranscript (
                DocumentID INTEGER PRIMARY KEY AUTOINCREMENT,
                StudentID VARCHAR(50) REFERENCES Student(StudentID) ON DELETE CASCADE,
                FileName VARCHAR(255) NOT NULL,
                FilePath VARCHAR(512) NOT NULL,
                UploadDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                VerificationStatus VARCHAR(20) DEFAULT 'Pending',
                TranscriptType VARCHAR(20) NOT NULL
            )
        """)

        # First, delete all existing documents for this student
        cursor.execute("DELETE FROM BirthCertificate WHERE StudentID = ?", (student_id,))
        cursor.execute("DELETE FROM ValidID WHERE StudentID = ?", (student_id,))
        cursor.execute("DELETE FROM AcademicTranscript WHERE StudentID = ?", (student_id,))

        # Get documents from enrollment database
        birth_cert = BirthCertificate.query.filter_by(student_id=student_id).first()
        valid_id = ValidID.query.filter_by(student_id=student_id).first()
        transcript = AcademicTranscript.query.filter_by(student_id=student_id).first()

        # Update birth certificate
        if birth_cert:
            # Convert file path to be relative to StudentService
            relative_path = os.path.relpath(birth_cert.file_path, start=os.path.dirname(os.path.dirname(__file__)))
            service_file_path = os.path.join(os.path.dirname(student_service_db_path), relative_path)
            
            cursor.execute("""
                INSERT INTO BirthCertificate (
                    StudentID, FileName, FilePath, VerificationStatus
                ) VALUES (?, ?, ?, ?)
            """, (student_id, birth_cert.filename, service_file_path, 'Verified' if birth_cert.verified else 'Pending'))

        # Update valid ID
        if valid_id:
            # Convert file path to be relative to StudentService
            relative_path = os.path.relpath(valid_id.file_path, start=os.path.dirname(os.path.dirname(__file__)))
            service_file_path = os.path.join(os.path.dirname(student_service_db_path), relative_path)
            
            cursor.execute("""
                INSERT INTO ValidID (
                    StudentID, FileName, FilePath, VerificationStatus, IDType
                ) VALUES (?, ?, ?, ?, ?)
            """, (student_id, valid_id.filename, service_file_path, 'Verified' if valid_id.verified else 'Pending', valid_id.id_type))

        # Update academic transcript
        if transcript:
            # Convert file path to be relative to StudentService
            relative_path = os.path.relpath(transcript.file_path, start=os.path.dirname(os.path.dirname(__file__)))
            service_file_path = os.path.join(os.path.dirname(student_service_db_path), relative_path)
            
            cursor.execute("""
                INSERT INTO AcademicTranscript (
                    StudentID, FileName, FilePath, VerificationStatus, TranscriptType
                ) VALUES (?, ?, ?, ?, ?)
            """, (student_id, transcript.filename, service_file_path, 'Verified' if transcript.verified else 'Pending', transcript.year_level))

        conn.commit()
        conn.close()

        app.logger.info(f"Successfully synchronized documents for student {student_id} between databases")

    except Exception as e:
        app.logger.error(f"Error updating documents in StudentService database: {str(e)}")
        raise

@app.route('/sas-staff/verify-document/<doc_type>/<int:doc_id>', methods=['POST'])
@login_required
@role_required('sas_staff')
def verify_document(doc_type, doc_id):
    try:
        # Map document type to model
        model_map = {
            'birth_certificate': BirthCertificate,
            'valid_id': ValidID,
            'academic_transcript': AcademicTranscript
        }

        if doc_type not in model_map:
            return jsonify({'status': 'error', 'message': 'Invalid document type'}), 400

        # Get document
        document = model_map[doc_type].query.get_or_404(doc_id)
        
        # Update verification status
        document.verified = True
        db.session.commit()

        # Update document in StudentService database
        update_student_documents_in_service_db(document.student_id)

        return jsonify({'status': 'success', 'message': 'Document verified successfully'})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error verifying document: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Error verifying document: {str(e)}'}), 500

@app.route('/sas-staff/remove-document/<doc_type>/<student_id>', methods=['POST'])
@login_required
@role_required('sas_staff')
def remove_document(doc_type, student_id):
    try:
        # Map document type to model
        model_map = {
            'birth_certificate': BirthCertificate,
            'valid_id': ValidID,
            'academic_transcript': AcademicTranscript
        }

        if doc_type not in model_map:
            return jsonify({'status': 'error', 'message': 'Invalid document type'}), 400

        # Get document
        document = model_map[doc_type].query.filter_by(student_id=student_id).first()
        if not document:
            return jsonify({'status': 'error', 'message': 'Document not found'}), 404

        # Remove file
        if os.path.exists(document.file_path):
            os.remove(document.file_path)

        # Remove from database
        db.session.delete(document)
        db.session.commit()

        # Update document in StudentService database
        update_student_documents_in_service_db(student_id)

        return jsonify({'status': 'success', 'message': 'Document removed successfully'})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error removing document: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Error removing document: {str(e)}'}), 500

@app.route('/sas-staff/view-document/<doc_type>/<int:doc_id>')
@login_required
@role_required('sas_staff')
def view_document(doc_type, doc_id):
    try:
        # Map document type to model
        model_map = {
            'birth_certificate': BirthCertificate,
            'valid_id': ValidID,
            'academic_transcript': AcademicTranscript
        }

        if doc_type not in model_map:
            return jsonify({'status': 'error', 'message': 'Invalid document type'}), 400

        # Get document
        document = model_map[doc_type].query.get_or_404(doc_id)
        
        # Check if file exists
        if not os.path.exists(document.file_path):
            return jsonify({'status': 'error', 'message': 'Document file not found'}), 404

        # Get file extension
        file_ext = os.path.splitext(document.filename)[1].lower()
        
        # Set content type based on file extension
        content_type = 'application/pdf' if file_ext == '.pdf' else \
                      'application/vnd.openxmlformats-officedocument.wordprocessingml.document' if file_ext == '.docx' else \
                      'image/jpeg' if file_ext in ['.jpg', '.jpeg'] else \
                      'image/png' if file_ext == '.png' else \
                      'application/octet-stream'

        return send_file(
            document.file_path,
            mimetype=content_type,
            as_attachment=False,
            download_name=document.filename
        )

    except Exception as e:
        app.logger.error(f"Error serving document: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Error serving document: {str(e)}'}), 500

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