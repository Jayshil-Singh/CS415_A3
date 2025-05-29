# enrollment_services/routes.py
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session, send_file, make_response
import logging
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import datetime
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.orm import joinedload
import jwt
from functools import wraps
from flask import current_app
import uuid

# Import db and models from your package.
from .db import db
from .model import (
    Program, SubProgram, Semester, Course, CourseAvailability,
    Student, StudentLevel, Hold,
    Enrollment, CourseFee, StudentCourseFee,
    User
)

# --- Blueprint Initialization ---
enrollment_bp = Blueprint('enrollment', __name__, template_folder='templates')

# --- Logging Setup ---
logging.basicConfig(level=logging.ERROR)

# --- Mock Data (IMPORTANT: To be Replaced with Actual Database Interactions) ---
student_details = {
    'name': 'Ratu Epeli Nailatikau',
    'id': 's11223344'
}
invoice_details = {
    'number': 'INV-2025-1234',
    'date': 'May 21, 2025',
    'semester': 'Semester 2, 2025',
    'payment_status': 'Paid'
}

# --- Define Program Structure and Prerequisites (NEW LOGIC) ---
# This dictionary defines the program structure and hardcoded prerequisites
# Semester names here are the full names used in the dropdown and CourseAvailability model
PROGRAM_STRUCTURE = {
    'Year 1': {
        'Semester 1': [
            {'code': 'CS111', 'title': 'Introduction to Programming', 'units': 1.0, 'prereq': None},
            {'code': 'ST131', 'title': 'Statistics for Science', 'units': 1.0, 'prereq': None},
            {'code': 'UU114', 'title': 'English for Academic Purposes', 'units': 1.0, 'prereq': None},
            {'code': 'MA111', 'title': 'Calculus I', 'units': 1.0, 'prereq': None},
            {'code': 'UU100A', 'title': 'Communications and Information Literacy', 'units': 0.5, 'prereq': None},
            {'code': 'MG101', 'title': 'Introduction to Management', 'units': 1.0, 'prereq': None},
        ],
        'Semester 2': [
            {'code': 'CS111', 'title': 'Introduction to Programming (Repeat)', 'units': 1.0, 'prereq': None},
            {'code': 'CS112', 'title': 'Data Structures and Algorithms', 'units': 1.0, 'prereq': 'CS111'},
            {'code': 'UU114', 'title': 'English for Academic Purposes (Repeat)', 'units': 1.0, 'prereq': None},
            {'code': 'MG101', 'title': 'Introduction to Management (Repeat)', 'units': 1.0, 'prereq': None},
            {'code': 'UU100A', 'title': 'Communications and Information Literacy (Repeat)', 'units': 0.5, 'prereq': None},
            {'code': 'MA161', 'title': 'Discrete Mathematics', 'units': 1.0, 'prereq': None},
            {'code': 'CS140', 'title': 'Introduction to Web Development', 'units': 1.0, 'prereq': None},
        ]
    },
    'Year 2': {
        'Semester 1': [
            {'code': 'CS211', 'title': 'Object-Oriented Programming', 'units': 1.0, 'prereq': None},
            {'code': 'CS230', 'title': 'Operating Systems', 'units': 1.0, 'prereq': None},
            {'code': 'IS221', 'title': 'Database Management Systems', 'units': 1.0, 'prereq': None},
            {'code': 'IS222', 'title': 'Systems Analysis and Design', 'units': 1.0, 'prereq': None},
            {'code': 'UU200', 'title': 'Ethics and Governance', 'units': 1.0, 'prereq': None},
            {'code': 'CS001', 'title': 'Industrial Attachment (Part 1)', 'units': 0.5, 'prereq': None},
        ],
        'Semester 2': [
            {'code': 'CS241', 'title': 'Computer Networks', 'units': 1.0, 'prereq': None},
            {'code': 'CS218', 'title': 'Software Engineering', 'units': 1.0, 'prereq': None},
            {'code': 'CS219', 'title': 'Web Application Development', 'units': 1.0, 'prereq': None},
            {'code': 'CS214', 'title': 'Artificial Intelligence', 'units': 1.0, 'prereq': None},
            {'code': 'UU200', 'title': 'Ethics and Governance (Repeat)', 'units': 1.0, 'prereq': None},
            {'code': 'CS001', 'title': 'Industrial Attachment (Part 1) (Repeat)', 'units': 0.5, 'prereq': None},
        ]
    },
    'Year 3': {
        'Semester 1': [
            {'code': 'CS310', 'title': 'Advanced Algorithms', 'units': 1.0, 'prereq': None},
            {'code': 'CS311', 'title': 'Compiler Design', 'units': 1.0, 'prereq': None},
            {'code': 'CS352', 'title': 'Computer Graphics', 'units': 1.0, 'prereq': None},
            {'code': 'IS333', 'title': 'Information Security', 'units': 1.0, 'prereq': None},
            {'code': 'CS001', 'title': 'Industrial Attachment (Part 1) (Repeat)', 'units': 0.5, 'prereq': None},
        ],
        'Semester 2': [
            {'code': 'CS324', 'title': 'Distributed Systems', 'units': 1.0, 'prereq': None},
            {'code': 'CS341', 'title': 'Mobile Application Development', 'units': 1.0, 'prereq': None},
            {'code': 'IS314', 'title': 'E-Commerce Systems', 'units': 1.0, 'prereq': None},
            {'code': 'IS328', 'title': 'Project Management', 'units': 1.0, 'prereq': None},
            {'code': 'CS001', 'title': 'Industrial Attachment (Part 1) (Repeat)', 'units': 0.5, 'prereq': None},
        ]
    },
    'Year 4': {
        'Semester 1': [
            {'code': 'CS415', 'title': 'Advanced Software Engineering', 'units': 1.0, 'prereq': None},
            {'code': 'CS412', 'title': 'Capstone Project I', 'units': 1.0, 'prereq': None},
            {'code': 'CS403', 'title': 'Cloud Computing', 'units': 1.0, 'prereq': None},
            {'code': 'CS001', 'title': 'Industrial Attachment (Part 1) (Repeat)', 'units': 0.5, 'prereq': None},
        ],
        'Semester 2': [
            {'code': 'CS400', 'title': 'Industrial Attachment (Part 2)', 'units': 1.0, 'prereq': None},
            {'code': 'CS412', 'title': 'Capstone Project II', 'units': 1.0, 'prereq': 'CS412'}, # Prereq for Capstone II is Capstone I
            {'code': 'CS424', 'title': 'Machine Learning', 'units': 1.0, 'prereq': None},
        ]
    }
}

# Helper to get all course codes for a specific year (excluding repeats for completion check)
def get_unique_course_codes_for_year(year_data):
    unique_codes = set()
    for semester_name, courses in year_data.items():
        for course in courses:
            # For year completion, we only care if a course was taken once, not if it's a repeat offering
            # We'll use the base code for uniqueness (e.g., 'CS111' regardless of 'Repeat')
            base_code = course['code'].split('(')[0].strip()
            unique_codes.add(base_code)
    return unique_codes

# --- Helper Functions for Data Processing and Serialization ---

