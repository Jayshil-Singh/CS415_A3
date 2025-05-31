# enrollment_services/routes.py
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session, make_response, current_app
import logging
from io import BytesIO
from datetime import datetime, timedelta
import jwt
from functools import wraps
import uuid
import random # For dummy grade generation

# ReportLab Imports
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.orm import joinedload

# Import db and models from your package.
from .db import db
from .model import (
    Program, SubProgram, Semester, Course, CourseAvailability,
    Student, StudentLevel, Hold, Enrollment, CourseFee, StudentCourseFee,
    User,
    Grade, GradeRecheck, SpecialApplication, ServiceAccess
)

# --- Blueprint Initialization ---
enrollment_bp = Blueprint('enrollment', __name__, template_folder='templates')

# --- Logging Setup ---
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# --- IMPORTANT: Flask App Configuration for JWT ---
# Ensure these are set in your main Flask app instance (e.g., in app.py or config.py)
# Example:
# app.config['JWT_SECRET_KEY'] = 'your_super_secret_key_here' # Change this to a strong, random key
# app.config['JWT_EXPIRATION_DELTA'] = timedelta(hours=1) # Token valid for 1 hour
# If not set, you will get a KeyError or similar 500 error.

# --- Mock Data (IMPORTANT: To be Replaced with Actual Database Interactions) ---
# Note: student_details and invoice_details will be largely superseded by live data from DB in new routes.
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

