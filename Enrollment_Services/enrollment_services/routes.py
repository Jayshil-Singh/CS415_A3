# enrollment_services/routes.py
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session, send_file, make_response
import logging
from io import BytesIO # For in-memory PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import datetime
from sqlalchemy.exc import IntegrityError, InvalidRequestError # Ensure InvalidRequestError is imported
from sqlalchemy.orm import joinedload # For eager loading relationships
import jwt # For JSON Web Tokens
from functools import wraps # For creating decorators
from flask import current_app # Import current_app for accessing app.config in decorators/endpoints

# Import db and models from your package.
from .db import db
from .model import (
    Program, SubProgram, Semester, Course, CourseAvailability,
    Student, StudentLevel, Hold,
    Enrollment, CourseFee, StudentCourseFee,
    User # Import the new User model for authentication
)

# --- Blueprint Initialization ---
# Create a Blueprint for all enrollment service routes.
enrollment_bp = Blueprint('enrollment', __name__, template_folder='templates')

# --- Logging Setup ---
logging.basicConfig(level=logging.ERROR)

# --- Mock Data (IMPORTANT: To be Replaced with Actual Database Interactions) ---
# These are placeholders for data that should eventually come from your database.

student_completed_courses = {'CS111'} # Example of courses completed by a student

def get_mock_courses_data():
    """
    Simulates fetching course data from the database.
    Replace with actual database queries from the Course model.
    """
    return [
        {
            'code': 'CS111',
            'title': 'Introduction to Computing',
            'description': 'Fundamentals of computer science and programming.',
            'prerequisites': set(),
            'credits': 3,
            'fee_per_credit': 50.00
        },
        {
            'code': 'CS112',
            'title': 'Data Structures and Algorithms',
            'description': 'Essential data structures and algorithm analysis.',
            'prerequisites': {'CS111'},
            'credits': 3,
            'fee_per_credit': 50.00
        },
        {
            'code': 'CS241',
            'title': 'Operating Systems',
            'description': 'Principles of modern operating systems.',
            'prerequisites': {'CS112'},
            'credits': 3,
            'fee_per_credit': 50.00
        },
        {
            'code': 'MA101',
            'title': 'Calculus I',
            'description': 'Introduction to differential and integral calculus.',
            'prerequisites': set(),
            'credits': 4,
            'fee_per_credit': 50.00
        }
    ]

# Mock student and invoice details
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

# --- Helper Functions for Data Processing and Serialization ---