def calculate_invoice(enrolled_courses_codes):
    """Calculates the invoice details for the given course codes."""
    invoice_items = []
    total_amount = 0
    # Instead of querying Course model, use the PROGRAM_STRUCTURE for mock fees
    # In a real app, you'd still query CourseFee or a similar model for actual fees.
    
    # Flatten PROGRAM_STRUCTURE to easily look up course details
    all_program_courses = {}
    for year_data in PROGRAM_STRUCTURE.values():
        for semester_data in year_data.values():
            for course_info in semester_data:
                all_program_courses[course_info['code']] = course_info

    for course_code in enrolled_courses_codes:
        course_info = all_program_courses.get(course_code)
        if course_info:
            # Assuming a default fee structure for calculation or linking to CourseFee if available
            course_fee_amount = 0.0
            # Try to fetch from CourseFee if it exists, otherwise use a placeholder
            db_course_fee = CourseFee.query.filter_by(CourseID=course_code).first()
            if db_course_fee:
                course_fee_amount = float(db_course_fee.amount)
            else:
                # Use a default fee per unit if not explicitly found in DB
                course_fee_amount = course_info['units'] * 100.00 # Example: $100 per unit

            subtotal = course_fee_amount
            invoice_items.append({
                'code': course_info['code'],
                'title': course_info['title'],
                'credits': course_info['units'], # Use units as credits for display
                'fee_per_credit': course_fee_amount, # This label might be misleading if it's total fee
                'subtotal': subtotal
            })
            total_amount += subtotal
    return invoice_items, total_amount


# Serialization functions (to convert SQLAlchemy models to dictionaries for JSON response)
def serialize_program(program):
    return {
        "ProgramID": program.ProgramID,
        "ProgramName": program.ProgramName,
        "SubProgramID": program.SubProgramID if hasattr(program, 'SubProgramID') else None
    }

def serialize_subprogram(subprogram):
    return {
        "SubProgramID": subprogram.SubProgramID,
        "SubProgramName": subprogram.SubProgramName,
        "SubProgramType": subprogram.SubProgramType,
        "ProgramID": subprogram.ProgramID
    }

def serialize_semester(semester):
    return {
        "SemesterID": semester.SemesterID,
        "SemesterName": semester.SemesterName
    }
# enrollment_services/routes.py (continued from Part 1)

# --- Serialization Functions for API Responses (continued) ---

def serialize_course(course):
    return {
        "CourseID": course.CourseID,
        "SubProgramID": course.SubProgramID,
        "CourseName": course.CourseName,
        "PrerequisiteCourseID": course.PrerequisiteCourseID,
        "SubProgramName": course.subprogram.SubProgramName if course.subprogram else None,
        "CourseAvailabilities": [
            {
                "CourseAvailabilityID": ca.CourseAvailabilityID,
                "SemesterID": ca.SemesterID,
                "SemesterName": ca.semester.SemesterName if ca.semester else None,
                "isAvailable": ca.isAvailable
            } for ca in course.course_availabilities
        ]
    }

def serialize_enrollment(enrollment):
    return {
        "EnrollmentID": enrollment.EnrollmentID,
        "EnrollmentDate": enrollment.EnrollmentDate.isoformat() if enrollment.EnrollmentDate else None,
        "StudentID": enrollment.StudentID,
        "StudentName": f"{enrollment.student.FirstName} {enrollment.student.LastName}" if enrollment.student else None,
        "CourseID": enrollment.CourseID,
        "CourseName": enrollment.course.CourseName if enrollment.course else None
    }

def serialize_course_fee(fee):
    return {
        "FeeID": fee.FeeID,
        "amount": fee.amount,
        "description": fee.description,
        "CourseID": fee.CourseID,
        "CourseName": fee.course.CourseName if fee.course else None
    }

def serialize_student_course_fee(scf):
    return {
        "StudentCourseFeeID": scf.StudentCourseFeeID,
        "due_date": scf.due_date.isoformat() if scf.due_date else None,
        "paid_date": scf.paid_date.isoformat() if scf.paid_date else None,
        "status": scf.status,
        "StudentID": scf.StudentID,
        "StudentName": f"{scf.student.FirstName} {scf.student.LastName}" if scf.student else None,
        "CourseID": scf.CourseID,
        "CourseName": scf.course.CourseName if scf.course else None,
        "FeeID": scf.FeeID,
        "FeeAmount": scf.course_fee.amount if scf.course_fee else None,
        "FeeDescription": scf.course_fee.description if scf.course_fee else None,
    }

def serialize_student(student):
    return {
        "StudentID": student.StudentID,
        "FirstName": student.FirstName,
        "LastName": student.LastName,
        "MiddleName": student.MiddleName,
        "DateOfBirth": student.DateOfBirth.isoformat() if student.DateOfBirth else None,
        "Gender": student.Gender,
        "Address": student.Address,
        "Contact": student.Contact,
        "Citizenship": student.Citizenship,
        "CampusID": student.CampusID,
        "ProgramID": student.ProgramID,
        "SubProgramID": student.SubProgramID,
        "StudentLevelID": student.StudentLevelID,
        "CreatedAt": student.CreatedAt.isoformat() if student.CreatedAt else None,
        "Email": student.Email,
        "ProgramName": student.program_obj.ProgramName if student.program_obj else None,
        "SubProgramName": student.subprogram_obj.SubProgramName if student.subprogram_obj else None,
        "StudentLevelName": student.student_levels_records[0].LevelName if student.student_levels_records else None,
    }

def serialize_student_level(student_level):
    return {
        "StudentLevelID": student_level.StudentLevelID,
        "LevelName": student_level.LevelName,
        "AttributeName1": student_level.AttributeName1,
        "AttributeName2": student_level.AttributeName2,
        "StudentID": student_level.StudentID,
        "StudentName": f"{student_level.student.FirstName} {student_level.student.LastName}" if student_level.student else None
    }

def serialize_hold(hold):
    return {
        "HoldID": hold.HoldID,
        "reason": hold.reason,
        "holdDate": hold.holdDate.isoformat() if hold.holdDate else None,
        "liftDate": hold.liftDate.isoformat() if hold.liftDate else None,
        "status": hold.status,
        "StudentID": hold.StudentID,
        "StudentName": f"{hold.student.FirstName} {hold.student.LastName}" if hold.student else None
    }

# --- Authentication Decorator and Endpoints ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'jwt_token' in session:
            token = session['jwt_token']
        elif 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if len(auth_header.split(" ")) == 2 and auth_header.split(" ")[0].lower() == 'bearer':
                token = auth_header.split(" ")[1]

        if not token:
            if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
                flash("Authentication required to access this page.", "error")
                return redirect(url_for('login_page'))
            else:
                return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
                    flash("Invalid user associated with token. Please log in again.", "error")
                    return redirect(url_for('login_page'))
                else:
                    return jsonify({'message': 'User not found!'}), 401

        except jwt.ExpiredSignatureError:
            if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
                flash("Your session has expired. Please log in again.", "error")
                return redirect(url_for('login_page'))
            else:
                return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
                flash("Invalid authentication token. Please log in again.", "error")
                return redirect(url_for('login_page'))
            else:
                return jsonify({'message': 'Token is invalid!'}), 401
        except Exception as e:
            logging.error(f"Token verification error: {e}")
            if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
                flash("Authentication error. Please log in again.", "error")
                return redirect(url_for('login_page'))
            else:
                return jsonify({'message': 'Token verification failed: ' + str(e)}), 401

        return f(current_user, *args, **kwargs)

    return decorated