# --- Define Program Structure and Prerequisites (EXISTING LOGIC) ---
PROGRAM_STRUCTURE = {
    'Year 1': {
        'Semester 1': [
            {'code': 'CS111', 'title': 'Introduction to C++ Programming', 'units': 1.0, 'prereq': None},
            {'code': 'ST131', 'title': 'Introduction to Statistics', 'units': 1.0, 'prereq': None},
            {'code': 'UU114', 'title': 'English for Academic Purposes', 'units': 1.0, 'prereq': None},
            {'code': 'MA111', 'title': 'Calculus and Linear Algebra', 'units': 1.0, 'prereq': None},
            {'code': 'UU100A', 'title': 'Communications and Information Literacy', 'units': 0.5, 'prereq': None},
            {'code': 'MG101', 'title': 'Introduction to Management', 'units': 1.0, 'prereq': None},
        ],
        'Semester 2': [
            {'code': 'CS111', 'title': 'Introduction to C++ Programming', 'units': 1.0, 'prereq': None},
            {'code': 'CS112', 'title': 'Data Structures and Algorithms', 'units': 1.0, 'prereq': 'CS111'},
            {'code': 'UU114', 'title': 'English for Academic Purposes (Repeat)', 'units': 1.0, 'prereq': None},
            {'code': 'MG101', 'title': 'Introduction to Management', 'units': 1.0, 'prereq': None},
            {'code': 'UU100A', 'title': 'Communications and Information Literacy', 'units': 0.5, 'prereq': None},
            {'code': 'MA161', 'title': 'Discrete Mathematics', 'units': 1.0, 'prereq': None},
            {'code': 'CS140', 'title': 'Introduction to Software Engineering', 'units': 1.0, 'prereq': None},
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
            base_code = course['code'].split('(')[0].strip()
            unique_codes.add(base_code)
    return unique_codes

# --- Helper Functions for Data Processing and Serialization ---

def calculate_invoice(enrolled_courses_codes):
    """Calculates the invoice details for the given course codes."""
    invoice_items = []
    total_amount = 0
    
    all_program_courses = {}
    for year_data in PROGRAM_STRUCTURE.values():
        for semester_data in year_data.values():
            for course_info in semester_data:
                all_program_courses[course_info['code']] = course_info

    for course_code in enrolled_courses_codes:
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
                'code': course_info['code'],
                'title': course_info['title'],
                'credits': course_info['units'],
                'fee_per_credit': course_fee_amount,
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

# New Serialization functions for the new models
def serialize_grade(grade):
    return {
        "GradeID": grade.id,
        "StudentID": grade.student_id,
        "CourseID": grade.course_id,
        "LetterGrade": grade.letter_grade,
        "NumericalGrade": grade.numerical_grade,
        "Year": grade.year,
        "Semester": grade.semester,
        "CourseName": grade.course.CourseName if grade.course else None,
        "StudentName": f"{grade.student.FirstName} {grade.student.LastName}" if grade.student else None
    }

def serialize_grade_recheck(recheck):
    return {
        "RecheckID": recheck.id,
        "StudentID": recheck.student_id,
        "GradeID": recheck.grade_id,
        "CourseID": recheck.course_id,
        "OriginalGrade": recheck.original_grade,
        "Reason": recheck.reason,
        "Status": recheck.status,
        "AdminNotes": recheck.admin_notes,
        "DateSubmitted": recheck.date_submitted.isoformat() if recheck.date_submitted else None,
        "DateResolved": recheck.date_resolved.isoformat() if recheck.date_resolved else None,
        "NewGradeIfChanged": recheck.new_grade_if_changed,
        "StudentName": f"{recheck.student.FirstName} {recheck.student.LastName}" if recheck.student else None,
        "CourseName": recheck.course.CourseName if recheck.course else None
    }

def serialize_special_application(app):
    return {
        "ApplicationID": app.id,
        "StudentID": app.student_id,
        "ApplicationType": app.application_type,
        "CourseID": app.course_id,
        "Reason": app.reason,
        "Status": app.status,
        "AdminNotes": app.admin_notes,
        "DateSubmitted": app.date_submitted.isoformat() if app.date_submitted else None,
        "DateResolved": app.date_resolved.isoformat() if app.date_resolved else None,
        "ExternalFormPath": app.external_form_path,
        "StudentName": f"{app.student.FirstName} {app.student.LastName}" if app.student else None,
        "CourseName": app.course.CourseName if app.course else None
    }

def serialize_service_access(service):
    return {
        "ServiceID": service.id,
        "ServiceName": service.service_name,
        "IsAvailableOnHold": service.is_available_on_hold
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
            logging.warning("Token missing for authenticated route access.")
            if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
                flash("Authentication required to access this page.", "error")
                return redirect(url_for('enrollment.login_page'))
            else:
                return jsonify({'message': 'Token is missing!'}), 401

        try:
            # Ensure JWT_SECRET_KEY is set in current_app.config
            if 'JWT_SECRET_KEY' not in current_app.config:
                logging.error("JWT_SECRET_KEY is not configured in Flask app.config!")
                raise ValueError("JWT_SECRET_KEY is not configured")

            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                logging.warning(f"User with ID {data.get('user_id')} not found for valid token.")
                if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
                    flash("Invalid user associated with token. Please log in again.", "error")
                    return redirect(url_for('enrollment.login_page'))
                else:
                    return jsonify({'message': 'User not found!'}), 401

        except jwt.ExpiredSignatureError:
            logging.warning("Expired JWT token detected.")
            if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
                flash("Your session has expired. Please log in again.", "error")
                return redirect(url_for('enrollment.login_page'))
            else:
                return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            logging.warning("Invalid JWT token detected.")
            if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
                flash("Invalid authentication token. Please log in again.", "error")
                return redirect(url_for('enrollment.login_page'))
            else:
                return jsonify({'message': 'Token is invalid!'}), 401
        except Exception as e:
            logging.exception(f"Token verification unexpected error: {e}") # Use exception for full traceback
            if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
                flash("Authentication error. Please log in again.", "error")
                return redirect(url_for('enrollment.login_page'))
            else:
                return jsonify({'message': 'Token verification failed: ' + str(e)}), 401

        return f(current_user, *args, **kwargs)

    return decorated

@enrollment_bp.route('/login', methods=['GET']) # Added a GET route for login page
def login_page():
    return render_template('login.html')

@enrollment_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    if not data:
        data = request.form

    if not data or not 'username' in data or not 'password' in data:
        logging.warning("Login attempt with missing username or password.")
        if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
            flash('Missing username or password', 'error')
            return redirect(url_for('enrollment.login_page'))
        else:
            return jsonify({'message': 'Missing username or password'}), 400

    username = data['username']
    password = data['password']

    user = None
    try:
        user = User.query.filter_by(username=username).first()
        if not user:
            logging.info(f"Login failed: User '{username}' not found.")
            if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
                flash('Invalid credentials', 'error')
                return redirect(url_for('enrollment.login_page'))
            else:
                return jsonify({'message': 'Invalid credentials'}), 401
        
        # IMPORTANT: Ensure your User model has a check_password method
        # that securely verifies the password (e.g., using werkzeug.security.check_password_hash)
        if not user.check_password(password):
            logging.info(f"Login failed: Incorrect password for user '{username}'.")
            if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
                flash('Invalid credentials', 'error')
                return redirect(url_for('enrollment.login_page'))
            else:
                return jsonify({'message': 'Invalid credentials'}), 401

    except AttributeError as e:
        # This likely means user.check_password does not exist or is malformed
        logging.exception(f"AttributeError during user authentication for '{username}': {e}. "
                          "Ensure User model has a 'check_password' method.")
        if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
            flash('Server error during login. Please contact support.', 'error')
            return redirect(url_for('enrollment.login_page'))
        else:
            return jsonify({'message': 'Server error during authentication.'}), 500
    except Exception as e:
        logging.exception(f"Unexpected error during user lookup or password check for '{username}': {e}")
        if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
            flash('An unexpected error occurred during login. Please try again.', 'error')
            return redirect(url_for('enrollment.login_page'))
        else:
            return jsonify({'message': 'An unexpected server error occurred.'}), 500

    try:
        # Ensure JWT_SECRET_KEY and JWT_EXPIRATION_DELTA are set
        if 'JWT_SECRET_KEY' not in current_app.config:
            logging.error("JWT_SECRET_KEY is not configured in Flask app.config!")
            raise ValueError("JWT_SECRET_KEY is not configured")
        if 'JWT_EXPIRATION_DELTA' not in current_app.config:
            logging.error("JWT_EXPIRATION_DELTA is not configured in Flask app.config!")
            # Provide a default if not set, or raise error
            current_app.config['JWT_EXPIRATION_DELTA'] = timedelta(hours=1)
            logging.warning("Using default JWT_EXPIRATION_DELTA (1 hour). Please configure it explicitly.")

        token_payload = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'exp': datetime.utcnow() + current_app.config['JWT_EXPIRATION_DELTA']
        }
        token = jwt.encode(token_payload, current_app.config['JWT_SECRET_KEY'], algorithm="HS256")

        session['jwt_token'] = token
        session['user_role'] = user.role # Store role in session for easier access in templates

        logging.info(f"User '{username}' logged in successfully. Role: {user.role}")

        if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
            flash('Login successful!', 'success')
            # Redirect based on role if needed, otherwise to a general dashboard
            if user.role == 'student':
                return redirect(url_for('enrollment.dashboard'))
            # REMOVED ADMIN REDIRECTION: elif user.role in ['admin', 'sas_manager']:
            # REMOVED ADMIN REDIRECTION:     return redirect(url_for('enrollment.admin_dashboard'))
            else: # For any other role, or if student, go to dashboard
                return redirect(url_for('enrollment.dashboard'))
        else:
            return jsonify({'message': 'Login successful', 'token': token, 'user': {'id': user.id, 'username': user.username, 'role': user.role}}), 200
    except Exception as e:
        logging.exception(f"Error during JWT encoding or session management for user '{username}': {e}")
        if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
            flash('An error occurred after successful login. Please try again.', 'error')
            return redirect(url_for('enrollment.login_page'))
        else:
            return jsonify({'message': 'Server error after authentication.'}), 500

@enrollment_bp.route('/auth/logout')
@token_required
def logout(current_user):
    session.pop('jwt_token', None)
    session.pop('user_role', None)
    flash('You have been logged out.', 'info')
    logging.info(f"User '{current_user.username}' logged out.")
    return redirect(url_for('enrollment.login_page'))


@enrollment_bp.route('/auth/verify_token', methods=['GET'])
@token_required
def verify_token(current_user):
    logging.debug(f"Token verification successful for user '{current_user.username}'.")
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
        try:
            # Ensure JWT_SECRET_KEY is set
            if 'JWT_SECRET_KEY' not in current_app.config:
                logging.error("JWT_SECRET_KEY is not configured in Flask app.config for set_session_token!")
                raise ValueError("JWT_SECRET_KEY is not configured")

            decoded_token = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            session['jwt_token'] = token
            session['user_role'] = decoded_token.get('role')
            logging.info(f"Session token set for user ID: {decoded_token.get('user_id')}, role: {decoded_token.get('role')}")
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
            logging.warning(f"Attempted to set expired or invalid token in session via set_session_token: {e}")
            # Clear session token if it's invalid
            session.pop('jwt_token', None)
            session.pop('user_role', None)
            return jsonify({'message': 'Provided token is invalid or expired'}), 400
        except Exception as e:
            logging.exception(f"Unexpected error in set_session_token: {e}")
            return jsonify({'message': 'Server error setting session token.'}), 500

        return jsonify({'message': 'Token set in session successfully'}), 200
    else:
        logging.warning("No token provided to set_session_token.")
        return jsonify({'message': 'No token provided'}), 400

# --- Frontend-facing Routes (HTML Rendering) ---

@enrollment_bp.route('/')
@enrollment_bp.route('/dashboard')
@token_required
def dashboard(current_user):
    if current_user.role == 'student':
        has_active_hold = Hold.query.filter_by(StudentID=current_user.id, status='Active').first() is not None
        logging.info(f"Rendering dashboard for student '{current_user.username}'. Has active hold: {has_active_hold}")
        return render_template('dashboard.html', current_user=current_user, has_active_hold=has_active_hold)
    else: # If not a student, or any other role, redirect to general dashboard
        flash("Unauthorized access. This dashboard is for students only.", "error")
        logging.warning(f"Unauthorized dashboard access attempt by user '{current_user.username}' with role '{current_user.role}'.")
        return redirect(url_for('enrollment.login_page'))


# REMOVED ADMIN DASHBOARD ROUTE: @enrollment_bp.route('/admin_dashboard')
# REMOVED ADMIN DASHBOARD ROUTE: def admin_dashboard(current_user):
# REMOVED ADMIN DASHBOARD ROUTE:    if current_user.role not in ['admin', 'sas_manager']:
# REMOVED ADMIN REDIRECTION:        flash("Unauthorized access.", "error")
# REMOVED ADMIN REDIRECTION:        return redirect(url_for('enrollment.dashboard'))
# REMOVED ADMIN REDIRECTION:    return render_template('admin_dashboard.html', current_user=current_user)

@enrollment_bp.route('/enroll', methods=['GET', 'POST'])
@token_required
def enroll(current_user):
    # Student role check
    if current_user.role != 'student':
        flash("Unauthorized access. Only students can enroll in courses.", "error")
        logging.warning(f"Enrollment access denied for non-student user '{current_user.username}'.")
        return redirect(url_for('enrollment.dashboard'))

    # Check if student is on hold before allowing enrollment
    active_hold = Hold.query.filter_by(StudentID=current_user.id, status='Active').first()
    if active_hold:
        course_reg_service = ServiceAccess.query.filter_by(service_name='course_registration').first()
        if course_reg_service and not course_reg_service.is_available_on_hold:
            flash(f"You have an active hold on your account ({active_hold.reason}). Course registration is currently restricted. Please resolve your hold.", "error")
            logging.info(f"Enrollment restricted for student '{current_user.username}' due to active hold: {active_hold.reason}.")
            return redirect(url_for('enrollment.student_hold_status'))

    try:
        current_enrollments = Enrollment.query.filter_by(StudentID=current_user.id).all()
        currently_enrolled_course_codes = {e.CourseID for e in current_enrollments}

        all_met_courses_for_prereq_check = set()
        completed_grades = Grade.query.filter_by(student_id=current_user.id).all()
        for grade_record in completed_grades:
            if grade_record.letter_grade.upper() in ['A+', 'A', 'B+', 'B', 'C+', 'C', 'P', 'CR', 'AEG', 'CMP']:
                all_met_courses_for_prereq_check.add(grade_record.course.CourseID.split('(')[0].strip()) # Use CourseID from model
        
        for course_code in currently_enrolled_course_codes:
            all_met_courses_for_prereq_check.add(course_code.split('(')[0].strip())


        completed_years = set()
        
        year_1_unique_courses = get_unique_course_codes_for_year(PROGRAM_STRUCTURE['Year 1'])
        if year_1_unique_courses.issubset(all_met_courses_for_prereq_check):
            completed_years.add('Year 1')

        if 'Year 1' in completed_years:
            year_2_unique_courses = get_unique_course_codes_for_year(PROGRAM_STRUCTURE['Year 2'])
            if year_2_unique_courses.issubset(all_met_courses_for_prereq_check):
                completed_years.add('Year 2')

        if 'Year 2' in completed_years:
            year_3_unique_courses = get_unique_course_codes_for_year(PROGRAM_STRUCTURE['Year 3'])
            if year_3_unique_courses.issubset(all_met_courses_for_prereq_check):
                completed_years.add('Year 3')
        
        if 'Year 3' in completed_years:
            year_4_unique_courses = get_unique_course_codes_for_year(PROGRAM_STRUCTURE['Year 4'])
            if year_4_unique_courses.issubset(all_met_courses_for_prereq_check):
                completed_years.add('Year 4')

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
                    base_course_code = course_code.split('(')[0].strip()

                    prereq_met = True
                    prereq_display_name = None

                    if course_info['prereq']:
                        prereq_course_code = course_info['prereq']
                        prereq_course_obj = Course.query.get(prereq_course_code)
                        if prereq_course_obj:
                            prereq_display_name = prereq_course_obj.CourseName
                        else:
                            prereq_display_name = prereq_course_code

                        if prereq_course_code not in all_met_courses_for_prereq_check:
                            prereq_met = False
                    
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
                        'prerequisites_display': prereq_display_name,
                        'already_enrolled': already_enrolled,
                        'year_unlocked': year_unlocked
                    })

        if request.method == 'POST':
            selected_codes = request.form.getlist('courses')
            
            unit_count = 0.0
            for code in selected_codes:
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

            # CUSTOM MESSAGE START
            if unit_count > 4.0:
                flash('You have exceeded the maximum enrollment limit of 4 full units. Please note that UU100A and CS001 each count as 0.5 units. Adjust your selection to proceed.', 'error')
                logging.warning(f"Student '{current_user.username}' attempted to enroll in {unit_count} units, exceeding the 4.0 unit limit.")
                return redirect(url_for('enrollment.enroll'))
            # CUSTOM MESSAGE END

            unmet = []
            already_enrolled_in_selection = []
            courses_to_enroll_db_records = []

            for course_code in selected_codes:
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

                is_prereq_met_for_selected = True
                prereq_message = ""

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
                        break

                if is_prereq_met_for_selected and course_info_selected['prereq']:
                    prereq_code = course_info_selected['prereq']
                    if prereq_code not in all_met_courses_for_prereq_check:
                        is_prereq_met_for_selected = False
                        prereq_course_obj = Course.query.get(prereq_code)
                        prereq_display_name = prereq_course_obj.CourseName if prereq_course_obj else prereq_code
                        prereq_message = prereq_display_name

                if course_code in currently_enrolled_course_codes:
                    already_enrolled_in_selection.append(course_info_selected['title'])
                    continue

                if not is_prereq_met_for_selected:
                    unmet.append(f"{course_info_selected['title']} (requires {prereq_message})")
                    continue

                db_course_obj = Course.query.get(course_code)
                if not db_course_obj:
                    logging.warning(f"Course {course_code} from PROGRAM_STRUCTURE not found in DB. Creating a mock Course object for enrollment.")
                    db_course_obj = Course(CourseID=course_code, CourseName=course_info_selected['title'], SubProgramID='SE', PrerequisiteCourseID=course_info_selected['prereq'])
                    db.session.add(db_course_obj)
                
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
                        all_met_courses_for_prereq_check.add(course_to_add.CourseID.split('(')[0].strip())
                        currently_enrolled_course_codes.add(course_to_add.CourseID)

                    except IntegrityError:
                        db.session.rollback()
                        flash(f"Error: Duplicate enrollment or ID conflict for {course_to_add.CourseName}. Please try again.", "error")
                        logging.error(f"IntegrityError during enrollment for {current_user.id} in {course_to_add.CourseID}")
                        return redirect(url_for('enrollment.enroll'))
                    except Exception as e:
                        db.session.rollback()
                        flash(f"An unexpected error occurred during enrollment for {course_to_add.CourseName}.", "error")
                        logging.error(f"Error enrolling student {current_user.id} in course {course_to_add.CourseID}: {e}")
                        return redirect(url_for('enrollment.enroll'))
                
                db.session.commit()
                if newly_enrolled_count > 0:
                    flash(f'Successfully enrolled in {newly_enrolled_count} new course(s)! Please confirm your courses.', 'success')
                return redirect(url_for('enrollment.display_courses'))

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

                    if not year_unlocked:
                        prereq_met = False
                        if year_name == 'Year 2':
                            prereq_display_name = "Completion of Year 1"
                        elif year_name == 'Year 3':
                            prereq_display_name = "Completion of Year 2"
                        elif year_name == 'Year 4':
                            prereq_display_name = "Completion of Year 3"
                    
                    if prereq_met and course_info['prereq']:
                        prereq_code = course_info['prereq']
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
        logging.exception(f"Error in /enroll for student {current_user.id}: {e}")
        db.session.rollback()
        flash("An unexpected error occurred during enrollment. Please try again.", "error")
        return render_template('500.html'), 500

@enrollment_bp.route('/display_courses')
@token_required
def display_courses(current_user):
    # Student role check
    if current_user.role != 'student':
        flash("Unauthorized access. Only students can view their courses.", "error")
        logging.warning(f"Display courses access denied for non-student user '{current_user.username}'.")
        return redirect(url_for('enrollment.dashboard'))
    try:
        enrolled_courses = Enrollment.query.filter_by(StudentID=current_user.id).all() # Load without joinedload here to avoid circularity if Course model is generating dummy data
        
        courses_for_template = []
        all_program_courses = {}
        for year_data in PROGRAM_STRUCTURE.values():
            for semester_data in year_data.values():
                for course_info in semester_data:
                    all_program_courses[course_info['code']] = course_info

        for enrollment in enrolled_courses:
            course_code = enrollment.CourseID
            course_info = all_program_courses.get(course_code)
            if course_info:
                courses_for_template.append({
                    'code': enrollment.CourseID, # Use CourseID directly from enrollment if not loading Course obj
                    'title': course_info['title'],
                    'semester': course_info['semester'],
                    'units': course_info['units']
                })
            else:
                 # If course_info not found in PROGRAM_STRUCTURE, try to get from DB
                 db_course = Course.query.get(course_code)
                 courses_for_template.append({
                    'code': course_code,
                    'title': db_course.CourseName if db_course else f"Unknown Course ({course_code})",
                    'semester': 'Unknown Semester', # Cannot infer from PROGRAM_STRUCTURE
                    'units': getattr(db_course, 'credit_hours', 1.0) # Assume 1.0 or get from DB if available
                })


        logging.info(f"Displaying {len(courses_for_template)} enrolled courses for student '{current_user.username}'.")
        return render_template('display_courses.html', enrolled_courses=courses_for_template)
    except Exception as e:
        logging.exception(f"Error in /display_courses for student {current_user.id}: {e}")
        return render_template('500.html'), 500

@enrollment_bp.route('/drop_course/<course_code>')
@token_required
def drop_course(current_user, course_code):
    # Student role check
    if current_user.role != 'student':
        flash("Unauthorized access. Only students can drop courses.", "error")
        logging.warning(f"Drop course access denied for non-student user '{current_user.username}'.")
        return redirect(url_for('enrollment.dashboard'))
    try:
        enrollment_to_delete = Enrollment.query.filter_by(
            StudentID=current_user.id,
            CourseID=course_code
        ).first()

        if enrollment_to_delete:
            db.session.delete(enrollment_to_delete)
            db.session.commit()
            flash(f'Course {course_code} dropped successfully.', 'success')
            logging.info(f"Student '{current_user.username}' successfully dropped course '{course_code}'.")
        else:
            flash(f'Enrollment for course {course_code} not found.', 'error')
            logging.warning(f"Student '{current_user.username}' attempted to drop non-existent enrollment for course '{course_code}'.")
            
        return redirect(url_for('enrollment.display_courses'))
    except Exception as e:
        db.session.rollback()
        logging.exception(f"Error in /drop_course/{course_code}: {e}")
        flash(f"An error occurred while dropping course {course_code}.", "error")
        return render_template('500.html'), 500

@enrollment_bp.route('/fees')
@token_required
def fees(current_user):
    # Student role check
    if current_user.role != 'student':
        flash("Unauthorized access. Only students can view their fees.", "error")
        logging.warning(f"Fees access denied for non-student user '{current_user.username}'.")
        return redirect(url_for('enrollment.dashboard'))
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


        logging.info(f"Displaying fees for student '{current_user.username}'. Total: ${total_amount:.2f}, Status: {invoice_details['payment_status']}.")
        return render_template(
            'fees.html',
            student=student_details,
            invoice=invoice_details,
            items=invoice_items,
            total=total_amount,
            general_services_fee=general_services_fee
        )
    except Exception as e:
        logging.exception(f"Error in /fees for student {current_user.id}: {e}")
        return render_template('500.html'), 500

@enrollment_bp.route('/download_invoice_pdf')
@token_required
def download_invoice_pdf(current_user):
    # Student role check
    if current_user.role != 'student':
        flash("Unauthorized access. Only students can download invoices.", "error")
        logging.warning(f"Invoice download access denied for non-student user '{current_user.username}'.")
        return redirect(url_for('enrollment.dashboard'))
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
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=inch/2, leftMargin=inch/2,
                                topMargin=inch/2, bottomMargin=inch/2)
        
        styles = getSampleStyleSheet()

        # Custom styles for PDF
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['h1'],
            fontSize=18,
            spaceAfter=14,
            alignment=1 # CENTER
        )
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['h2'],
            fontSize=14,
            spaceAfter=10,
            alignment=1 # CENTER
        )
        section_title_style = ParagraphStyle(
            'SectionTitleStyle',
            parent=styles['h3'],
            fontSize=12,
            spaceBefore=10,
            spaceAfter=6
        )
        normal_style = styles['Normal']
        normal_bold_style = ParagraphStyle(
            'NormalBold',
            parent=normal_style,
            fontName='Helvetica-Bold'
        )

        elements = []

        # University Header
        elements.append(Paragraph("University of the South Pacific", title_style))
        elements.append(Paragraph("Invoice", header_style))
        elements.append(Paragraph("Registrar's Office | Suva, Fiji", normal_style))
        elements.append(Paragraph("Phone: [Your University Phone] | Email: [Your University Email]", normal_style))
        elements.append(Paragraph("Website: [Your University Website]", normal_style))
        elements.append(Spacer(1, 0.2 * inch))

        # Invoice Details
        elements.append(Paragraph("Invoice Details:", section_title_style))
        elements.append(Paragraph(f"<b>Invoice Number:</b> {invoice_details['number']}", normal_style))
        elements.append(Paragraph(f"<b>Date:</b> {invoice_details['date']}", normal_style))
        elements.append(Paragraph(f"<b>Semester:</b> {invoice_details['semester']}", normal_style))
        elements.append(Spacer(1, 0.1 * inch))

        # Student Details
        elements.append(Paragraph("Student Details:", section_title_style))
        elements.append(Paragraph(f"<b>Name:</b> {student_details['name']}", normal_style))
        elements.append(Paragraph(f"<b>Student ID:</b> {student_details['id']}", normal_style))
        elements.append(Spacer(1, 0.2 * inch))

        # Line Items Table
        elements.append(Paragraph("Charges:", section_title_style))
        data = [['Description', 'Amount']]
        for item in invoice_items:
            fee_display = f"${item['fee']:.2f}" if isinstance(item['fee'], (int, float)) else str(item['fee'])
            data.append([f"{item['title']} ({item['code']})", fee_display])
        
        data.append(['General Services Fee', f"${general_services_fee:.2f}"])

        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F2F2F2')), # Header background
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
        
        col_widths = [4.5 * inch, 1.5 * inch] # Adjust column widths as needed
        invoice_table = Table(data, colWidths=col_widths)
        invoice_table.setStyle(table_style)
        elements.append(invoice_table)
        elements.append(Spacer(1, 0.2 * inch))

        # Total and Payment Status
        summary_data = [
            [Paragraph("<b>Total Amount Due:</b>", normal_bold_style), Paragraph(f"${total_amount:.2f}", normal_style)],
            [Paragraph("<b>Payment Status:</b>", normal_bold_style), Paragraph(invoice_details['payment_status'], normal_style)],
        ]
        summary_table_style = TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('GRID', (0,0), (-1,0), 0.5, colors.black), # Added grid for summary header
            ('GRID', (0,1), (-1,-1), 0.5, colors.black), # Added grid for summary data
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EEEEEE')), # Header background
        ])
        summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch])
        summary_table.setStyle(summary_table_style)
        elements.append(summary_table)
        elements.append(Spacer(1, 0.5 * inch))

        # Footer/Disclaimer
        elements.append(Paragraph("This is an official document of the University of the South Pacific. Any alteration or unauthorized duplication of this invoice may result in severe penalties.", normal_style))
        elements.append(Paragraph(f"Document generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
        elements.append(Paragraph("Accounts Department Signature: _________________________<br/><br/>", normal_style))

        doc.build(elements)

        buffer.seek(0)
        response = make_response(buffer.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment;filename=invoice_{student_details['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf'

        logging.info(f"Generated and sent invoice PDF for student '{current_user.username}'.")
        return response

    except Exception as e:
        logging.exception(f"Error in /download_invoice_pdf for student {current_user.id}: {e}")
        flash(f"An error occurred while generating your PDF invoice: {str(e)}", "danger")
        return redirect(url_for('enrollment.fees')) # Redirect back to fees page on error

# --- New Routes: Grade Recheck (Manual Form Handling) ---

# Helper function to generate dummy grades for a student
def generate_dummy_grades_for_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        logging.warning(f"Attempted to generate dummy grades for non-existent student ID: {student_id}")
        return False

    # Check if student already has grades to avoid duplicates for testing
    if Grade.query.filter_by(student_id=student_id).first():
        logging.info(f"Student {student_id} already has grades. Skipping dummy grade generation.")
        return False

    # Dummy courses (must exist in your Course table or PROGRAM_STRUCTURE)
    # Ensure these course IDs actually exist in your database or are handled by mock Course creation.
    dummy_courses = [
        {'id': 'CS111', 'name': 'Introduction to C++ Programming', 'units': 1.0},
        {'id': 'CS112', 'name': 'Data Structures and Algorithms', 'units': 1.0},
        {'id': 'MA111', 'name': 'Calculus and Linear Algebra', 'units': 1.0},
        {'id': 'UU100A', 'name': 'Communications & Info Lit', 'units': 0.5},
        {'id': 'CS140', 'name': 'Intro to Software Engineering', 'units': 1.0},
        {'id': 'ST131', 'name': 'Introduction to Statistics', 'units': 1.0}
    ]

    grades_to_add = []
    grade_options_passing = ['A+', 'A', 'B+', 'B', 'C+', 'C']
    grade_options_failing = ['D', 'E', 'F', 'R'] # Include 'R' (Repeat) as a failing/re-attempt grade
    
    # Ensure at least one failing grade if there are enough courses
    has_failing_grade = False

    for i, course_info in enumerate(dummy_courses):
        course_id = course_info['id']
        # Ensure the course exists in the database. If not, create a placeholder.
        course_obj = Course.query.get(course_id)
        if not course_obj:
            logging.info(f"Course {course_id} from dummy data not found in DB. Creating a mock Course object.")
            course_obj = Course(CourseID=course_id, CourseName=course_info['name'], SubProgramID='GEN', PrerequisiteCourseID=None)
            # Assuming 'credit_hours' is a field on Course model.
            if hasattr(course_obj, 'credit_hours'):
                course_obj.credit_hours = course_info['units']
            db.session.add(course_obj)
            try:
                db.session.commit() # Commit mock course to allow linking
            except IntegrityError:
                db.session.rollback() # Course already exists, ignore
                course_obj = Course.query.get(course_id) # Re-fetch if it already exists

        numerical_grade = random.randint(50, 95) # Default to passing range
        letter_grade = random.choice(grade_options_passing)

        # Logic to ensure at least one failing grade and also include passed grades
        if not has_failing_grade and i == 0: # Make the first course a guaranteed fail for recheck testing
            numerical_grade = random.randint(0, 49)
            letter_grade = random.choice(grade_options_failing)
            has_failing_grade = True
        elif not has_failing_grade and random.random() < 0.2: # 20% chance of a fail for other courses
            numerical_grade = random.randint(0, 49)
            letter_grade = random.choice(grade_options_failing)
            has_failing_grade = True
        
        # Ensure numerical grade aligns with letter grade for realism (optional, but good practice)
        if letter_grade in ['A+', 'A']: numerical_grade = random.randint(90, 100)
        elif letter_grade in ['B+', 'B']: numerical_grade = random.randint(80, 89)
        elif letter_grade in ['C+', 'C']: numerical_grade = random.randint(70, 79)
        elif letter_grade == 'D': numerical_grade = random.randint(50, 59) # D is usually a conditional pass/fail boundary
        elif letter_grade in ['E', 'F', 'R']: numerical_grade = random.randint(0, 49)


        grades_to_add.append(
            Grade(
                student_id=student.StudentID,
                course_id=course_id,
                letter_grade=letter_grade,
                numerical_grade=numerical_grade,
                year=2024 if i % 2 == 0 else 2025, # Alternate years
                semester='Semester 1' if i % 2 == 0 else 'Semester 2' # Alternate semesters
            )
        )
    
    # Final check to ensure at least one failing grade if the random chance didn't hit
    if not has_failing_grade and grades_to_add:
        idx_to_fail = random.randint(0, len(grades_to_add) - 1)
        grades_to_add[idx_to_fail].letter_grade = random.choice(grade_options_failing)
        grades_to_add[idx_to_fail].numerical_grade = random.randint(0, 49)


    for grade in grades_to_add:
        db.session.add(grade)
    try:
        db.session.commit()
        logging.info(f"Successfully generated {len(grades_to_add)} dummy grades for student {student_id}.")
        return True
    except IntegrityError:
        db.session.rollback()
        logging.warning(f"Could not commit dummy grades for {student_id} due to integrity error (e.g., duplicate grade for course).")
        return False
    except Exception as e:
        db.session.rollback()
        logging.exception(f"Failed to generate dummy grades for student {student_id}: {e}")
        return False

# TEMPORARY: Route to generate dummy grades for the current logged-in student
@enrollment_bp.route('/student/generate_grades', methods=['GET'])
@token_required
def generate_grades(current_user):
    if current_user.role != 'student':
        flash("Unauthorized access.", "error")
        return redirect(url_for('enrollment.dashboard'))
    
    success = generate_dummy_grades_for_student(current_user.id)
    if success:
        flash("Dummy grades generated successfully for your account!", "success")
    else:
        flash("Could not generate dummy grades (they might already exist or an error occurred).", "info")
    return redirect(url_for('enrollment.view_transcript'))


@enrollment_bp.route('/student/apply_grade_recheck', methods=['GET', 'POST'])
@token_required
def apply_grade_recheck(current_user):
    # Student role check
    if current_user.role != 'student':
        flash("Unauthorized access. Only students can apply for grade recheck.", "error")
        logging.warning(f"Grade recheck access denied for non-student user '{current_user.username}'.")
        return redirect(url_for('enrollment.dashboard'))

    active_hold = Hold.query.filter_by(StudentID=current_user.id, status='Active').first()
    if active_hold:
        grade_recheck_service = ServiceAccess.query.filter_by(service_name='apply_grade_recheck').first()
        if grade_recheck_service and not grade_recheck_service.is_available_on_hold:
            flash(f"You have an active hold on your account ({active_hold.reason}). Applying for grade recheck is currently restricted. Please resolve your hold.", "error")
            logging.info(f"Grade recheck restricted for student '{current_user.username}' due to active hold: {active_hold.reason}.")
            return redirect(url_for('enrollment.student_hold_status'))

    errors = {}
    current_reason = ""
    current_selected_grade_id = ""

    if request.method == 'POST':
        selected_grade_id_str = request.form.get('course_grade')
        reason = request.form.get('reason')

        current_reason = reason
        current_selected_grade_id = selected_grade_id_str

        # Manual Validation for course_grade
        if not selected_grade_id_str:
            errors['course_grade'] = "Please select a course and grade."
            grade_id = None
        else:
            try:
                grade_id = int(selected_grade_id_str)
                grade_to_recheck = Grade.query.get(grade_id)
                if not grade_to_recheck or str(grade_to_recheck.student_id) != str(current_user.id):
                    errors['course_grade'] = "Invalid course or grade selected."
                    grade_id = None
            except ValueError:
                errors['course_grade'] = "Invalid grade selection."
                grade_id = None

        # Manual Validation for reason
        if not reason:
            errors['reason'] = "Please provide a detailed reason for your recheck request."
        elif not (50 <= len(reason) <= 500):
            errors['reason'] = "Reason must be between 50 and 500 characters."
        
        # If there are no errors yet, check for pending recheck
        if not errors and grade_id is not None:
            existing_recheck = GradeRecheck.query.filter_by(
                student_id=current_user.id,
                grade_id=grade_id,
                status='Pending'
            ).first()

            if existing_recheck:
                flash('A recheck request for this grade is already pending.', 'info')
                logging.info(f"Student '{current_user.username}' attempted to submit duplicate grade recheck for grade ID {grade_id}.")
                return redirect(url_for('enrollment.view_recheck_history'))

        if errors:
            for field, msg in errors.items():
                flash(f"Error in {field.replace('_', ' ').title()}: {msg}", "danger")
            logging.warning(f"Grade recheck submission failed for '{current_user.username}' due to validation errors: {errors}.")
        else:
            try:
                new_recheck = GradeRecheck(
                    student_id=current_user.id,
                    grade_id=grade_to_recheck.id,
                    course_id=grade_to_recheck.course_id,
                    original_grade=grade_to_recheck.letter_grade,
                    reason=reason,
                    status='Pending',
                    date_submitted=datetime.utcnow()
                )
                db.session.add(new_recheck)
                db.session.commit()

                flash('Your grade recheck request has been submitted successfully!', 'success')
                logging.info(f"Student '{current_user.username}' submitted grade recheck request {new_recheck.id} for grade ID {grade_to_recheck.id}.")
                return redirect(url_for('enrollment.grade_check_confirmation', recheck_id=new_recheck.id))

            except Exception as e:
                db.session.rollback()
                logging.exception(f"Error submitting grade recheck for student {current_user.id}: {e}")
                flash(f'An unexpected error occurred while submitting your request. Please try again. Error: {e}', 'danger')

    # For GET request or re-rendering due to errors:
    student_grades = Grade.query.filter_by(student_id=current_user.id).options(joinedload(Grade.course)).order_by(Grade.year.desc(), Grade.semester.desc()).all()
    
    grade_choices_html = [('', '--- Select a Course Grade to Recheck ---')]
    for grade in student_grades:
        if grade.course:
            existing_recheck = GradeRecheck.query.filter_by(grade_id=grade.id, status='Pending').first()
            # Only allow recheck if not already pending. Allow recheck for any grade.
            if not existing_recheck:
                grade_choices_html.append((grade.id, f"{grade.course.CourseID} - {grade.course.CourseName} (Grade: {grade.letter_grade})")) # Use CourseID and CourseName

    return render_template('grade_recheck.html', # Matches your file name
                           grade_choices=grade_choices_html,
                           current_reason=current_reason,
                           current_selected_grade_id=current_selected_grade_id,
                           errors=errors)

@enrollment_bp.route('/student/grade_check_confirmation/<int:recheck_id>')
@token_required
def grade_check_confirmation(current_user, recheck_id):
    # Student role check
    if current_user.role != 'student':
        flash("Unauthorized access.", "error")
        logging.warning(f"Grade recheck confirmation access denied for non-student user '{current_user.username}'.")
        return redirect(url_for('enrollment.dashboard'))

    recheck = GradeRecheck.query.get_or_404(recheck_id)

    if recheck.student_id != current_user.id:
        flash('You do not have permission to view this grade recheck confirmation.', 'danger')
        logging.warning(f"Unauthorized access attempt to grade recheck confirmation {recheck_id} by user '{current_user.username}'.")
        return redirect(url_for('enrollment.dashboard'))

    student_data = Student.query.get(recheck.student_id)
    course_data = Course.query.get(recheck.course_id)

    student_name = f"{student_data.FirstName} {student_data.LastName}" if student_data else current_user.username
    course_name = course_data.CourseName if course_data else "N/A" # Use CourseName
    course_code = course_data.CourseID if course_data else "N/A" # Use CourseID
    
    confirmation_number = recheck.id 
    logging.info(f"Displaying grade recheck confirmation {recheck_id} for student '{current_user.username}'.")
    return render_template('grade_recheck_confirmation.html', # Matches your file name
                           student_name=student_name,
                           course_name=course_name,
                           course_code=course_code,
                           original_grade=recheck.original_grade,
                           recheck_reason=recheck.reason,
                           confirmation_number=confirmation_number)

@enrollment_bp.route('/student/recheck_history')
@token_required
def view_recheck_history(current_user):
    # Student role check
    if current_user.role != 'student':
        flash("Unauthorized access.", "error")
        logging.warning(f"Recheck history access denied for non-student user '{current_user.username}'.")
        return redirect(url_for('enrollment.dashboard'))

    recheck_requests = GradeRecheck.query.filter_by(student_id=current_user.id).options(joinedload(GradeRecheck.course)).order_by(GradeRecheck.date_submitted.desc()).all()
    logging.info(f"Displaying {len(recheck_requests)} grade recheck requests for student '{current_user.username}'.")
    return render_template('view_recheck_history.html', recheck_requests=recheck_requests)

# REMOVED ADMIN ROUTES FOR GRADE RECHECK MANAGEMENT

# --- New Routes: Special Applications (Graduation, Pass, Re-sit) (Manual Form Handling) ---

@enrollment_bp.route('/student/apply_special_application', methods=['GET', 'POST'])
@token_required
def apply_special_application(current_user):
    # Student role check
    if current_user.role != 'student':
        flash("Unauthorized access. Only students can apply for special applications.", "error")
        logging.warning(f"Special application access denied for non-student user '{current_user.username}'.")
        return redirect(url_for('enrollment.dashboard'))

    active_hold = Hold.query.filter_by(StudentID=current_user.id, status='Active').first()
    if active_hold:
        app_grad_service = ServiceAccess.query.filter_by(service_name='apply_graduation').first()
        app_other_pass_resit_service = ServiceAccess.query.filter_by(service_name='apply_grade_recheck').first() # Using recheck as a placeholder
        
        is_restricted = False
        if app_grad_service and not app_grad_service.is_available_on_hold:
            is_restricted = True
        elif app_other_pass_resit_service and not app_other_pass_resit_service.is_available_on_hold:
            is_restricted = True

        if is_restricted:
            flash(f"You have an active hold on your account ({active_hold.reason}). Applying for special applications is currently restricted. Please resolve your hold.", "error")
            logging.info(f"Special application restricted for student '{current_user.username}' due to active hold: {active_hold.reason}.")
            return redirect(url_for('enrollment.student_hold_status'))

    errors = {}
    current_application_type = ""
    current_course_id = ""
    current_reason = ""

    # Populate course choices for pass/re-sit applications (same logic as before)
    current_and_past_courses = []
    enrolled_courses = Enrollment.query.filter_by(StudentID=current_user.id).all() # No joinedload needed here to avoid conflict
    for enrollment in enrolled_courses:
        # Fetch course separately if needed, or rely on course ID if you don't need full object
        db_course = Course.query.get(enrollment.CourseID)
        if db_course:
            current_and_past_courses.append(db_course)

    graded_courses = Grade.query.filter_by(student_id=current_user.id).options(joinedload(Grade.course)).all()
    for grade_record in graded_courses:
        if grade_record.course and grade_record.course not in current_and_past_courses:
            current_and_past_courses.append(grade_record.course)

    unique_courses = {c.CourseID: c for c in current_and_past_courses}.values()
    
    course_choices_html = [('', '--- Select a Course (if applicable) ---')]
    for course in unique_courses:
        course_choices_html.append((course.CourseID, f"{course.CourseID} - {course.CourseName}"))

    if request.method == 'POST':
        application_type = request.form.get('application_type')
        course_id = request.form.get('course')
        reason = request.form.get('reason')

        current_application_type = application_type
        current_course_id = course_id
        current_reason = reason

        # Manual Validation
        if not application_type:
            errors['application_type'] = "Please select an application type."
        
        if application_type != 'Graduation' and not course_id:
            errors['course'] = "Please select a course for this application type."
        elif application_type != 'Graduation' and course_id:
            course_obj = Course.query.get(course_id)
            if not course_obj or course_obj.CourseID not in [c[0] for c in course_choices_html if c[0]]:
                errors['course'] = "Invalid course selected."

        if not reason:
            errors['reason'] = "Please provide a reason for your application."
        elif not (50 <= len(reason) <= 1000):
            errors['reason'] = "Reason must be between 50 and 1000 characters."
        
        if application_type == 'Graduation' and not errors:
            pass # Placeholder for actual graduation eligibility check

        if errors:
            for field, msg in errors.items():
                flash(f"Error in {field.replace('_', ' ').title()}: {msg}", "danger")
            logging.warning(f"Special application submission failed for '{current_user.username}' due to validation errors: {errors}.")
        else:
            try:
                new_application = SpecialApplication(
                    student_id=current_user.id,
                    application_type=application_type,
                    course_id=course_id if application_type != 'Graduation' else None,
                    reason=reason,
                    status='Pending',
                    date_submitted=datetime.utcnow(),
                    external_form_path=None
                )
                db.session.add(new_application)
                db.session.commit()

                flash('Your application has been successfully submitted!', 'success')
                logging.info(f"Student '{current_user.username}' submitted special application {new_application.id} of type '{application_type}'.")
                return redirect(url_for('enrollment.special_application_confirmation', application_id=new_application.id))

            except Exception as e:
                db.session.rollback()
                logging.exception(f"Error submitting special application for student {current_user.id}: {e}")
                flash(f'An unexpected error occurred while submitting your application. Please try again. Error: {e}', 'danger')

    # For GET request or re-rendering due to errors:
    # FIX: Corrected template name from 'apply_sepcial_application.html' to 'apply_special_application.html'
    return render_template('apply_special_application.html',
                           application_type_choices=[
                               ('', '--- Select an Application Type ---'),
                               ('Graduation', 'Application for Graduation'),
                               ('Compassionate Pass', 'Application for Compassionate Pass'),
                               ('Aegrotat Pass', 'Application for Aegrotat Pass'),
                               ('Re-sit', 'Application for Course Re-sit')
                           ],
                           course_choices=course_choices_html,
                           current_application_type=current_application_type,
                           current_course_id=current_course_id,
                           current_reason=current_reason,
                           errors=errors)


@enrollment_bp.route('/student/special_application_confirmation/<int:application_id>')
@token_required
def special_application_confirmation(current_user, application_id):
    # Student role check
    if current_user.role != 'student':
        flash("Unauthorized access.", "error")
        logging.warning(f"Special application confirmation access denied for non-student user '{current_user.username}'.")
        return redirect(url_for('enrollment.dashboard'))

    application = SpecialApplication.query.get_or_404(application_id)

    if application.student_id != current_user.id:
        flash('You do not have permission to view this application confirmation.', 'danger')
        logging.warning(f"Unauthorized access attempt to special application confirmation {application_id} by user '{current_user.username}'.")
        return redirect(url_for('enrollment.dashboard'))

    if application.course_id:
        # Using Course.query.get() instead of assuming application.course is loaded
        application.course = Course.query.get(application.course_id) 
    
    logging.info(f"Displaying special application confirmation {application_id} for student '{current_user.username}'.")
    return render_template('special_application_confirmation.html', application=application)

@enrollment_bp.route('/student/applications_history')
@token_required
def view_special_applications_history(current_user):
    # Student role check
    if current_user.role != 'student':
        flash("Unauthorized access.", "error")
        logging.warning(f"Special applications history access denied for non-student user '{current_user.username}'.")
        return redirect(url_for('enrollment.dashboard'))
    
    applications = SpecialApplication.query.filter_by(student_id=current_user.id).options(joinedload(SpecialApplication.course)).order_by(SpecialApplication.date_submitted.desc()).all()
    logging.info(f"Displaying {len(applications)} special applications for student '{current_user.username}'.")
    return render_template('view_special_applications_history.html', applications=applications)

# REMOVED ADMIN ROUTES FOR SPECIAL APPLICATION MANAGEMENT

# --- New Routes: Student Hold Status ---

@enrollment_bp.route('/student/hold_status')
@token_required
def student_hold_status(current_user):
    # Student role check
    if current_user.role != 'student':
        flash("Unauthorized access.", "error")
        logging.warning(f"Hold status access denied for non-student user '{current_user.username}'.")
        return redirect(url_for('enrollment.dashboard'))

    active_hold = Hold.query.filter_by(
        StudentID=current_user.id,
        status='Active'
    ).first()

    restricted_services = []
    if active_hold:
        restricted_services = ServiceAccess.query.filter_by(is_available_on_hold=False).all()
        
        if active_hold.imposed_by_user_id:
            active_hold.imposed_by_user = User.query.get(active_hold.imposed_by_user_id)
    
    logging.info(f"Displaying hold status for student '{current_user.username}'. Active hold: {bool(active_hold)}.")
    return render_template('student_hold_status.html',
                           hold_status=active_hold,
                           restricted_services=restricted_services)

# REMOVED ADMIN ROUTES FOR MANAGE STUDENT HOLDS AND SERVICE ACCESS

# --- New Routes: Academic Transcript ---

# Helper function to convert letter grade to GPA points
def convert_grade_to_gpa_points(letter_grade):
    """Simple mapping for GPA calculation based on new grading scale."""
    gpa_map = {
        'A+': 4.5, 'A': 4.0,
        'B+': 3.5, 'B': 3.0,
        'C+': 2.5, 'C': 2.0,
        'R': 1.5,
        'D': 1.0, 'DX': 1.0,
        'E': 0.0, 'EX': 0.0,
        'F': 0.0,
        'W': 0.0, 'P': 0.0, 'CR': 0.0,
        'S': 0.0, 'U': 0.0, 'AUD': 0.0,
        'I': 0.0, 'AEG': 0.0, 'CMP': 0.0
    }
    return gpa_map.get(letter_grade.upper(), 0.0)

def get_student_academic_data(student_id):
    """
    Fetches all necessary data for the academic transcript of a given student.
    Includes student details, program, and all completed grades with GPA calculation.
    """
    student = Student.query.get(student_id)
    if not student:
        logging.warning(f"Student with ID {student_id} not found for academic data retrieval.")
        return None

    grades = Grade.query.filter_by(student_id=student_id).options(joinedload(Grade.course)).order_by(Grade.year, Grade.semester).all()

    total_grade_points_sum = 0.0
    total_gpa_credit_hours_sum = 0.0
    transcript_courses = []

    for grade_record in grades:
        course = grade_record.course
        if course:
            gpa_points = convert_grade_to_gpa_points(grade_record.letter_grade)
            
            credit_hours_for_gpa = 0.0
            # Only count credit hours for GPA if the grade is a standard graded one
            # and not a withdrawal, pass/fail, audit, incomplete, or certain non-GPA grades
            if grade_record.letter_grade.upper() not in ['W', 'P', 'CR', 'S', 'U', 'AUD', 'I', 'AEG', 'CMP']:
                 # Assuming 'credit_hours' attribute exists on the Course model
                # Use getattr with a default of 1.0 if 'credit_hours' is missing
                credit_hours_for_gpa = getattr(course, 'credit_hours', 1.0) 

            total_grade_points_sum += (gpa_points * credit_hours_for_gpa)
            total_gpa_credit_hours_sum += credit_hours_for_gpa

            transcript_courses.append({
                'year': grade_record.year,
                'semester': grade_record.semester,
                'course_code': course.CourseID,
                'course_name': course.CourseName,
                'credit_hours': getattr(course, 'credit_hours', 1.0), # Default to 1.0 if not found
                'letter_grade': grade_record.letter_grade,
                'gpa_points_earned': gpa_points * credit_hours_for_gpa
            })
        else:
            logging.warning(f"Course not found for grade record ID {grade_record.id} (CourseID: {grade_record.course_id}). Skipping for transcript.")


    cumulative_gpa = total_grade_points_sum / total_gpa_credit_hours_sum if total_gpa_credit_hours_sum > 0 else 0.0

    # Total credits earned should only count successfully completed courses (passing grades)
    total_credits_earned = sum(course['credit_hours'] for course in transcript_courses if course['letter_grade'].upper() not in ['F', 'E', 'EX', 'W', 'U', 'AUD', 'I', 'R', 'D', 'DX'])

    program_name = student.program_obj.ProgramName if student.program_obj else "N/A"
    subprogram_name = student.subprogram_obj.SubProgramName if student.subprogram_obj else "N/A"

    logging.debug(f"Academic data fetched for student {student_id}: GPA={cumulative_gpa:.2f}, Credits={total_credits_earned}.")
    return {
        'student_full_name': f"{student.FirstName} {student.LastName}",
        'student_id_number': student.StudentID,
        'date_of_birth': student.DateOfBirth.strftime('%Y-%m-%d') if student.DateOfBirth else 'N/A',
        'program_enrolled': f"{program_name} - {subprogram_name}",
        'date_generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'cumulative_gpa': f"{cumulative_gpa:.2f}",
        'total_credits_earned': total_credits_earned,
        'courses': transcript_courses
    }

@enrollment_bp.route('/student/view_transcript', methods=['GET'])
@token_required
def view_transcript(current_user):
    # Student role check
    if current_user.role != 'student':
        flash("Unauthorized access. Only students can view their transcript.", "error")
        logging.warning(f"Transcript view access denied for non-student user '{current_user.username}'.")
        return redirect(url_for('enrollment.dashboard'))

    active_hold = Hold.query.filter_by(StudentID=current_user.id, status='Active').first()
    if active_hold:
        view_grades_service = ServiceAccess.query.filter_by(service_name='view_course_grades').first()
        if view_grades_service and not view_grades_service.is_available_on_hold:
            flash(f"You have an active hold on your account ({active_hold.reason}). Viewing your academic transcript is currently restricted. Please resolve your hold.", "error")
            logging.info(f"Transcript view restricted for student '{current_user.username}' due to active hold: {active_hold.reason}.")
            return redirect(url_for('enrollment.student_hold_status'))

    logging.info(f"Rendering transcript view for student '{current_user.username}'.")
    return render_template('view_transcript.html')

@enrollment_bp.route('/student/download_transcript_pdf', methods=['GET'])
@token_required
def download_transcript_pdf(current_user):
    # Student role check
    if current_user.role != 'student':
        flash("Unauthorized access.", "error")
        logging.warning(f"Transcript download access denied for non-student user '{current_user.username}'.")
        return redirect(url_for('enrollment.dashboard'))

    active_hold = Hold.query.filter_by(StudentID=current_user.id, status='Active').first()
    if active_hold:
        view_grades_service = ServiceAccess.query.filter_by(service_name='view_course_grades').first()
        if view_grades_service and not view_grades_service.is_available_on_hold:
            flash(f"Your academic transcript download is currently restricted due to an active hold ({active_hold.reason}). Please resolve your hold.", "error")
            logging.info(f"Transcript download restricted for student '{current_user.username}' due to active hold: {active_hold.reason}.")
            return redirect(url_for('enrollment.student_hold_status'))

    student_data = get_student_academic_data(current_user.id)

    if not student_data:
        flash("Could not retrieve your academic record for transcript generation. Please contact administration.", "danger")
        logging.error(f"Failed to retrieve academic data for student {current_user.id} for transcript generation.")
        return redirect(url_for('enrollment.view_transcript'))

    # --- ReportLab PDF Generation Logic ---
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=inch/2, leftMargin=inch/2,
                            topMargin=inch/2, bottomMargin=inch/2)
    
    styles = getSampleStyleSheet()
    elements = []

    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['h1'],
        fontSize=18,
        spaceAfter=14,
        alignment=1 # CENTER
    )
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['h2'],
        fontSize=14,
        spaceAfter=10,
        alignment=1 # CENTER
    )
    section_title_style = ParagraphStyle(
        'SectionTitleStyle',
        parent=styles['h3'],
        fontSize=12,
        spaceBefore=10,
        spaceAfter=6
    )
    normal_style = styles['Normal']
    normal_bold_style = ParagraphStyle(
        'NormalBold',
        parent=normal_style,
        fontName='Helvetica-Bold'
    )

    # University Header
    elements.append(Paragraph("UNIVERSITY OF THE SOUTH PACIFIC", title_style))
    elements.append(Paragraph("Official Academic Transcript", header_style))
    elements.append(Paragraph("Registrar's Office | Suva, Fiji", normal_style))
    elements.append(Paragraph("Phone: [Your University Phone] | Email: [Your University Email]", normal_style))
    elements.append(Paragraph("Website: [Your University Website]", normal_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Student Information
    elements.append(Paragraph("Student Information:", section_title_style))
    elements.append(Paragraph(f"<b>Name:</b> {student_data['student_full_name']}", normal_style))
    elements.append(Paragraph(f"<b>Student ID:</b> {student_data['student_id_number']}", normal_style))
    elements.append(Paragraph(f"<b>Date of Birth:</b> {student_data['date_of_birth']}", normal_style))
    elements.append(Paragraph(f"<b>Program Enrolled:</b> {student_data['program_enrolled']}", normal_style))
    elements.append(Paragraph(f"<b>Date Generated:</b> {student_data['date_generated']}", normal_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Academic Record Table
    elements.append(Paragraph("Academic Record:", section_title_style))
    table_data = [
        ['Year', 'Sem', 'Course Code', 'Course Name', 'Credits', 'Grade', 'GPA Points']
    ]

    for course in student_data['courses']:
        table_data.append([
            str(course['year']),
            str(course['semester']),
            course['course_code'],
            course['course_name'],
            str(course['credit_hours']),
            course['letter_grade'],
            f"{course['gpa_points_earned']:.2f}"
        ])

    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F2F2F2')), # Header background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])

    col_widths = [
        0.7 * inch, # Year
        0.5 * inch, # Sem
        1.0 * inch, # Course Code
        2.5 * inch, # Course Name
        0.7 * inch, # Credits
        0.7 * inch, # Grade
        0.8 * inch  # GPA Points
    ]
    
    academic_table = Table(table_data, colWidths=col_widths)
    academic_table.setStyle(table_style)
    elements.append(academic_table)
    elements.append(Spacer(1, 0.2 * inch))

    # Summary Information
    elements.append(Paragraph("Summary:", section_title_style))
    summary_data = [
        [Paragraph("<b>Cumulative GPA:</b>", normal_bold_style), Paragraph(f"{student_data['cumulative_gpa']}", normal_style)],
        [Paragraph("<b>Total Credits Earned:</b>", normal_bold_style), Paragraph(f"{student_data['total_credits_earned']}", normal_style)],
    ]
    summary_table_style = TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,0), 0.5, colors.black), # Added grid for summary header
        ('GRID', (0,1), (-1,-1), 0.5, colors.black), # Added grid for summary data
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EEEEEE')), # Header background
    ])
    summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch])
    summary_table.setStyle(summary_table_style)
    elements.append(summary_table)
    elements.append(Spacer(1, 0.5 * inch))

    # Footer/Disclaimer
    elements.append(Paragraph("This is an official document of the University of the South Pacific. Any alteration or unauthorized duplication of this transcript may result in severe penalties.", normal_style))
    elements.append(Paragraph(f"Document generated on: {student_data['date_generated']}", normal_style))
    elements.append(Paragraph("Registrar's Signature: _________________________<br/><br/>", normal_style))

    try:
        doc.build(elements)
        pdf_file = buffer.getvalue()
        buffer.close()

        response = make_response(pdf_file)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment;filename=Academic_Transcript_{student_data["student_id_number"]}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf'

        logging.info(f"Generated and sent transcript PDF for student '{current_user.username}'.")
        return response
    except Exception as e:
        logging.exception(f"Error generating PDF transcript for student {current_user.id} with ReportLab: {e}")
        flash(f"An error occurred while generating your PDF transcript: {str(e)}", "danger")
        return redirect(url_for('enrollment.view_transcript'))