def calculate_invoice(enrolled_courses_codes):
    """Calculates the invoice details for the given course codes."""
    invoice_items = []
    total_amount = 0
    courses_data = get_mock_courses_data()
    for course_code in enrolled_courses_codes:
        course = next((c for c in courses_data if c['code'] == course_code), None)
        if course:
            subtotal = course['credits'] * course['fee_per_credit']
            invoice_items.append({
                'code': course['code'],
                'title': course['title'],
                'credits': course['credits'],
                'fee_per_credit': course['fee_per_credit'],
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
        "Email": student.Email,
    }

def serialize_student_level(student_level):
    return {
        "StudentLevelID": student_level.StudentLevelID,
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
# enrollment_services/routes.py (update this function)

def token_required(f):
    """
    Decorator to protect routes that require a valid JWT.
    It checks for token in Flask session (for HTML pages) or Authorization header (for API calls).
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # 1. Try to get token from Flask session (for HTML page loads)
        if 'jwt_token' in session:
            token = session['jwt_token']
        # 2. If not in session, try to get from Authorization header (for API calls)
        elif 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if len(auth_header.split(" ")) == 2 and auth_header.split(" ")[0].lower() == 'bearer':
                token = auth_header.split(" ")[1]

        if not token:
            # If no token is found in session or header, redirect to login for HTML requests
            # Or return JSON error for API requests
            if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
                flash("Authentication required to access this page.", "error")
                return redirect(url_for('login_page')) # Redirect to the app's login page
            else: # Assume it's an API request expecting JSON
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

# ... (rest of your routes.py code, all other routes remain as they were in the previous parts) ...


@enrollment_bp.route('/auth/login', methods=['POST'])
def login():
    """
    Handles user login, authenticates credentials, and issues a JWT.
    Expects JSON input: {"username": "...", "password": "..."}
    """
    data = request.json
    if not data or not 'username' in data or not 'password' in data:
        return jsonify({'message': 'Missing username or password'}), 400

    user = User.query.filter_by(username=data['username']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401

    # If credentials are valid, generate a JWT
    token_payload = {
        'user_id': user.id,
        'username': user.username,
        'role': user.role,
        'exp': datetime.utcnow() + current_app.config['JWT_EXPIRATION_DELTA']
    }
    token = jwt.encode(token_payload, current_app.config['JWT_SECRET_KEY'], algorithm="HS256")

    # Store token in Flask session upon successful login (for HTML route authentication check)
    session['jwt_token'] = token

    return jsonify({'message': 'Login successful', 'token': token, 'user': {'id': user.id, 'username': user.username, 'role': user.role}}), 200

@enrollment_bp.route('/auth/verify_token', methods=['GET'])
@token_required # Protect this endpoint itself for demonstration
def verify_token(current_user):
    """
    Verifies the provided JWT and returns user information.
    Accessible only with a valid token.
    """
    # If the decorator passed, the token is valid and current_user is set
    return jsonify({
        'message': 'Token is valid',
        'user_id': current_user.id,
        'username': current_user.username,
        'role': current_user.role
    }), 200
# enrollment_services/routes.py (add this in the authentication section)

@enrollment_bp.route('/auth/set_session_token', methods=['POST'])
def set_session_token():
    """
    Receives a JWT from the client and stores it in the Flask session.
    This is used to bridge client-side localStorage/cookies with server-side session
    for HTML page authentication checks.
    """
    data = request.json
    token = data.get('token')

    if token:
        # Optionally, you could decode and validate the token here again,
        # but for this flow, we assume it's just received from a successful login
        # and its validation will happen on actual protected routes.
        session['jwt_token'] = token
        return jsonify({'message': 'Token set in session successfully'}), 200
    else:
        return jsonify({'message': 'No token provided'}), 400

# ... (rest of your routes.py code) ...
# enrollment_services/routes.py (continued from Part 2)

# --- Frontend-facing Routes (HTML Rendering) ---
# These routes handle displaying HTML pages and simple user interactions that might
# involve session data. They will be prefixed by the blueprint's url_prefix (e.g., /enrollment_services/)
# when registered in run_es.py.
# All these routes are now protected by the token_required decorator.

@enrollment_bp.route('/')
@enrollment_bp.route('/dashboard')
@token_required # Protect the dashboard route
def dashboard(current_user): # Add current_user parameter to receive user info from decorator
    """Renders the dashboard page. Requires authentication."""
    # You can now use current_user.username, current_user.role etc. in your dashboard.html template
    # Example: return render_template('dashboard.html', user=current_user)
    return render_template('dashboard.html')

@enrollment_bp.route('/enroll', methods=['GET', 'POST'])
@token_required # Protect the enroll route
def enroll(current_user): # Add current_user parameter
    """Handles course enrollment. Requires authentication."""
    try:
        # Fetch courses from mock data (To be replaced with DB queries from Course model)
        courses_data = get_mock_courses_data()

        if 'enrolled_courses' not in session:
            session['enrolled_courses'] = []

        if request.method == 'POST':
            selected_codes = request.form.getlist('courses')
            if len(selected_codes) > 4:
                flash('You can select a maximum of 4 courses.', 'error')
                return redirect(url_for('enrollment.enroll'))

            unmet = []
            for course_mock in courses_data:
                if course_mock['code'] in selected_codes:
                    if not course_mock['prerequisites'].issubset(student_completed_courses.union(session['enrolled_courses'])):
                        unmet.append(course_mock['code'])

            if unmet:
                flash(f"Cannot enroll in: {', '.join(unmet)} due to unmet prerequisites.", 'error')
            else:
                newly_enrolled = [c for c in selected_codes if c not in session['enrolled_courses']]
                session['enrolled_courses'].extend(newly_enrolled)
                session.modified = True
                flash('Enrollment successful! Please confirm your courses.', 'success')
                return redirect(url_for('enrollment.display_courses'))

        for course_mock in courses_data:
            course_mock['prereq_met'] = course_mock['prerequisites'].issubset(student_completed_courses)

        return render_template('enroll.html', courses=courses_data)
    except Exception as e:
        logging.error(f"Error in /enroll: {e}")
        return render_template('500.html'), 500

@enrollment_bp.route('/display_courses')
@token_required # Protect the display_courses route
def display_courses(current_user): # Add current_user parameter
    """Displays the courses currently selected/enrolled by the student (from session). Requires authentication."""
    try:
        courses_data = get_mock_courses_data()
        enrolled_courses_codes = session.get('enrolled_courses', [])
        enrolled_courses = [course_mock for course_mock in courses_data if course_mock['code'] in enrolled_courses_codes]
        return render_template('display_courses.html', enrolled_courses=enrolled_courses)
    except Exception as e:
        logging.error(f"Error in /display_courses: {e}")
        return render_template('500.html'), 500

@enrollment_bp.route('/drop_course/<course_code>')
@token_required # Protect the drop_course route
def drop_course(current_user, course_code): # Add current_user parameter
    """Allows a student to drop a course from their current session enrollment. Requires authentication."""
    try:
        if 'enrolled_courses' in session:
            session['enrolled_courses'] = [code for code in session['enrolled_courses'] if code != course_code]
            session.modified = True
            flash(f'Course {course_code} dropped successfully.', 'success')
        return redirect(url_for('enrollment.display_courses'))
    except Exception as e:
        logging.error(f"Error in /drop_course/{course_code}: {e}")
        return render_template('500.html'), 500

@enrollment_bp.route('/fees')
@token_required # Protect the fees route
def fees(current_user): # Add current_user parameter
    """Renders the fees overview page, showing calculated invoice details. Requires authentication."""
    try:
        enrolled_courses_codes = session.get('enrolled_courses', [])
        invoice_items, total_amount = calculate_invoice(enrolled_courses_codes)
        return render_template(
            'fees.html',
            student=student_details,
            invoice=invoice_details,
            items=invoice_items,
            total=total_amount
        )
    except Exception as e:
        logging.error(f"Error in /fees: {e}")
        return render_template('500.html'), 500

@enrollment_bp.route('/download_invoice_pdf')
@token_required # Protect the download_invoice_pdf route
def download_invoice_pdf(current_user): # Add current_user parameter
    """Generates and provides a PDF download of the invoice. Requires authentication."""
    try:
        enrolled_courses_codes = session.get('enrolled_courses', [])
        invoice_items, total_amount = calculate_invoice(enrolled_courses_codes)

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Build PDF content
        elements.append(Paragraph("Invoice", styles['h1']))
        elements.append(Paragraph("University of the South Pacific", styles['h2']))
        elements.append(Paragraph(f"Invoice Number: {invoice_details['number']}", styles['Normal']))
        elements.append(Paragraph(f"Date: {invoice_details['date']}", styles['Normal']))
        elements.append(Paragraph(f"Semester: {invoice_details['semester']}", styles['Normal']))

        elements.append(Paragraph("Student Details", styles['h3']))
        elements.append(Paragraph(f"Name: {student_details['name']}", styles['Normal']))
        elements.append(Paragraph(f"ID: {student_details['id']}", styles['Normal']))

        data = [['Course Code', 'Course Title', 'Credits', 'Fee per Credit', 'Subtotal']]
        for item in invoice_items:
            data.append([item['code'], item['title'], item['credits'], f"${item['fee_per_credit']:.2f}",
                         f"${item['subtotal']:.2f}"])
        data.append(['', '', '', 'Total:', f"${total_amount:.2f}"])

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

# Error handler for any 404 Not Found errors within this blueprint
@enrollment_bp.errorhandler(404)
def page_not_found(e):
    """Custom 404 error handler for blueprint routes."""
    # This error handler does not take current_user as it's for 404s,
    # which can happen before or after authentication.
    return render_template('404.html'), 404


# enrollment_services/routes.py (continued from Part 3)

# --- API Endpoints (JSON Responses) ---
# These routes provide data for your frontend or other services.
# They are prefixed by the blueprint's url_prefix and are now protected by token_required.

# Program Endpoints
@enrollment_bp.route('/programs', methods=['GET'])
@token_required # Protect this route
def get_programs(current_user): # Add current_user parameter
    """Retrieves all programs from the database. Requires authentication."""
    # Example: You can implement role-based access control here if needed
    # if current_user.role not in ['admin', 'sas_manager']:
    #     return jsonify({'message': 'Unauthorized: Access restricted'}), 403
    programs = Program.query.all()
    return jsonify([serialize_program(p) for p in programs])

@enrollment_bp.route('/programs/<string:program_id>', methods=['GET'])
@token_required # Protect this route
def get_program(current_user, program_id): # Add current_user parameter
    """Retrieves a single program by its ID. Requires authentication."""
    program = Program.query.get(program_id)
    if not program:
        return jsonify({"message": "Program not found"}), 404
    return jsonify(serialize_program(program))

@enrollment_bp.route('/programs', methods=['POST'])
@token_required # Protect this route
def add_program(current_user): # Add current_user parameter
    """Adds a new program to the database. Requires authentication."""
    # Example: Only admins can add programs
    if current_user.role != 'admin':
        return jsonify({'message': 'Unauthorized: Only administrators can add programs'}), 403

    data = request.json
    if not data or not all(k in data for k in ['ProgramID', 'ProgramName', 'SubProgramID']):
        return jsonify({"message": "Missing program data (requires ProgramID, ProgramName, SubProgramID)"}), 400

    new_program = Program(
        ProgramID=data['ProgramID'],
        ProgramName=data['ProgramName'],
        SubProgramID=data['SubProgramID'] # Assuming this is part of the composite PK or a FK
    )
    db.session.add(new_program)
    try:
        db.session.commit()
        return jsonify({"message": "Program added successfully", "program_id": new_program.ProgramID}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Program with this ID already exists"}), 409
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding program: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/programs/<string:program_id>', methods=['PUT'])
@token_required # Protect this route
def update_program(current_user, program_id): # Add current_user parameter
    """Updates an existing program by its ID. Requires authentication."""
    if current_user.role != 'admin':
        return jsonify({'message': 'Unauthorized: Only administrators can update programs'}), 403

    program = Program.query.get(program_id)
    if not program:
        return jsonify({"message": "Program not found"}), 404

    data = request.json
    if not data:
        return jsonify({"message": "No data provided for update"}), 400

    if 'ProgramName' in data:
        program.ProgramName = data['ProgramName']
    if 'SubProgramID' in data:
        subprogram_exists = SubProgram.query.get(data['SubProgramID'])
        if not subprogram_exists:
            return jsonify({"message": "SubProgramID for update does not exist"}), 404
        program.SubProgramID = data['SubProgramID']

    try:
        db.session.commit()
        return jsonify({"message": "Program updated successfully", "program_id": program.ProgramID}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating program: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/programs/<string:program_id>', methods=['DELETE'])
@token_required # Protect this route
def delete_program(current_user, program_id): # Add current_user parameter
    """Deletes a program by its ID. Requires authentication."""
    if current_user.role != 'admin':
        return jsonify({'message': 'Unauthorized: Only administrators can delete programs'}), 403

    program = Program.query.get(program_id)
    if not program:
        return jsonify({"message": "Program not found"}), 404

    db.session.delete(program)
    try:
        db.session.commit()
        return jsonify({"message": "Program deleted successfully"}), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Cannot delete program; related SubPrograms exist. Delete them first."}), 409
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting program: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500


# SubProgram Endpoints
@enrollment_bp.route('/subprograms', methods=['GET'])
@token_required # Protect this route
def get_subprograms(current_user): # Add current_user parameter
    """Retrieves all subprograms from the database. Requires authentication."""
    subprograms = SubProgram.query.all()
    return jsonify([serialize_subprogram(s) for s in subprograms])

@enrollment_bp.route('/subprograms/<string:subprogram_id>', methods=['GET'])
@token_required # Protect this route
def get_subprogram(current_user, subprogram_id): # Add current_user parameter
    """Retrieves a single subprogram by its ID. Requires authentication."""
    subprogram = SubProgram.query.get(subprogram_id)
    if not subprogram:
        return jsonify({"message": "SubProgram not found"}), 404
    return jsonify(serialize_subprogram(subprogram))

@enrollment_bp.route('/subprograms', methods=['POST'])
@token_required # Protect this route
def add_subprogram(current_user): # Add current_user parameter
    """Adds a new subprogram to the database. Requires authentication."""
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators or SAS managers can add subprograms'}), 403

    data = request.json
    if not data or not all(k in data for k in ['SubProgramID', 'SubProgramName', 'ProgramID']):
        return jsonify({"message": "Missing subprogram data (requires SubProgramID, SubProgramName, ProgramID)"}), 400

    program = Program.query.get(data['ProgramID'])
    if not program:
        return jsonify({"message": "Parent ProgramID does not exist"}), 404

    new_subprogram = SubProgram(
        SubProgramID=data['SubProgramID'],
        SubProgramName=data['SubProgramName'],
        SubProgramType=data.get('SubProgramType'),
        ProgramID=data['ProgramID']
    )
    db.session.add(new_subprogram)
    try:
        db.session.commit()
        return jsonify({"message": "SubProgram added successfully", "subprogram_id": new_subprogram.SubProgramID}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "SubProgram with this ID already exists"}), 409
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding subprogram: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/subprograms/<string:subprogram_id>', methods=['PUT'])
@token_required # Protect this route
def update_subprogram(current_user, subprogram_id): # Add current_user parameter
    """Updates an existing subprogram by its ID. Requires authentication."""
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators or SAS managers can update subprograms'}), 403

    subprogram = SubProgram.query.get(subprogram_id)
    if not subprogram:
        return jsonify({"message": "SubProgram not found"}), 404

    data = request.json
    if not data:
        return jsonify({"message": "No data provided for update"}), 400

    if 'SubProgramName' in data:
        subprogram.SubProgramName = data['SubProgramName']
    if 'SubProgramType' in data:
        subprogram.SubProgramType = data['SubProgramType']
    if 'ProgramID' in data:
        program_exists = Program.query.get(data['ProgramID'])
        if not program_exists:
            return jsonify({"message": "New ProgramID does not exist"}), 404
        subprogram.ProgramID = data['ProgramID']

    try:
        db.session.commit()
        return jsonify({"message": "SubProgram updated successfully", "subprogram_id": subprogram.SubProgramID}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating subprogram: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/subprograms/<string:subprogram_id>', methods=['DELETE'])
@token_required # Protect this route
def delete_subprogram(current_user, subprogram_id): # Add current_user parameter
    """Deletes a subprogram by its ID. Requires authentication."""
    if current_user.role != 'admin': # Only admins can delete subprograms
        return jsonify({'message': 'Unauthorized: Only administrators can delete subprograms'}), 403

    subprogram = SubProgram.query.get(subprogram_id)
    if not subprogram:
        return jsonify({"message": "SubProgram not found"}), 404

    db.session.delete(subprogram)
    try:
        db.session.commit()
        return jsonify({"message": "SubProgram deleted successfully"}), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Cannot delete subprogram; related Courses exist. Delete them first."}), 409
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting subprogram: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500


# Semester Endpoints
@enrollment_bp.route('/semesters', methods=['GET'])
@token_required # Protect this route
def get_semesters(current_user): # Add current_user parameter
    """Retrieves all semesters from the database. Requires authentication."""
    semesters = Semester.query.all()
    return jsonify([serialize_semester(s) for s in semesters])

@enrollment_bp.route('/semesters/<string:semester_id>', methods=['GET'])
@token_required # Protect this route
def get_semester(current_user, semester_id): # Add current_user parameter
    """Retrieves a single semester by its ID. Requires authentication."""
    semester = Semester.query.get(semester_id)
    if not semester:
        return jsonify({"message": "Semester not found"}), 404
    return jsonify(serialize_semester(semester))

@enrollment_bp.route('/semesters', methods=['POST'])
@token_required # Protect this route
def add_semester(current_user): # Add current_user parameter
    """Adds a new semester to the database. Requires authentication."""
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators or SAS managers can add semesters'}), 403

    data = request.json
    if not data or not all(k in data for k in ['SemesterID', 'SemesterName']):
        return jsonify({"message": "Missing semester data (requires SemesterID, SemesterName)"}), 400

    new_semester = Semester(
        SemesterID=data['SemesterID'],
        SemesterName=data['SemesterName']
    )
    db.session.add(new_semester)
    try:
        db.session.commit()
        return jsonify({"message": "Semester added successfully", "semester_id": new_semester.SemesterID}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Semester with this ID already exists"}), 409
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding semester: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/semesters/<string:semester_id>', methods=['PUT'])
@token_required # Protect this route
def update_semester(current_user, semester_id): # Add current_user parameter
    """Updates an existing semester by its ID. Requires authentication."""
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators or SAS managers can update semesters'}), 403

    semester = Semester.query.get(semester_id)
    if not semester:
        return jsonify({"message": "Semester not found"}), 404

    data = request.json
    if not data:
        return jsonify({"message": "No data provided for update"}), 400

    if 'SemesterName' in data:
        semester.SemesterName = data['SemesterName']

    try:
        db.session.commit()
        return jsonify({"message": "Semester updated successfully", "semester_id": semester.SemesterID}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating semester: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/semesters/<string:semester_id>', methods=['DELETE'])
@token_required # Protect this route
def delete_semester(current_user, semester_id): # Add current_user parameter
    """Deletes a semester by its ID. Requires authentication."""
    if current_user.role != 'admin': # Only admins can delete semesters
        return jsonify({'message': 'Unauthorized: Only administrators can delete semesters'}), 403

    semester = Semester.query.get(semester_id)
    if not semester:
        return jsonify({"message": "Semester not found"}), 404

    db.session.delete(semester)
    try:
        db.session.commit()
        return jsonify({"message": "Semester deleted successfully"}), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Cannot delete semester; related Course Availabilities exist. Delete them first."}), 409
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting semester: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500


# enrollment_services/routes.py (continued from Part 4)

# --- API Endpoints (JSON Responses) continued ---

# Student Endpoints
@enrollment_bp.route('/students', methods=['GET'])
@token_required # Protect this route
def get_students(current_user): # Add current_user parameter
    """Retrieves all students from the database. Requires authentication."""
    # Example: Only admins or SAS managers can view all students
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Access restricted to administrators and SAS managers'}), 403
    students = Student.query.all()
    return jsonify([serialize_student(s) for s in students])

@enrollment_bp.route('/students', methods=['POST'])
@token_required # Protect this route
def create_student(current_user): # Add current_user parameter
    """Creates a new student record in the database. Requires authentication."""
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators and SAS managers can create students'}), 403

    data = request.json
    if not data or not all(k in data for k in ['StudentID', 'FirstName', 'LastName', 'Email']):
        return jsonify({"message": "Missing student data (requires StudentID, FirstName, LastName, Email)"}), 400

    new_student = Student(
        StudentID=data['StudentID'],
        FirstName=data['FirstName'],
        LastName=data['LastName'],
        Email=data['Email']
    )
    db.session.add(new_student)
    try:
        db.session.commit()
        return jsonify({"message": "Student created successfully", "student_id": new_student.StudentID}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Student with this ID or Email already exists"}), 409
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating student: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/students/<string:student_id>', methods=['GET'])
@token_required # Protect this route
def get_student(current_user, student_id): # Add current_user parameter
    """Retrieves a single student by their ID. Requires authentication."""
    # A student should only be able to view their own profile, managers/admins can view any
    if current_user.role == 'student' and current_user.id != student_id:
        return jsonify({'message': 'Unauthorized: You can only view your own student profile'}), 403

    student = Student.query.get(student_id)
    if not student:
        return jsonify({"message": "Student not found"}), 404
    return jsonify(serialize_student(student))

@enrollment_bp.route('/students/<string:student_id>', methods=['PUT'])
@token_required # Protect this route
def update_student(current_user, student_id): # Add current_user parameter
    """Updates an existing student's details. Requires authentication."""
    # Students can only update their own profile; admins/managers can update any
    if current_user.role == 'student' and current_user.id != student_id:
        return jsonify({'message': 'Unauthorized: You can only update your own student profile'}), 403
    if current_user.role not in ['admin', 'sas_manager', 'student']: # Add 'student' if students can update certain fields
        return jsonify({'message': 'Unauthorized: Insufficient privileges to update student'}), 403

    student = Student.query.get(student_id)
    if not student:
        return jsonify({"message": "Student not found"}), 404

    data = request.json
    if not data:
        return jsonify({"message": "No data provided for update"}), 400

    # Example: Allow students to update only their email/name, not ID
    if current_user.role == 'student':
        if 'StudentID' in data and data['StudentID'] != student_id: # Prevent ID change
             return jsonify({"message": "Unauthorized: Cannot change your Student ID"}), 403
        if 'role' in data: # Prevent role change for students
             return jsonify({"message": "Unauthorized: Cannot change role"}), 403

    if 'FirstName' in data:
        student.FirstName = data['FirstName']
    if 'LastName' in data:
        student.LastName = data['LastName']
    if 'Email' in data:
        if Student.query.filter(Student.Email == data['Email'], Student.StudentID != student_id).first():
            return jsonify({"message": "Email already registered to another student"}), 409
        student.Email = data['Email']
    # Admins/Managers could potentially update more fields like role, but students cannot.

    try:
        db.session.commit()
        return jsonify({"message": "Student updated successfully", "student_id": student.StudentID}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating student {student_id}: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/students/<string:student_id>', methods=['DELETE'])
@token_required # Protect this route
def delete_student(current_user, student_id): # Add current_user parameter
    """Deletes a student and associated records (enrollments, fees, holds, levels). Requires authentication."""
    if current_user.role != 'admin': # Only admins can delete student records
        return jsonify({'message': 'Unauthorized: Only administrators can delete student records'}), 403

    student = Student.query.get(student_id)
    if not student:
        return jsonify({"message": "Student not found"}), 404

    try:
        # Delete related records first due to foreign key constraints
        StudentLevel.query.filter_by(StudentID=student_id).delete(synchronize_session=False)
        Hold.query.filter_by(StudentID=student_id).delete(synchronize_session=False)
        Enrollment.query.filter_by(StudentID=student_id).delete(synchronize_session=False)
        StudentCourseFee.query.filter_by(StudentID=student_id).delete(synchronize_session=False)

        db.session.delete(student)
        db.session.commit()
        return jsonify({"message": "Student and all associated records deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting student {student_id}: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500


# Course Endpoints
@enrollment_bp.route('/courses_api', methods=['GET']) # Using _api suffix to differentiate from frontend course list
@token_required # Protect this route
def get_courses_api(current_user): # Add current_user parameter
    """Retrieves all courses with their subprogram and availability details. Requires authentication."""
    courses = Course.query.options(db.joinedload(Course.subprogram), db.joinedload(Course.course_availabilities).joinedload(CourseAvailability.semester)).all()
    return jsonify([serialize_course(course) for course in courses])

@enrollment_bp.route('/courses_api/<string:course_id>', methods=['GET'])
@token_required # Protect this route
def get_course_api(current_user, course_id): # Add current_user parameter
    """Retrieves a single course by its ID with subprogram and availability details. Requires authentication."""
    course = Course.query.options(db.joinedload(Course.subprogram), db.joinedload(Course.course_availabilities).joinedload(CourseAvailability.semester)).get(course_id)
    if not course:
        return jsonify({"message": "Course not found"}), 404
    return jsonify(serialize_course(course))

@enrollment_bp.route('/courses_api', methods=['POST'])
@token_required # Protect this route
def add_course_api(current_user): # Add current_user parameter
    """Adds a new course to the database. Requires authentication."""
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators and SAS managers can add courses'}), 403

    data = request.json
    if not data or not all(k in data for k in ['CourseID', 'CourseName', 'SubProgramID']):
        return jsonify({"message": "Missing course data (requires CourseID, CourseName, SubProgramID)"}), 400

    subprogram = SubProgram.query.get(data['SubProgramID'])
    if not subprogram:
        return jsonify({"message": "SubProgramID does not exist"}), 404

    prereq_course_id = data.get('PrerequisiteCourseID')
    if prereq_course_id:
        prereq_course = Course.query.get(prereq_course_id)
        if not prereq_course:
            return jsonify({"message": "PrerequisiteCourseID does not exist"}), 404

    new_course = Course(
        CourseID=data['CourseID'],
        CourseName=data['CourseName'],
        SubProgramID=data['SubProgramID'],
        PrerequisiteCourseID=prereq_course_id
    )
    db.session.add(new_course)
    try:
        db.session.commit()
        return jsonify({"message": "Course added successfully", "course_id": new_course.CourseID}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Course with this ID already exists"}), 409
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding course: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/courses_api/<string:course_id>', methods=['PUT'])
@token_required # Protect this route
def update_course_api(current_user, course_id): # Add current_user parameter
    """Updates an existing course by its ID. Requires authentication."""
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators and SAS managers can update courses'}), 403

    course = Course.query.get(course_id)
    if not course:
        return jsonify({"message": "Course not found"}), 404

    data = request.json
    if not data:
        return jsonify({"message": "No data provided for update"}), 400

    if 'CourseName' in data:
        course.CourseName = data['CourseName']
    if 'SubProgramID' in data:
        subprogram = SubProgram.query.get(data['SubProgramID'])
        if not subprogram:
            return jsonify({"message": "New SubProgramID does not exist"}), 404
        course.SubProgramID = data['SubProgramID']
    if 'PrerequisiteCourseID' in data:
        prereq_course_id = data['PrerequisiteCourseID']
        if prereq_course_id:
            prereq_course = Course.query.get(prereq_course_id)
            if not prereq_course:
                return jsonify({"message": "New PrerequisiteCourseID does not exist"}), 404
        course.PrerequisiteCourseID = prereq_course_id

    try:
        db.session.commit()
        return jsonify({"message": "Course updated successfully", "course_id": course.CourseID}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating course {course_id}: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/courses_api/<string:course_id>', methods=['DELETE'])
@token_required # Protect this route
def delete_course_api(current_user, course_id): # Add current_user parameter
    """Deletes a course by its ID. Requires authentication."""
    if current_user.role != 'admin': # Only admins can delete courses
        return jsonify({'message': 'Unauthorized: Only administrators can delete courses'}), 403

    course = Course.query.get(course_id)
    if not course:
        return jsonify({"message": "Course not found"}), 404

    try:
        # Check for related records before deleting to prevent IntegrityError
        if Enrollment.query.filter_by(CourseID=course_id).first():
            return jsonify({"message": "Cannot delete course; existing enrollments depend on it. Delete enrollments first."}), 409
        if StudentCourseFee.query.filter_by(CourseID=course_id).first():
            return jsonify({"message": "Cannot delete course; existing student fees depend on it. Delete fees first."}), 409
        if CourseAvailability.query.filter_by(CourseID=course_id).first():
            return jsonify({"message": "Cannot delete course; existing course availabilities depend on it. Delete availabilities first."}), 409
        if CourseFee.query.filter_by(CourseID=course_id).first():
            return jsonify({"message": "Cannot delete course; existing course fees depend on it. Delete fees first."}), 409
        if Course.query.filter_by(PrerequisiteCourseID=course_id).first():
            return jsonify({"message": "Cannot delete course; it is a prerequisite for other courses. Update those courses first."}), 409

        db.session.delete(course)
        db.session.commit()
        return jsonify({"message": "Course deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting course {course_id}: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

# Course Availability Endpoints
@enrollment_bp.route('/course_availabilities', methods=['GET'])
@token_required # Protect this route
def get_course_availabilities(current_user): # Add current_user parameter
    """Retrieves all course availabilities, with related course and semester details. Requires authentication."""
    availabilities = CourseAvailability.query.options(db.joinedload(CourseAvailability.course), db.joinedload(CourseAvailability.semester)).all()
    return jsonify([{
        "CourseAvailabilityID": ca.CourseAvailabilityID,
        "isAvailable": ca.isAvailable,
        "CourseID": ca.CourseID,
        "CourseName": ca.course.CourseName if ca.course else None,
        "SemesterID": ca.SemesterID,
        "SemesterName": ca.semester.SemesterName if ca.semester else None
    } for ca in availabilities])

@enrollment_bp.route('/course_availabilities/<string:ca_id>', methods=['GET'])
@token_required # Protect this route
def get_course_availability(current_user, ca_id): # Add current_user parameter
    """Retrieves a single course availability by its ID. Requires authentication."""
    availability = CourseAvailability.query.options(db.joinedload(CourseAvailability.course), db.joinedload(CourseAvailability.semester)).get(ca_id)
    if not availability:
        return jsonify({"message": "Course availability not found"}), 404
    return jsonify({
        "CourseAvailabilityID": availability.CourseAvailabilityID,
        "isAvailable": availability.isAvailable,
        "CourseID": availability.CourseID,
        "CourseName": availability.course.CourseName if availability.course else None,
        "SemesterID": availability.SemesterID,
        "SemesterName": availability.semester.SemesterName if availability.semester else None
    })

@enrollment_bp.route('/course_availabilities', methods=['POST'])
@token_required # Protect this route
def add_course_availability(current_user): # Add current_user parameter
    """Adds a new course availability record. Requires authentication."""
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators and SAS managers can add course availabilities'}), 403

    data = request.json
    if not data or not all(k in data for k in ['CourseAvailabilityID', 'CourseID', 'SemesterID']):
        return jsonify({"message": "Missing course availability data (requires CourseAvailabilityID, CourseID, SemesterID)"}), 400

    course = Course.query.get(data['CourseID'])
    semester = Semester.query.get(data['SemesterID'])
    if not course:
        return jsonify({"message": "Course not found"}), 404
    if not semester:
        return jsonify({"message": "Semester not found"}), 404

    existing_availability = CourseAvailability.query.filter_by(
        CourseID=data['CourseID'],
        SemesterID=data['SemesterID']
    ).first()
    if existing_availability:
        return jsonify({"message": "Course already available for this semester"}), 409

    new_availability = CourseAvailability(
        CourseAvailabilityID=data['CourseAvailabilityID'],
        CourseID=data['CourseID'],
        SemesterID=data['SemesterID'],
        isAvailable=data.get('isAvailable', True)
    )
    db.session.add(new_availability)
    try:
        db.session.commit()
        return jsonify({"message": "Course availability added successfully", "id": new_availability.CourseAvailabilityID}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Course Availability with this ID already exists"}), 409
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding course availability: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/course_availabilities/<string:ca_id>', methods=['PUT'])
@token_required # Protect this route
def update_course_availability(current_user, ca_id): # Add current_user parameter
    """Updates an existing course availability record. Requires authentication."""
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators and SAS managers can update course availabilities'}), 403

    availability = CourseAvailability.query.get(ca_id)
    if not availability:
        return jsonify({"message": "Course availability not found"}), 404

    data = request.json
    if not data:
        return jsonify({"message": "No data provided for update"}), 400

    if 'isAvailable' in data:
        availability.isAvailable = data['isAvailable']

    try:
        db.session.commit()
        return jsonify({"message": "Course availability updated successfully", "id": availability.CourseAvailabilityID}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating course availability {ca_id}: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/course_availabilities/<string:ca_id>', methods=['DELETE'])
@token_required # Protect this route
def delete_course_availability(current_user, ca_id): # Add current_user parameter
    """Deletes a course availability record. Requires authentication."""
    if current_user.role != 'admin':
        return jsonify({'message': 'Unauthorized: Only administrators can delete course availabilities'}), 403

    availability = CourseAvailability.query.get(ca_id)
    if not availability:
        return jsonify({"message": "Course availability not found"}), 404

    db.session.delete(availability)
    try:
        db.session.commit()
        return jsonify({"message": "Course availability deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting course availability {ca_id}: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

# enrollment_services/routes.py (continued from Part 5)

# --- API Endpoints (JSON Responses) continued ---

# Enrollment Endpoints
@enrollment_bp.route('/enrollments_api', methods=['GET'])
@token_required # Protect this route
def get_enrollments_api(current_user): # Add current_user parameter
    """Retrieves all enrollments with related student and course details. Requires authentication."""
    # Example: Students can only view their own enrollments; others can view all
    if current_user.role == 'student':
        enrollments = Enrollment.query.options(db.joinedload(Enrollment.student), db.joinedload(Enrollment.course)).filter_by(StudentID=current_user.id).all()
    else: # admin, sas_manager
        enrollments = Enrollment.query.options(db.joinedload(Enrollment.student), db.joinedload(Enrollment.course)).all()
    return jsonify([serialize_enrollment(e) for e in enrollments])

@enrollment_bp.route('/enrollments_api/<string:enrollment_id>', methods=['GET'])
@token_required # Protect this route
def get_enrollment_api(current_user, enrollment_id): # Add current_user parameter
    """Retrieves a single enrollment by its ID. Requires authentication."""
    enrollment = Enrollment.query.options(db.joinedload(Enrollment.student), db.joinedload(Enrollment.course)).get(enrollment_id)
    if not enrollment:
        return jsonify({"message": "Enrollment not found"}), 404

    # Students can only view their own specific enrollment
    if current_user.role == 'student' and enrollment.StudentID != current_user.id:
        return jsonify({'message': 'Unauthorized: You can only view your own enrollments'}), 403

    return jsonify(serialize_enrollment(enrollment))

@enrollment_bp.route('/enrollments_api', methods=['POST'])
@token_required # Protect this route
def create_enrollment_api(current_user): # Add current_user parameter
    """Creates a new enrollment record. Requires authentication."""
    # Only students can enroll themselves; admins/managers can enroll anyone
    if current_user.role == 'student' and request.json.get('StudentID') != current_user.id:
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

    # Prevent duplicate enrollments for the same student in the same course
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
    except IntegrityError: # Catches if EnrollmentID is duplicated
        db.session.rollback()
        return jsonify({"message": "Enrollment with this ID already exists"}), 409
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating enrollment: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/enrollments_api/<string:enrollment_id>', methods=['PUT'])
@token_required # Protect this route
def update_enrollment_api(current_user, enrollment_id): # Add current_user parameter
    """Updates an existing enrollment record. Requires authentication."""
    # Only admins/managers can update enrollments
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
    # Typically, StudentID and CourseID are not updated for an existing enrollment.

    try:
        db.session.commit()
        return jsonify({"message": "Enrollment updated successfully", "enrollment_id": enrollment.EnrollmentID}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating enrollment {enrollment_id}: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/enrollments_api/<string:enrollment_id>', methods=['DELETE'])
@token_required # Protect this route
def delete_enrollment_api(current_user, enrollment_id): # Add current_user parameter
    """Deletes an enrollment record. Requires authentication."""
    # Only admins/managers can delete enrollments
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
        logging.error(f"Error deleting enrollment {enrollment_id}: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500


# Course Fees Endpoints
@enrollment_bp.route('/course_fees_api', methods=['GET'])
@token_required # Protect this route
def get_course_fees_api(current_user): # Add current_user parameter
    """Retrieves all course fees with related course details. Requires authentication."""
    fees = CourseFee.query.options(db.joinedload(CourseFee.course)).all()
    return jsonify([serialize_course_fee(f) for f in fees])

@enrollment_bp.route('/course_fees_api/<int:fee_id>', methods=['GET'])
@token_required # Protect this route
def get_course_fee_api(current_user, fee_id): # Add current_user parameter
    """Retrieves a single course fee by its ID. Requires authentication."""
    fee = CourseFee.query.options(db.joinedload(CourseFee.course)).get(fee_id)
    if not fee:
        return jsonify({"message": "Course fee not found"}), 404
    return jsonify(serialize_course_fee(fee))

@enrollment_bp.route('/course_fees_api', methods=['POST'])
@token_required # Protect this route
def add_course_fee_api(current_user): # Add current_user parameter
    """Adds a new course fee record. Requires authentication."""
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators or SAS managers can add course fees'}), 403

    data = request.json
    if not data or not all(k in data for k in ['amount', 'description', 'CourseID']):
        return jsonify({"message": "Missing course fee data (requires amount, description, CourseID)"}), 400

    course = Course.query.get(data['CourseID'])
    if not course:
        return jsonify({"message": "Course not found"}), 404

    new_fee = CourseFee(
        amount=data['amount'],
        description=data['description'],
        CourseID=data['CourseID']
    )
    db.session.add(new_fee)
    try:
        db.session.commit()
        return jsonify({"message": "Course fee added successfully", "fee_id": new_fee.FeeID}), 201
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding course fee: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/course_fees_api/<int:fee_id>', methods=['PUT'])
@token_required # Protect this route
def update_course_fee_api(current_user, fee_id): # Add current_user parameter
    """Updates an existing course fee record. Requires authentication."""
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

@enrollment_bp.route('/course_fees_api/<int:fee_id>', methods=['DELETE'])
@token_required # Protect this route
def delete_course_fee_api(current_user, fee_id): # Add current_user parameter
    """Deletes a course fee record. Requires authentication."""
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
@token_required # Protect this route
def get_student_course_fees_api(current_user): # Add current_user parameter
    """Retrieves all student course fee records with related student, course, and course fee details. Requires authentication."""
    if current_user.role == 'student':
        # Students can only see their own assigned fees
        student_fees = StudentCourseFee.query.options(
            db.joinedload(StudentCourseFee.student),
            db.joinedload(StudentCourseFee.course),
            db.joinedload(StudentCourseFee.course_fee)
        ).filter_by(StudentID=current_user.id).all()
    else: # admin, sas_manager can see all
        student_fees = StudentCourseFee.query.options(
            db.joinedload(StudentCourseFee.student),
            db.joinedload(StudentCourseFee.course),
            db.joinedload(StudentCourseFee.course_fee)
        ).all()
    return jsonify([serialize_student_course_fee(sf) for sf in student_fees])

@enrollment_bp.route('/student_course_fees_api/<int:scf_id>', methods=['GET'])
@token_required # Protect this route
def get_student_course_fee_api(current_user, scf_id): # Add current_user parameter
    """Retrieves a single student course fee record by its ID. Requires authentication."""
    student_fee = StudentCourseFee.query.options(
        db.joinedload(StudentCourseFee.student),
        db.joinedload(StudentCourseFee.course),
        db.joinedload(StudentCourseFee.course_fee)
    ).get(scf_id)
    if not student_fee:
        return jsonify({"message": "Student course fee not found"}), 404

    # Students can only view their own fees
    if current_user.role == 'student' and student_fee.StudentID != current_user.id:
        return jsonify({'message': 'Unauthorized: You can only view your own student course fees'}), 403

    return jsonify(serialize_student_course_fee(student_fee))

@enrollment_bp.route('/student_course_fees_api', methods=['POST'])
@token_required # Protect this route
def assign_student_course_fee_api(current_user): # Add current_user parameter
    """Assigns a course fee to a specific student for a specific course. Requires authentication."""
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators or SAS managers can assign student course fees'}), 403

    data = request.json
    if not data or not all(k in data for k in ['StudentID', 'CourseID', 'due_date']):
        return jsonify({"message": "Missing student course fee data (requires StudentID, CourseID, due_date)"}), 400

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

    new_student_fee = StudentCourseFee(
        StudentID=data['StudentID'],
        CourseID=data['CourseID'],
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

@enrollment_bp.route('/student_course_fees_api/<int:scf_id>', methods=['PUT'])
@token_required # Protect this route
def update_student_course_fee_api(current_user, scf_id): # Add current_user parameter
    """Updates an existing student course fee record. Requires authentication."""
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators or SAS managers can update student course fees'}), 403

    student_fee = StudentCourseFee.query.get(scf_id)
    if not student_fee:
        return jsonify({"message": "Student course fee not found"}), 404

    data = request.json
    if not data:
        return jsonify({"message": "No data provided for update"}), 400

    if 'due_date' in data:
        student_fee.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
    if 'paid_date' in data:
        student_fee.paid_date = datetime.strptime(data['paid_date'], '%Y-%m-%d').date() if data['paid_date'] else None
    if 'status' in data:
        student_fee.status = data['status']

    try:
        db.session.commit()
        return jsonify({"message": "Student course fee updated successfully", "student_course_fee_id": student_fee.StudentCourseFeeID}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating student course fee {scf_id}: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/student_course_fees_api/<int:scf_id>', methods=['DELETE'])
@token_required # Protect this route
def delete_student_course_fee_api(current_user, scf_id): # Add current_user parameter
    """Deletes a student course fee record. Requires authentication."""
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

# enrollment_services/routes.py (continued from Part 6)

# --- API Endpoints (JSON Responses) continued ---

# Hold Endpoints
@enrollment_bp.route('/holds', methods=['GET'])
@token_required # Protect this route
def get_holds(current_user): # Add current_user parameter
    """Retrieves all hold records with related student details. Requires authentication."""
    if current_user.role == 'student':
        # Students can only view their own holds
        holds = Hold.query.options(db.joinedload(Hold.student)).filter_by(StudentID=current_user.id).all()
    else: # admin, sas_manager
        holds = Hold.query.options(db.joinedload(Hold.student)).all()
    return jsonify([serialize_hold(h) for h in holds])

@enrollment_bp.route('/holds/<int:hold_id>', methods=['GET'])
@token_required # Protect this route
def get_hold(current_user, hold_id): # Add current_user parameter
    """Retrieves a single hold record by its ID. Requires authentication."""
    hold = Hold.query.options(db.joinedload(Hold.student)).get(hold_id)
    if not hold:
        return jsonify({"message": "Hold not found"}), 404

    # Students can only view their own specific hold
    if current_user.role == 'student' and hold.StudentID != current_user.id:
        return jsonify({'message': 'Unauthorized: You can only view your own holds'}), 403

    return jsonify(serialize_hold(hold))

@enrollment_bp.route('/holds', methods=['POST'])
@token_required # Protect this route
def add_hold(current_user): # Add current_user parameter
    """Adds a new hold record for a student. Requires authentication."""
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators or SAS managers can add holds'}), 403

    data = request.json
    if not data or not all(k in data for k in ['StudentID', 'reason']):
        return jsonify({"message": "Missing hold data (requires StudentID, reason)"}), 400

    student = Student.query.get(data['StudentID'])
    if not student:
        return jsonify({"message": "Student not found"}), 404

    new_hold = Hold(
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
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding hold: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/holds/<int:hold_id>', methods=['PUT'])
@token_required # Protect this route
def update_hold(current_user, hold_id): # Add current_user parameter
    """Updates an existing hold record. Requires authentication."""
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

    try:
        db.session.commit()
        return jsonify({"message": "Hold updated successfully", "hold_id": hold.HoldID}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating hold {hold_id}: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/holds/<int:hold_id>', methods=['DELETE'])
@token_required # Protect this route
def delete_hold(current_user, hold_id): # Add current_user parameter
    """Deletes a hold record. Requires authentication."""
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
@token_required # Protect this route
def get_student_levels(current_user): # Add current_user parameter
    """Retrieves all student level records with related student details. Requires authentication."""
    if current_user.role == 'student':
        # Students can only view their own student levels
        student_levels = StudentLevel.query.options(db.joinedload(StudentLevel.student)).filter_by(StudentID=current_user.id).all()
    else: # admin, sas_manager
        student_levels = StudentLevel.query.options(db.joinedload(StudentLevel.student)).all()
    return jsonify([serialize_student_level(sl) for sl in student_levels])

@enrollment_bp.route('/student_levels/<string:student_level_id>', methods=['GET'])
@token_required # Protect this route
def get_student_level(current_user, student_level_id): # Add current_user parameter
    """Retrieves a single student level record by its ID. Requires authentication."""
    student_level = StudentLevel.query.options(db.joinedload(StudentLevel.student)).get(student_level_id)
    if not student_level:
        return jsonify({"message": "Student level not found"}), 404

    # Students can only view their own specific student level
    if current_user.role == 'student' and student_level.StudentID != current_user.id:
        return jsonify({'message': 'Unauthorized: You can only view your own student levels'}), 403

    return jsonify(serialize_student_level(student_level))

@enrollment_bp.route('/student_levels', methods=['POST'])
@token_required # Protect this route
def add_student_level(current_user): # Add current_user parameter
    """Adds a new student level record. Requires authentication."""
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators or SAS managers can add student levels'}), 403

    data = request.json
    if not data or not all(k in data for k in ['StudentLevelID', 'StudentID']):
        return jsonify({"message": "Missing student level data (requires StudentLevelID, StudentID)"}), 400

    student = Student.query.get(data['StudentID'])
    if not student:
        return jsonify({"message": "Student not found"}), 404

    new_student_level = StudentLevel(
        StudentLevelID=data['StudentLevelID'],
        StudentID=data['StudentID'],
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
@token_required # Protect this route
def update_student_level(current_user, student_level_id): # Add current_user parameter
    """Updates an existing student level record. Requires authentication."""
    if current_user.role not in ['admin', 'sas_manager']:
        return jsonify({'message': 'Unauthorized: Only administrators or SAS managers can update student levels'}), 403

    student_level = StudentLevel.query.get(student_level_id)
    if not student_level:
        return jsonify({"message": "Student level not found"}), 404

    data = request.json
    if not data:
        return jsonify({"message": "No data provided for update"}), 400

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
@token_required # Protect this route
def delete_student_level(current_user, student_level_id): # Add current_user parameter
    """Deletes a student level record. Requires authentication."""
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

# --- End of routes.py ---