@enrollment_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    if not data or not 'username' in data or not 'password' in data:
        return jsonify({'message': 'Missing username or password'}), 400

    user = User.query.filter_by(username=data['username']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401

    token_payload = {
        'user_id': user.id,
        'username': user.username,
        'role': user.role,
        'exp': datetime.utcnow() + current_app.config['JWT_EXPIRATION_DELTA']
    }
    token = jwt.encode(token_payload, current_app.config['JWT_SECRET_KEY'], algorithm="HS256")

    session['jwt_token'] = token

    return jsonify({'message': 'Login successful', 'token': token, 'user': {'id': user.id, 'username': user.username, 'role': user.role}}), 200

@enrollment_bp.route('/auth/verify_token', methods=['GET'])
@token_required
def verify_token(current_user):
    return jsonify({
        'message': 'Token is valid',
        'user_id': current_user.id,
        'username': current_user.username,
        'role': current_user.role
    }), 200

@enrollment_bp.route('/auth/set_session_token', methods=['POST'])
def set_session_token():
    data = request.json
    token = data.get('token')

    if token:
        session['jwt_token'] = token
        return jsonify({'message': 'Token set in session successfully'}), 200
    else:
        return jsonify({'message': 'No token provided'}), 400

# --- Frontend-facing Routes (HTML Rendering) ---

@enrollment_bp.route('/')
@enrollment_bp.route('/dashboard')
@token_required
def dashboard(current_user):
    return render_template('dashboard.html')


@enrollment_bp.route('/enroll', methods=['GET', 'POST'])
@token_required
def enroll(current_user):
    try:
        # Get courses the student is already enrolled in
        current_enrollments = Enrollment.query.filter_by(StudentID=current_user.id).all()
        # Use a set for faster lookup of enrolled courses
        currently_enrolled_course_codes = {e.CourseID for e in current_enrollments}

        # Simulate "completed courses" from current enrollments.
        # In a real system, this would come from a StudentAcademicRecord or similar.
        # Ensure that base codes are considered for prerequisite fulfillment (e.g., CS111 vs CS111 (Repeat))
        all_met_courses_for_prereq_check = set()
        for course_code in currently_enrolled_course_codes:
            all_met_courses_for_prereq_check.add(course_code.split('(')[0].strip())


        # Determine which years the student has completed
        completed_years = set()
        years_list = list(PROGRAM_STRUCTURE.keys())

        # Check Year 1 completion
        year_1_unique_courses = get_unique_course_codes_for_year(PROGRAM_STRUCTURE['Year 1'])
        if year_1_unique_courses.issubset(all_met_courses_for_prereq_check):
            completed_years.add('Year 1')

        # Check Year 2 completion (if Year 1 is completed)
        if 'Year 1' in completed_years:
            year_2_unique_courses = get_unique_course_codes_for_year(PROGRAM_STRUCTURE['Year 2'])
            if year_2_unique_courses.issubset(all_met_courses_for_prereq_check):
                completed_years.add('Year 2')

        # Check Year 3 completion (if Year 2 is completed)
        if 'Year 2' in completed_years:
            year_3_unique_courses = get_unique_course_codes_for_year(PROGRAM_STRUCTURE['Year 3'])
            if year_3_unique_courses.issubset(all_met_courses_for_prereq_check):
                completed_years.add('Year 3')
        
        # Check Year 4 completion (if Year 3 is completed) - Not strictly needed for enrollment but for completeness
        if 'Year 3' in completed_years:
            year_4_unique_courses = get_unique_course_codes_for_year(PROGRAM_STRUCTURE['Year 4'])
            if year_4_unique_courses.issubset(all_met_courses_for_prereq_check):
                completed_years.add('Year 4')

        # Prepare courses data for the template based on PROGRAM_STRUCTURE
        courses_for_template = []
        for year_name, year_data in PROGRAM_STRUCTURE.items():
            year_unlocked = True
            if year_name == 'Year 2' and 'Year 1' not in completed_years:
                year_unlocked = False
            elif year_name == 'Year 3' and 'Year 2' not in completed_years:
                year_unlocked = False
            elif year_name == 'Year 4' and 'Year 3' not in completed_years:
                year_unlocked = False

            for semester_name, semester_courses in year_data.items():
                for course_info in semester_courses:
                    course_code = course_info['code']
                    base_course_code = course_code.split('(')[0].strip() # Get base code for prereq check

                    prereq_met = True
                    prereq_display_name = None

                    # Check individual course prerequisite
                    if course_info['prereq']:
                        prereq_course_code = course_info['prereq']
                        prereq_course_obj = Course.query.get(prereq_course_code) # Look up actual Course model for title if needed
                        if prereq_course_obj:
                            prereq_display_name = prereq_course_obj.CourseName
                        else:
                            prereq_display_name = prereq_course_code # Fallback to code if not in DB

                        if prereq_course_code not in all_met_courses_for_prereq_check:
                            prereq_met = False
                    
                    # Also consider year-level prerequisites
                    if not year_unlocked:
                        prereq_met = False
                        if year_name == 'Year 2':
                            prereq_display_name = prereq_display_name or "Completion of Year 1"
                        elif year_name == 'Year 3':
                            prereq_display_name = prereq_display_name or "Completion of Year 2"
                        elif year_name == 'Year 4':
                            prereq_display_name = prereq_display_name or "Completion of Year 3"


                    already_enrolled = course_code in currently_enrolled_course_codes

                    courses_for_template.append({
                        'code': course_code,
                        'title': course_info['title'],
                        'units': course_info['units'],
                        'semester_name': semester_name,
                        'year_name': year_name,
                        'prereq_met': prereq_met,
                        'prerequisites_display': prereq_display_name, # This is the display text
                        'already_enrolled': already_enrolled,
                        'year_unlocked': year_unlocked # Flag to indicate if the whole year is accessible
                    })

        if request.method == 'POST':
            selected_codes = request.form.getlist('courses')
            
            unit_count = 0.0
            for code in selected_codes:
                # Find the units from PROGRAM_STRUCTURE (assuming selected_codes are valid course codes)
                found_units = 0.0
                for year_data in PROGRAM_STRUCTURE.values():
                    for semester_data in year_data.values():
                        for course_info in semester_data:
                            if course_info['code'] == code:
                                found_units = course_info['units']
                                break
                        if found_units > 0: break
                    if found_units > 0: break
                unit_count += found_units

            if unit_count > 4.0:
                flash('You can select a maximum of 4 full units. UU100A and CS001 count as 0.5 units each.', 'error')
                return redirect(url_for('enrollment.enroll'))

            unmet = []
            already_enrolled_in_selection = []
            courses_to_enroll_db_records = [] # To hold Course objects to add to DB

            for course_code in selected_codes:
                # Find the course info from PROGRAM_STRUCTURE for validation
                course_info_selected = None
                for year_data in PROGRAM_STRUCTURE.values():
                    for semester_data in year_data.values():
                        for c_info in semester_data:
                            if c_info['code'] == course_code:
                                course_info_selected = c_info
                                break
                        if course_info_selected: break
                    if course_info_selected: break

                if not course_info_selected:
                    flash(f"Error: Course '{course_code}' not found in program structure.", 'error')
                    continue

                # Re-validate based on current state (important for post-submission checks)
                is_prereq_met_for_selected = True
                prereq_message = ""

                # Check year-level prerequisite first
                selected_course_year_name = None
                for year_name, year_data in PROGRAM_STRUCTURE.items():
                    for semester_courses in year_data.values():
                        if any(c['code'] == course_code for c in semester_courses):
                            selected_course_year_name = year_name
                            break
                    if selected_course_year_name: break

                year_index = list(PROGRAM_STRUCTURE.keys()).index(selected_course_year_name)
                for i in range(year_index):
                    prev_year_name = list(PROGRAM_STRUCTURE.keys())[i]
                    prev_year_unique_courses = get_unique_course_codes_for_year(PROGRAM_STRUCTURE[prev_year_name])
                    if not prev_year_unique_courses.issubset(all_met_courses_for_prereq_check):
                        is_prereq_met_for_selected = False
                        prereq_message = f"Completion of {prev_year_name}"
                        break # Stop checking higher years if a lower one is not met

                # Check individual course prerequisite if year-level is met
                if is_prereq_met_for_selected and course_info_selected['prereq']:
                    prereq_code = course_info_selected['prereq']
                    if prereq_code not in all_met_courses_for_prereq_check:
                        is_prereq_met_for_selected = False
                        prereq_message = course_info_selected['prereq']

                # Check if already enrolled
                if course_code in currently_enrolled_course_codes:
                    already_enrolled_in_selection.append(course_info_selected['title'])
                    continue # Skip to next course if already enrolled

                if not is_prereq_met_for_selected:
                    unmet.append(f"{course_info_selected['title']} (requires {prereq_message})")
                    continue # Skip to next course if prereqs not met

                # If all checks pass, find the Course object from DB
                db_course_obj = Course.query.get(course_code)
                if not db_course_obj:
                    # If for some reason the hardcoded course doesn't exist in DB, create a mock one for enrollment
                    # This is a fallback; ideally, all PROGRAM_STRUCTURE courses should exist in DB
                    logging.warning(f"Course {course_code} from PROGRAM_STRUCTURE not found in DB. Creating a mock Course object for enrollment.")
                    db_course_obj = Course(CourseID=course_code, CourseName=course_info_selected['title'], SubProgramID='SE', PrerequisiteCourseID=course_info_selected['prereq'])
                    # Note: This mock Course won't have proper relationships until committed/flushed
                    db.session.add(db_course_obj) # Add to session, but not commit yet
                
                courses_to_enroll_db_records.append(db_course_obj)


            if unmet:
                flash(f"Cannot enroll in: {', '.join(unmet)} due to unmet prerequisites.", 'error')
            if already_enrolled_in_selection:
                flash(f"You are already enrolled in: {', '.join(already_enrolled_in_selection)}.", 'info')

            if courses_to_enroll_db_records:
                newly_enrolled_count = 0
                for course_to_add in courses_to_enroll_db_records:
                    try:
                        new_enrollment_id = str(uuid.uuid4())[:10]
                        
                        while db.session.get(Enrollment, new_enrollment_id):
                            new_enrollment_id = str(uuid.uuid4())[:10]

                        enrollment = Enrollment(
                            EnrollmentID=new_enrollment_id,
                            StudentID=current_user.id,
                            CourseID=course_to_add.CourseID,
                            EnrollmentDate=datetime.utcnow().date()
                        )
                        db.session.add(enrollment)
                        newly_enrolled_count += 1
                        # Update the set of met courses *immediately* for subsequent prereq checks within the same submission
                        all_met_courses_for_prereq_check.add(course_to_add.CourseID.split('(')[0].strip())
                        currently_enrolled_course_codes.add(course_to_add.CourseID)

                    except IntegrityError:
                        db.session.rollback()
                        flash(f"Error: Duplicate enrollment or ID conflict for {course_to_add.CourseName}. Please try again.", "error")
                        logging.error(f"IntegrityError during enrollment for {current_user.id} in {course_to_add.CourseID}")
                        # Re-fetch courses for template with updated status if needed
                        # For simplicity, redirecting in case of error to force a fresh page load
                        return redirect(url_for('enrollment.enroll'))
                    except Exception as e:
                        db.session.rollback()
                        flash(f"An unexpected error occurred during enrollment for {course_to_add.CourseName}.", "error")
                        logging.error(f"Error enrolling student {current_user.id} in course {course_to_add.CourseID}: {e}")
                        # Redirecting in case of error to force a fresh page load
                        return redirect(url_for('enrollment.enroll'))
                
                db.session.commit()
                if newly_enrolled_count > 0:
                    flash(f'Successfully enrolled in {newly_enrolled_count} new course(s)! Please confirm your courses.', 'success')
                return redirect(url_for('enrollment.display_courses'))

        # Re-evaluate courses_for_template to ensure latest status is reflected
        # This re-evaluation is crucial if some courses were enrolled successfully in the POST request.
        final_courses_for_template = []
        for year_name, year_data in PROGRAM_STRUCTURE.items():
            year_unlocked = True
            if year_name == 'Year 2' and 'Year 1' not in completed_years:
                year_unlocked = False
            elif year_name == 'Year 3' and 'Year 2' not in completed_years:
                year_unlocked = False
            elif year_name == 'Year 4' and 'Year 3' not in completed_years:
                year_unlocked = False

            for semester_name, semester_courses in year_data.items():
                for course_info in semester_courses:
                    course_code = course_info['code']
                    base_course_code = course_code.split('(')[0].strip()

                    prereq_met = True
                    prereq_display_name = None

                    # Re-check year-level prerequisite
                    if not year_unlocked:
                        prereq_met = False
                        if year_name == 'Year 2':
                            prereq_display_name = "Completion of Year 1"
                        elif year_name == 'Year 3':
                            prereq_display_name = "Completion of Year 2"
                        elif year_name == 'Year 4':
                            prereq_display_name = "Completion of Year 3"
                    
                    # Re-check individual course prerequisite (if year is unlocked)
                    if prereq_met and course_info['prereq']:
                        prereq_code = course_info['prereq']
                        # Check against the updated all_met_courses_for_prereq_check
                        if prereq_code not in all_met_courses_for_prereq_check:
                            prereq_met = False
                            prereq_course_obj = Course.query.get(prereq_code)
                            prereq_display_name = prereq_course_obj.CourseName if prereq_course_obj else prereq_code

                    already_enrolled = course_code in currently_enrolled_course_codes

                    final_courses_for_template.append({
                        'code': course_code,
                        'title': course_info['title'],
                        'units': course_info['units'],
                        'semester_name': semester_name,
                        'year_name': year_name,
                        'prereq_met': prereq_met,
                        'prerequisites_display': prereq_display_name,
                        'already_enrolled': already_enrolled,
                        'year_unlocked': year_unlocked
                    })


        return render_template('enroll.html', courses=final_courses_for_template, program_structure=PROGRAM_STRUCTURE)
    except Exception as e:
        logging.error(f"Error in /enroll: {e}")
        db.session.rollback()
        flash("An unexpected error occurred. Please try again.", "error")
        return render_template('500.html'), 500

@enrollment_bp.route('/display_courses')
@token_required
def display_courses(current_user):
    try:
        enrolled_courses = Enrollment.query.filter_by(StudentID=current_user.id).options(joinedload(Enrollment.course)).all()
        
        courses_for_template = []
        # Flatten PROGRAM_STRUCTURE to easily look up semester/units for enrolled courses
        all_program_courses = {}
        for year_data in PROGRAM_STRUCTURE.values():
            for semester_name, semester_courses in year_data.items():
                for course_info in semester_courses:
                    all_program_courses[course_info['code']] = {
                        'title': course_info['title'],
                        'semester': semester_name,
                        'units': course_info['units']
                    }

        for enrollment in enrolled_courses:
            if enrollment.course:
                course_info = all_program_courses.get(enrollment.course.CourseID)
                if course_info:
                    courses_for_template.append({
                        'code': enrollment.course.CourseID,
                        'title': course_info['title'], # Use title from program structure for consistency
                        'semester': course_info['semester'], # Get semester from program structure
                        'units': course_info['units']
                    })
                else:
                     # Fallback if course is enrolled but not in PROGRAM_STRUCTURE
                     courses_for_template.append({
                        'code': enrollment.course.CourseID,
                        'title': enrollment.course.CourseName,
                        'semester': 'Unknown Semester',
                        'units': 1.0 # Default unit if not found
                    })


        return render_template('display_courses.html', enrolled_courses=courses_for_template)
    except Exception as e:
        logging.error(f"Error in /display_courses: {e}")
        return render_template('500.html'), 500

@enrollment_bp.route('/drop_course/<course_code>')
@token_required
def drop_course(current_user, course_code):
    try:
        enrollment_to_delete = Enrollment.query.filter_by(
            StudentID=current_user.id,
            CourseID=course_code
        ).first()

        if enrollment_to_delete:
            db.session.delete(enrollment_to_delete)
            db.session.commit()
            flash(f'Course {course_code} dropped successfully.', 'success')
        else:
            flash(f'Enrollment for course {course_code} not found.', 'error')
            
        return redirect(url_for('enrollment.display_courses'))
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in /drop_course/{course_code}: {e}")
        flash(f"An error occurred while dropping course {course_code}.", "error")
        return render_template('500.html'), 500

@enrollment_bp.route('/fees')
@token_required
def fees(current_user):
    try:
        general_services_fee = 50.00

        enrolled_courses_db = Enrollment.query.filter_by(StudentID=current_user.id).all() # Just need the codes
        
        invoice_items = []
        total_amount = 0

        # Flatten PROGRAM_STRUCTURE to easily look up course details and units
        all_program_courses = {}
        for year_data in PROGRAM_STRUCTURE.values():
            for semester_data in year_data.values():
                for course_info in semester_data:
                    all_program_courses[course_info['code']] = course_info

        for enrollment in enrolled_courses_db:
            course_code = enrollment.CourseID
            course_info = all_program_courses.get(course_code)
            if course_info:
                # Use the 'units' from program structure for calculation
                # For actual fees, you'd still fetch from CourseFee table
                course_fee_amount = 0.0
                db_course_fee = CourseFee.query.filter_by(CourseID=course_code).first()
                if db_course_fee:
                    course_fee_amount = float(db_course_fee.amount)
                else:
                    course_fee_amount = course_info['units'] * 100.00 # Default $100 per unit if no specific fee

                subtotal = course_fee_amount
                invoice_items.append({
                    'code': course_code,
                    'title': course_info['title'],
                    'fee': subtotal
                })
                total_amount += subtotal
            else:
                # Fallback for courses not defined in PROGRAM_STRUCTURE (e.g., old enrollments)
                db_course = Course.query.get(course_code)
                invoice_items.append({
                    'code': course_code,
                    'title': db_course.CourseName if db_course else f"Unknown Course ({course_code})",
                    'fee': 0.00 # Default to 0 if not found in program structure or CourseFee
                })
        
        total_amount += general_services_fee

        student_data = Student.query.get(current_user.id)
        if student_data:
            student_details['name'] = f"{student_data.FirstName} {student_data.LastName}"
            student_details['id'] = student_data.StudentID
        else:
            student_details['name'] = current_user.username
            student_details['id'] = current_user.id
            
        invoice_details['number'] = f"INV-{uuid.uuid4().hex[:8].upper()}"
        invoice_details['date'] = datetime.now().strftime('%B %d, %Y')
        # This will depend on the actual semester the student is viewing fees for
        invoice_details['semester'] = 'Semester 2, 2025' # Hardcoded for now
        student_fees_records = StudentCourseFee.query.filter_by(StudentID=current_user.id, status='Outstanding').first()
        if student_fees_records:
            invoice_details['payment_status'] = 'Pending'
        else:
            invoice_details['payment_status'] = 'Paid'


        return render_template(
            'fees.html',
            student=student_details,
            invoice=invoice_details,
            items=invoice_items,
            total=total_amount,
            general_services_fee=general_services_fee
        )
    except Exception as e:
        logging.error(f"Error in /fees: {e}")
        return render_template('500.html'), 500

@enrollment_bp.route('/download_invoice_pdf')
@token_required
def download_invoice_pdf(current_user):
    try:
        general_services_fee = 50.00

        enrolled_courses_db = Enrollment.query.filter_by(StudentID=current_user.id).all()
        
        invoice_items = []
        total_amount = 0

        all_program_courses = {}
        for year_data in PROGRAM_STRUCTURE.values():
            for semester_data in year_data.values():
                for course_info in semester_data:
                    all_program_courses[course_info['code']] = course_info

        for enrollment in enrolled_courses_db:
            course_code = enrollment.CourseID
            course_info = all_program_courses.get(course_code)
            if course_info:
                course_fee_amount = 0.0
                db_course_fee = CourseFee.query.filter_by(CourseID=course_code).first()
                if db_course_fee:
                    course_fee_amount = float(db_course_fee.amount)
                else:
                    course_fee_amount = course_info['units'] * 100.00

                subtotal = course_fee_amount
                invoice_items.append({
                    'code': course_code,
                    'title': course_info['title'],
                    'fee': subtotal
                })
                total_amount += subtotal
            else:
                 db_course = Course.query.get(course_code)
                 invoice_items.append({
                    'code': course_code,
                    'title': db_course.CourseName if db_course else f"Unknown Course ({course_code})",
                    'fee': 0.00
                })
        
        total_amount += general_services_fee
        
        student_data = Student.query.get(current_user.id)
        if student_data:
            student_details['name'] = f"{student_data.FirstName} {student_data.LastName}"
            student_details['id'] = student_data.StudentID
        else:
            student_details['name'] = current_user.username
            student_details['id'] = current_user.id

        invoice_details['number'] = f"INV-{uuid.uuid4().hex[:8].upper()}"
        invoice_details['date'] = datetime.now().strftime('%B %d, %Y')
        invoice_details['semester'] = 'Semester 2, 2025'
        student_fees_records = StudentCourseFee.query.filter_by(StudentID=current_user.id, status='Outstanding').first()
        if student_fees_records:
            invoice_details['payment_status'] = 'Pending'
        else:
            invoice_details['payment_status'] = 'Paid'


        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Paragraph("Invoice", styles['h1']))
        elements.append(Paragraph("University of the South Pacific", styles['h2']))
        elements.append(Paragraph(f"Invoice Number: {invoice_details['number']}", styles['Normal']))
        elements.append(Paragraph(f"Date: {invoice_details['date']}", styles['Normal']))
        elements.append(Paragraph(f"Semester: {invoice_details['semester']}", styles['Normal']))

        elements.append(Paragraph("Student Details", styles['h3']))
        elements.append(Paragraph(f"Name: {student_details['name']}", styles['Normal']))
        elements.append(Paragraph(f"ID: {student_details['id']}", styles['Normal']))

        data = [['Description', 'Fee']]
        for item in invoice_items:
            fee_display = f"${item['fee']:.2f}" if isinstance(item['fee'], (int, float)) else str(item['fee'])
            data.append([f"{item['title']} ({item['code']})", fee_display])
        
        data.append(['General Services Fee', f"${general_services_fee:.2f}"])

        data.append(['', 'Total:', f"${total_amount:.2f}"])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)

        elements.append(Paragraph(f"Payment Status: {invoice_details['payment_status']}", styles['Normal']))

        doc.build(elements)

        buffer.seek(0)
        response = make_response(buffer.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment;filename=invoice.pdf'

        return response

    except Exception as e:
        logging.error(f"Error in /download_invoice_pdf: {e}")
        return render_template('500.html'), 500

@enrollment_bp.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# --- API Endpoints (JSON Responses) continued ---

# Enrollment Endpoints
@enrollment_bp.route('/enrollments_api', methods=['GET'])
@token_required
def get_enrollments_api(current_user):
    if current_user.role == 'student':
        enrollments = Enrollment.query.options(db.joinedload(Enrollment.student), db.joinedload(Enrollment.course)).filter_by(StudentID=current_user.id).all()
    else:
        enrollments = Enrollment.query.options(db.joinedload(Enrollment.student), db.joinedload(Enrollment.course)).all()
    return jsonify([serialize_enrollment(e) for e in enrollments])

@enrollment_bp.route('/enrollments_api/<string:enrollment_id>', methods=['GET'])
@token_required
def get_enrollment_api(current_user, enrollment_id):
    enrollment = Enrollment.query.options(db.joinedload(Enrollment.student), db.joinedload(Enrollment.course)).get(enrollment_id)
    if not enrollment:
        return jsonify({"message": "Enrollment not found"}), 404

    if current_user.role == 'student' and enrollment.StudentID != current_user.id:
        return jsonify({'message': 'Unauthorized: You can only view your own enrollments'}), 403

    return jsonify(serialize_enrollment(enrollment))

@enrollment_bp.route('/enrollments_api', methods=['POST'])
@token_required
def create_enrollment_api(current_user):
    if current_user.role == 'student' and request.json.get('StudentID') and request.json.get('StudentID') != current_user.id:
        return jsonify({'message': 'Unauthorized: Students can only create enrollments for themselves'}), 403
    if current_user.role not in ['admin', 'sas_manager', 'student']:
         return jsonify({'message': 'Unauthorized: Insufficient privileges to create enrollment'}), 403

    data = request.json
    if not data or not all(k in data for k in ['EnrollmentID', 'StudentID', 'CourseID']):
        return jsonify({"message": "Missing enrollment data (requires EnrollmentID, StudentID, CourseID)"}), 400

    student = Student.query.get(data['StudentID'])
    course = Course.query.get(data['CourseID'])
    if not student:
        return jsonify({"message": "Student not found"}), 404
    if not course:
        return jsonify({"message": "Course not found"}), 404

    existing_enrollment = Enrollment.query.filter_by(StudentID=data['StudentID'], CourseID=data['CourseID']).first()
    if existing_enrollment:
        return jsonify({"message": "Student already enrolled in this course"}), 409

    new_enrollment = Enrollment(
        EnrollmentID=data['EnrollmentID'],
        StudentID=data['StudentID'],
        CourseID=data['CourseID'],
        EnrollmentDate=datetime.strptime(data['EnrollmentDate'], '%Y-%m-%d').date() if 'EnrollmentDate' in data and data['EnrollmentDate'] else datetime.utcnow().date()
    )
    db.session.add(new_enrollment)
    try:
        db.session.commit()
        return jsonify({"message": "Enrollment created successfully", "enrollment_id": new_enrollment.EnrollmentID}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Enrollment with this ID already exists"}), 409
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating enrollment: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/enrollments_api/<string:enrollment_id>', methods=['PUT'])
@token_required
def update_enrollment_api(current_user, enrollment_id):
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators or SAS managers can update enrollments'}), 403

    enrollment = Enrollment.query.get(enrollment_id)
    if not enrollment:
        return jsonify({"message": "Enrollment not found"}), 404

    data = request.json
    if not data:
        return jsonify({"message": "No data provided for update"}), 400

    if 'EnrollmentDate' in data:
        enrollment.EnrollmentDate = datetime.strptime(data['EnrollmentDate'], '%Y-%m-%d').date() if data['EnrollmentDate'] else None

    try:
        db.session.commit()
        return jsonify({"message": "Enrollment updated successfully", "enrollment_id": enrollment.EnrollmentID}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating enrollment {enrollment_id}: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/enrollments_api/<string:enrollment_id>', methods=['DELETE'])
@token_required
def delete_enrollment_api(current_user, enrollment_id):
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators or SAS managers can delete enrollments'}), 403

    enrollment = Enrollment.query.get(enrollment_id)
    if not enrollment:
        return jsonify({"message": "Enrollment not found"}), 404

    db.session.delete(enrollment)
    try:
        db.session.commit()
        return jsonify({"message": "Enrollment deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting enrollment {enroll_id}: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500


# Course Fees Endpoints
@enrollment_bp.route('/course_fees_api', methods=['GET'])
@token_required
def get_course_fees_api(current_user):
    fees = CourseFee.query.options(db.joinedload(CourseFee.course)).all()
    return jsonify([serialize_course_fee(f) for f in fees])

@enrollment_bp.route('/course_fees_api/<string:fee_id>', methods=['GET'])
@token_required
def get_course_fee_api(current_user, fee_id):
    fee = CourseFee.query.options(db.joinedload(CourseFee.course)).get(fee_id)
    if not fee:
        return jsonify({"message": "Course fee not found"}), 404
    return jsonify(serialize_course_fee(fee))

@enrollment_bp.route('/course_fees_api', methods=['POST'])
@token_required
def add_course_fee_api(current_user):
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators or SAS managers can add course fees'}), 403

    data = request.json
    if not data or not all(k in data for k in ['FeeID', 'amount', 'CourseID']):
        return jsonify({"message": "Missing course fee data (requires FeeID, amount, CourseID)"}), 400

    course = Course.query.get(data['CourseID'])
    if not course:
        return jsonify({"message": "Course not found"}), 404
    
    existing_fee = CourseFee.query.get(data['FeeID'])
    if existing_fee:
        return jsonify({"message": "Course fee with this ID already exists"}), 409

    new_fee = CourseFee(
        FeeID=data['FeeID'],
        amount=data['amount'],
        description=data.get('description'),
        CourseID=data['CourseID']
    )
    db.session.add(new_fee)
    try:
        db.session.commit()
        return jsonify({"message": "Course fee added successfully", "fee_id": new_fee.FeeID}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Course fee with this ID already exists"}), 409
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding course fee: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/course_fees_api/<string:fee_id>', methods=['PUT'])
@token_required
def update_course_fee_api(current_user, fee_id):
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators or SAS managers can update course fees'}), 403

    fee = CourseFee.query.get(fee_id)
    if not fee:
        return jsonify({"message": "Course fee not found"}), 404

    data = request.json
    if not data:
        return jsonify({"message": "No data provided for update"}), 400

    if 'amount' in data:
        fee.amount = data['amount']
    if 'description' in data:
        fee.description = data['description']
    if 'CourseID' in data:
        course = Course.query.get(data['CourseID'])
        if not course:
            return jsonify({"message": "New CourseID for fee does not exist"}), 404
        fee.CourseID = data['CourseID']

    try:
        db.session.commit()
        return jsonify({"message": "Course fee updated successfully", "fee_id": fee.FeeID}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating course fee {fee_id}: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/course_fees_api/<string:fee_id>', methods=['DELETE'])
@token_required
def delete_course_fee_api(current_user, fee_id):
    if current_user.role != 'admin':
        return jsonify({'message': 'Unauthorized: Only administrators can delete course fees'}), 403

    fee = CourseFee.query.get(fee_id)
    if not fee:
        return jsonify({"message": "Course fee not found"}), 404

    try:
        if StudentCourseFee.query.filter_by(FeeID=fee_id).first():
            return jsonify({"message": "Cannot delete course fee; existing student course fees depend on it. Delete related student fees first."}), 409

        db.session.delete(fee)
        db.session.commit()
        return jsonify({"message": "Course fee deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting course fee {fee_id}: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

# Student Course Fees Endpoints
@enrollment_bp.route('/student_course_fees_api', methods=['GET'])
@token_required
def get_student_course_fees_api(current_user):
    if current_user.role == 'student':
        student_fees = StudentCourseFee.query.options(
            db.joinedload(StudentCourseFee.student),
            db.joinedload(StudentCourseFee.course),
            db.joinedload(StudentCourseFee.course_fee)
        ).filter_by(StudentID=current_user.id).all()
    else:
        student_fees = StudentCourseFee.query.options(
            db.joinedload(StudentCourseFee.student),
            db.joinedload(StudentCourseFee.course),
            db.joinedload(StudentCourseFee.course_fee)
        ).all()
    return jsonify([serialize_student_course_fee(sf) for sf in student_fees])

@enrollment_bp.route('/student_course_fees_api/<string:scf_id>', methods=['GET'])
@token_required
def get_student_course_fee_api(current_user, scf_id):
    student_fee = StudentCourseFee.query.options(
        db.joinedload(StudentCourseFee.student),
        db.joinedload(StudentCourseFee.course),
        db.joinedload(StudentCourseFee.course_fee)
    ).get(scf_id)
    if not student_fee:
        return jsonify({"message": "Student course fee not found"}), 404

    if current_user.role == 'student' and student_fee.StudentID != current_user.id:
        return jsonify({'message': 'Unauthorized: You can only view your own student course fees'}), 403

    return jsonify(serialize_student_course_fee(student_fee))

@enrollment_bp.route('/student_course_fees_api', methods=['POST'])
@token_required
def assign_student_course_fee_api(current_user):
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators or SAS managers can assign student course fees'}), 403

    data = request.json
    if not data or not all(k in data for k in ['StudentCourseFeeID', 'StudentID', 'CourseID', 'amount', 'due_date']):
        return jsonify({"message": "Missing student course fee data (requires StudentCourseFeeID, StudentID, CourseID, amount, due_date)"}), 400

    student = Student.query.get(data['StudentID'])
    course = Course.query.get(data['CourseID'])
    if not student:
        return jsonify({"message": "Student not found"}), 404
    if not course:
        return jsonify({"message": "Course not found"}), 404

    fee_id = data.get('FeeID')
    if fee_id:
        course_fee = CourseFee.query.get(fee_id)
        if not course_fee:
            return jsonify({"message": "Provided FeeID does not exist"}), 404
        if course_fee.CourseID != course.CourseID:
            return jsonify({"message": "Provided FeeID does not belong to the specified CourseID"}), 400

    existing_assignment = StudentCourseFee.query.filter_by(StudentID=data['StudentID'], CourseID=data['CourseID']).first()
    if existing_assignment:
        return jsonify({"message": "Student already has a fee assigned for this course"}), 409
    
    existing_scf_id = StudentCourseFee.query.get(data['StudentCourseFeeID'])
    if existing_scf_id:
        return jsonify({"message": "Student Course Fee with this ID already exists"}), 409


    new_student_fee = StudentCourseFee(
        StudentCourseFeeID=data['StudentCourseFeeID'],
        StudentID=data['StudentID'],
        CourseID=data['CourseID'],
        amount=data['amount'],
        due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date(),
        paid_date=datetime.strptime(data['paid_date'], '%Y-%m-%d').date() if 'paid_date' in data and data['paid_date'] else None,
        status=data.get('status', 'Outstanding'),
        FeeID=fee_id
    )
    db.session.add(new_student_fee)
    try:
        db.session.commit()
        return jsonify({"message": "Student course fee assigned successfully", "student_course_fee_id": new_student_fee.StudentCourseFeeID}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Failed to assign student course fee due to data conflict"}), 409
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error assigning student course fee: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/student_course_fees_api/<string:scf_id>', methods=['PUT'])
@token_required
def update_student_course_fee_api(current_user, scf_id):
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators or SAS managers can update student course fees'}), 403

    student_fee = StudentCourseFee.query.get(scf_id)
    if not student_fee:
        return jsonify({"message": "Student course fee not found"}), 404

    data = request.json
    if not data:
        return jsonify({"message": "No data provided for update"}), 400

    if 'amount' in data:
        student_fee.amount = data['amount']
    if 'due_date' in data:
        student_fee.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
    if 'paid_date' in data:
        student_fee.paid_date = datetime.strptime(data['paid_date'], '%Y-%m-%d').date() if data['paid_date'] else None
    if 'status' in data:
        student_fee.status = data['status']
    if 'FeeID' in data:
        course_fee = CourseFee.query.get(data['FeeID'])
        if not course_fee:
            return jsonify({"message": "New FeeID for student course fee does not exist"}), 404
        student_fee.FeeID = data['FeeID']

    try:
        db.session.commit()
        return jsonify({"message": "Student course fee updated successfully", "student_course_fee_id": student_fee.StudentCourseFeeID}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating student course fee {scf_id}: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/student_course_fees_api/<string:scf_id>', methods=['DELETE'])
@token_required
def delete_student_course_fee_api(current_user, scf_id):
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators or SAS managers can delete student course fees'}), 403

    student_fee = StudentCourseFee.query.get(scf_id)
    if not student_fee:
        return jsonify({"message": "Student course fee not found"}), 404

    db.session.delete(student_fee)
    try:
        db.session.commit()
        return jsonify({"message": "Student course fee deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting student course fee {scf_id}: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

# Hold Endpoints
@enrollment_bp.route('/holds', methods=['GET'])
@token_required
def get_holds(current_user):
    if current_user.role == 'student':
        holds = Hold.query.options(db.joinedload(Hold.student)).filter_by(StudentID=current_user.id).all()
    else:
        holds = Hold.query.options(db.joinedload(Hold.student)).all()
    return jsonify([serialize_hold(h) for h in holds])

@enrollment_bp.route('/holds/<string:hold_id>', methods=['GET'])
@token_required
def get_hold(current_user, hold_id):
    hold = Hold.query.options(db.joinedload(Hold.student)).get(hold_id)
    if not hold:
        return jsonify({"message": "Hold not found"}), 404

    if current_user.role == 'student' and hold.StudentID != current_user.id:
        return jsonify({'message': 'Unauthorized: You can only view your own holds'}), 403

    return jsonify(serialize_hold(hold))

@enrollment_bp.route('/holds', methods=['POST'])
@token_required
def add_hold(current_user):
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators or SAS managers can add holds'}), 403

    data = request.json
    if not data or not all(k in data for k in ['HoldID', 'StudentID', 'reason']):
        return jsonify({"message": "Missing hold data (requires HoldID, StudentID, reason)"}), 400

    student = Student.query.get(data['StudentID'])
    if not student:
        return jsonify({"message": "Student not found"}), 404
    
    existing_hold = Hold.query.get(data['HoldID'])
    if existing_hold:
        return jsonify({"message": "Hold with this ID already exists"}), 409


    new_hold = Hold(
        HoldID=data['HoldID'],
        StudentID=data['StudentID'],
        reason=data['reason'],
        holdDate=datetime.strptime(data['holdDate'], '%Y-%m-%d').date() if 'holdDate' in data and data['holdDate'] else datetime.utcnow().date(),
        liftDate=datetime.strptime(data['liftDate'], '%Y-%m-%d').date() if 'liftDate' in data and data['liftDate'] else None,
        status=data.get('status', 'Active')
    )
    db.session.add(new_hold)
    try:
        db.session.commit()
        return jsonify({"message": "Hold added successfully", "hold_id": new_hold.HoldID}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Hold with this ID already exists"}), 409
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding hold: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/holds/<string:hold_id>', methods=['PUT'])
@token_required
def update_hold(current_user, hold_id):
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators or SAS managers can update holds'}), 403

    hold = Hold.query.get(hold_id)
    if not hold:
        return jsonify({"message": "Hold not found"}), 404

    data = request.json
    if not data:
        return jsonify({"message": "No data provided for update"}), 400

    if 'reason' in data:
        hold.reason = data['reason']
    if 'holdDate' in data:
        hold.holdDate = datetime.strptime(data['holdDate'], '%Y-%m-%d').date() if data['holdDate'] else None
    if 'liftDate' in data:
        hold.liftDate = datetime.strptime(data['liftDate'], '%Y-%m-%d').date() if data['liftDate'] else None
    if 'status' in data:
        hold.status = data['status']
    if 'StudentID' in data:
        student = Student.query.get(data['StudentID'])
        if not student:
            return jsonify({"message": "New StudentID for hold does not exist"}), 404
        hold.StudentID = data['StudentID']

    try:
        db.session.commit()
        return jsonify({"message": "Hold updated successfully", "hold_id": hold.HoldID}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating hold {hold_id}: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/holds/<string:hold_id>', methods=['DELETE'])
@token_required
def delete_hold(current_user, hold_id):
    if current_user.role != 'admin':
        return jsonify({'message': 'Unauthorized: Only administrators can delete holds'}), 403

    hold = Hold.query.get(hold_id)
    if not hold:
        return jsonify({"message": "Hold not found"}), 404

    db.session.delete(hold)
    try:
        db.session.commit()
        return jsonify({"message": "Hold deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting hold {hold_id}: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

# Student Level Endpoints
@enrollment_bp.route('/student_levels', methods=['GET'])
@token_required
def get_student_levels(current_user):
    if current_user.role == 'student':
        student_levels = StudentLevel.query.options(db.joinedload(StudentLevel.student)).filter_by(StudentID=current_user.id).all()
    else:
        student_levels = StudentLevel.query.options(db.joinedload(StudentLevel.student)).all()
    return jsonify([serialize_student_level(sl) for sl in student_levels])

@enrollment_bp.route('/student_levels/<string:student_level_id>', methods=['GET'])
@token_required
def get_student_level(current_user, student_level_id):
    student_level = StudentLevel.query.options(db.joinedload(StudentLevel.student)).get(student_level_id)
    if not student_level:
        return jsonify({"message": "Student level not found"}), 404

    if current_user.role == 'student' and student_level.StudentID != current_user.id:
        return jsonify({'message': 'Unauthorized: You can only view your own student levels'}), 403

    return jsonify(serialize_student_level(student_level))

@enrollment_bp.route('/student_levels', methods=['POST'])
@token_required
def add_student_level(current_user):
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators or SAS managers can add student levels'}), 403

    data = request.json
    if not data or not all(k in data for k in ['StudentLevelID', 'StudentID']):
        return jsonify({"message": "Missing student level data (requires StudentLevelID, StudentID)"}), 400

    student = Student.query.get(data['StudentID'])
    if not student:
        return jsonify({"message": "Student not found"}), 404
    
    existing_level = StudentLevel.query.get(data['StudentLevelID'])
    if existing_level:
        return jsonify({"message": "Student level with this ID already exists"}), 409

    new_student_level = StudentLevel(
        StudentLevelID=data['StudentLevelID'],
        StudentID=data['StudentID'],
        LevelName=data.get('LevelName'),
        AttributeName1=data.get('AttributeName1'),
        AttributeName2=data.get('AttributeName2')
    )
    db.session.add(new_student_level)
    try:
        db.session.commit()
        return jsonify({"message": "Student level added successfully", "student_level_id": new_student_level.StudentLevelID}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Student level with this ID already exists"}), 409
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding student level: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/student_levels/<string:student_level_id>', methods=['PUT'])
@token_required
def update_student_level(current_user, student_level_id):
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators or SAS managers can update student levels'}), 403

    student_level = StudentLevel.query.get(student_level_id)
    if not student_level:
        return jsonify({"message": "Student level not found"}), 404

    data = request.json
    if not data:
        return jsonify({"message": "No data provided for update"}), 400

    if 'LevelName' in data:
        student_level.LevelName = data['LevelName']
    if 'AttributeName1' in data:
        student_level.AttributeName1 = data['AttributeName1']
    if 'AttributeName2' in data:
        student_level.AttributeName2 = data['AttributeName2']
    if 'StudentID' in data:
        student = Student.query.get(data['StudentID'])
        if not student:
            return jsonify({"message": "New StudentID for student level does not exist"}), 404
        student_level.StudentID = data['StudentID']

    try:
        db.session.commit()
        return jsonify({"message": "Student level updated successfully", "student_level_id": student_level.StudentLevelID}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating student level {student_level_id}: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/student_levels/<string:student_level_id>', methods=['DELETE'])
@token_required
def delete_student_level(current_user, student_level_id):
    if current_user.role != 'admin':
        return jsonify({'message': 'Unauthorized: Only administrators can delete student levels'}), 403

    student_level = StudentLevel.query.get(student_level_id)
    if not student_level:
        return jsonify({"message": "Student level not found"}), 404

    db.session.delete(student_level)
    try:
        db.session.commit()
        return jsonify({"message": "Student level deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting student level {student_level_id}: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500