# --- API Endpoints for listing data ---
# These are added to fix the BuildError in dashboard.html
@enrollment_bp.route('/api/courses', methods=['GET'])
@token_required
def get_courses_api(current_user):
    """API endpoint to list all courses."""
    try:
        courses = Course.query.all()
        # Ensure serialize_course can handle Course objects even if not fully linked
        return jsonify([{'CourseID': c.CourseID, 'CourseName': c.CourseName} for c in courses]), 200
    except Exception as e:
        logging.exception("Error fetching courses via API:")
        return jsonify({"message": f"Error fetching courses: {str(e)}"}), 500

@enrollment_bp.route('/api/students', methods=['GET'])
@token_required
def get_students_api(current_user):
    """API endpoint to list all students."""
    try:
        students = Student.query.all()
        return jsonify([{'StudentID': s.StudentID, 'FirstName': s.FirstName, 'LastName': s.LastName} for s in students]), 200
    except Exception as e:
        logging.exception("Error fetching students via API:")
        return jsonify({"message": f"Error fetching students: {str(e)}"}), 500

@enrollment_bp.route('/api/enrollments', methods=['GET'])
@token_required
def get_enrollments_api(current_user):
    """API endpoint to list all enrollments."""
    try:
        enrollments = Enrollment.query.all() # Avoid joinedload for API simplicity unless fully serialized
        return jsonify([{'EnrollmentID': e.EnrollmentID, 'StudentID': e.StudentID, 'CourseID': e.CourseID} for e in enrollments]), 200
    except Exception as e:
        logging.exception("Error fetching enrollments via API:")
        return jsonify({"message": f"Error fetching enrollments: {str(e)}"}), 500


# --- Error Handler (kept for completeness) ---
@enrollment_bp.errorhandler(404)
def page_not_found(e):
    logging.warning(f"404 Not Found: {request.url}")
    return render_template('404.html'), 404