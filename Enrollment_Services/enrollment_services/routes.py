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
import uuid # Import uuid for generating unique IDs

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
    # Fetch course data from the database, focusing on enrolled courses
    courses_from_db = Course.query.filter(Course.CourseID.in_(enrolled_courses_codes)).options(joinedload(Course.course_fees_records)).all()

    for course_db in courses_from_db:
        # Assuming fee_per_credit is still a mock concept for invoice, or you have a default fee.
        # For accurate fees, you'd need CourseFee objects linked to courses.
        # If CourseFee is populated, use that amount directly.
        course_fee_amount = 0.0
        if course_db.course_fees_records:
            # Assuming one relevant fee per course for simplicity in this calculation
            course_fee_amount = course_db.course_fees_records[0].amount
        else:
            # Fallback for courses without explicit fees or mock value
            # You might want to get this dynamically from your CourseFee model in a real app
            # For now, let's use a placeholder if no specific fee is linked
            course_fee_amount = 50.00 # Default mock fee if not found via CourseFee

        # Assuming credits are part of the Course model or a related entity.
        # If not, you'd need to either mock them or add them to your schema.
        # For demonstration, let's just assume a fixed credit or derive if possible.
        course_credits = 3 # Placeholder if not in DB schema for Course

        subtotal = course_credits * course_fee_amount
        invoice_items.append({
            'code': course_db.CourseID,
            'title': course_db.CourseName,
            'credits': course_credits,
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
        # Fetch only 'CS' courses from the database
        # This filters courses where CourseID starts with 'CS'
        all_cs_courses = Course.query.filter(Course.CourseID.like('CS%')).options(
            joinedload(Course.subprogram),
            joinedload(Course.course_availabilities).joinedload(CourseAvailability.semester)
        ).all()

        # Fetch courses the student has ALREADY completed or is currently enrolled in
        student_completed_courses = set() # Placeholder for actual completed courses
        current_enrollments = Enrollment.query.filter_by(StudentID=current_user.id).all()
        currently_enrolled_course_ids = {e.CourseID for e in current_enrollments}

        # Combine explicitly completed courses with currently enrolled ones for prerequisite checks
        all_met_courses_for_prereq_check = student_completed_courses.union(currently_enrolled_course_ids)

        courses_for_template = []
        for course_db in all_cs_courses: # Iterate through filtered CS courses
            prerequisite_course_name = None
            prereq_met = True
            if course_db.PrerequisiteCourseID:
                prereq_course_obj = Course.query.get(course_db.PrerequisiteCourseID)
                if prereq_course_obj:
                    prerequisite_course_name = prereq_course_obj.CourseName
                    if prereq_course_obj.CourseID not in all_met_courses_for_prereq_check:
                        prereq_met = False
                else:
                    # Prerequisite course ID exists but actual course object not found
                    prerequisite_course_name = f"Unknown ({course_db.PrerequisiteCourseID})"
                    prereq_met = False # Cannot verify if prerequisite is met

            # Check if course is already enrolled
            already_enrolled = course_db.CourseID in currently_enrolled_course_ids

            courses_for_template.append({
                'code': course_db.CourseID,
                'title': course_db.CourseName,
                'description': f"Offered in {', '.join([ca.semester.SemesterName for ca in course_db.course_availabilities if ca.isAvailable])}" if course_db.course_availabilities else 'Availability Unknown',
                'prerequisites': {prerequisite_course_name} if prerequisite_course_name else set(),
                'prereq_met': prereq_met,
                'already_enrolled': already_enrolled
            })

        if request.method == 'POST':
            selected_codes = request.form.getlist('courses')
            
            # --- New logic for unit counting ---
            unit_count = 0.0
            for code in selected_codes:
                if code in ['UU100A', 'CS001']:
                    unit_count += 0.5
                else:
                    unit_count += 1.0
            
            if unit_count > 4.0:
                flash('You can select a maximum of 4 full units (UU100A and CS001 count as 0.5 units each).', 'error')
                return redirect(url_for('enrollment.enroll'))
            # --- End new logic ---

            unmet = []
            already_enrolled_in_selection = []
            courses_to_enroll = []

            for course_code in selected_codes:
                course_obj = Course.query.get(course_code)
                if not course_obj:
                    flash(f"Error: Course '{course_code}' not found.", 'error')
                    continue

                # Re-check prerequisites for the selected course
                prereq_met_for_selected = True
                if course_obj.PrerequisiteCourseID:
                    prereq_course_obj = Course.query.get(course_obj.PrerequisiteCourseID)
                    if prereq_course_obj:
                        prerequisite_course_name = prereq_course_obj.CourseName
                        if prereq_course_obj.CourseID not in all_met_courses_for_prereq_check:
                            prereq_met_for_selected = False
                            # Fetch the actual prerequisite course name for the flash message
                            prereq_course_for_msg = Course.query.get(course_obj.PrerequisiteCourseID)
                            unmet_course_name = prereq_course_for_msg.CourseName if prereq_course_for_msg else course_obj.PrerequisiteCourseID
                            unmet.append(f"{course_obj.CourseName} (requires {unmet_course_name})")

                # Check if already enrolled
                if course_code in currently_enrolled_course_ids:
                    already_enrolled_in_selection.append(course_obj.CourseName)

                if prereq_met_for_selected and not (course_code in currently_enrolled_course_ids):
                    courses_to_enroll.append(course_obj)

            if unmet:
                flash(f"Cannot enroll in: {', '.join(unmet)} due to unmet prerequisites.", 'error')
            if already_enrolled_in_selection:
                flash(f"You are already enrolled in: {', '.join(already_enrolled_in_selection)}.", 'info')

            if courses_to_enroll:
                newly_enrolled_count = 0
                for course_to_add in courses_to_enroll:
                    try:
                        new_enrollment_id = str(uuid.uuid4())[:10]
                        
                        # Ensure ID is unique (though uuid4 makes it highly improbable to clash)
                        while db.session.get(Enrollment, new_enrollment_id):
                            new_enrollment_id = str(uuid.uuid4())[:10]

                        enrollment = Enrollment(
                            EnrollmentID=new_enrollment_id,
                            StudentID=current_user.id, # Use the logged-in student's ID
                            CourseID=course_to_add.CourseID,
                            EnrollmentDate=datetime.utcnow().date()
                        )
                        db.session.add(enrollment)
                        newly_enrolled_count += 1
                        all_met_courses_for_prereq_check.add(course_to_add.CourseID) # Update for subsequent prereq checks in the same session
                        currently_enrolled_course_ids.add(course_to_add.CourseID)

                    except IntegrityError:
                        db.session.rollback()
                        flash(f"Error: Duplicate enrollment or ID conflict for {course_to_add.CourseName}. Please try again.", "error")
                        logging.error(f"IntegrityError during enrollment for {current_user.id} in {course_to_add.CourseID}")
                        return redirect(url_for('enrollment.enroll')) # Redirect to prevent re-submission issue
                    except Exception as e:
                        db.session.rollback()
                        flash(f"An unexpected error occurred during enrollment for {course_to_add.CourseName}.", "error")
                        logging.error(f"Error enrolling student {current_user.id} in course {course_to_add.CourseID}: {e}")
                        return redirect(url_for('enrollment.enroll')) # Redirect to prevent re-submission issue
                
                db.session.commit() # Commit all new enrollments in one go
                if newly_enrolled_count > 0:
                    flash(f'Successfully enrolled in {newly_enrolled_count} new course(s)! Please confirm your courses.', 'success')
                return redirect(url_for('enrollment.display_courses'))

        # Prepare courses for rendering again, with updated prereq_met status based on new enrollments
        # This loop is slightly redundant if no POST occurred, but harmless.
        # It ensures correct state if there was a partial enrollment or error.
        updated_courses_for_template = []
        for course_item in courses_for_template:
            course_obj = Course.query.get(course_item['code'])
            prerequisite_course_name = None
            prereq_met_display = True
            if course_obj.PrerequisiteCourseID:
                prereq_course_obj = Course.query.get(course_obj.PrerequisiteCourseID)
                if prereq_course_obj:
                    prerequisite_course_name = prereq_course_obj.CourseName
                    if prereq_course_obj.CourseID not in all_met_courses_for_prereq_check:
                        prereq_met_display = False
                else:
                    prerequisite_course_name = f"Unknown ({course_obj.PrerequisiteCourseID})"
                    prereq_met_display = False

            course_item['prerequisites'] = {prerequisite_course_name} if prerequisite_course_name else set()
            course_item['prereq_met'] = prereq_met_display
            course_item['already_enrolled'] = course_item['code'] in currently_enrolled_course_ids
            updated_courses_for_template.append(course_item)


        return render_template('enroll.html', courses=updated_courses_for_template)
    except Exception as e:
        logging.error(f"Error in /enroll: {e}")
        db.session.rollback() # Ensure rollback on any unhandled exception
        flash("An unexpected error occurred. Please try again.", "error")
        return render_template('500.html'), 500

@enrollment_bp.route('/display_courses')
@token_required # Protect the display_courses route
def display_courses(current_user): # Add current_user parameter
    """Displays the courses currently selected/enrolled by the student (from session). Requires authentication."""
    try:
        # Fetch enrolled courses for the logged-in student from the database
        # Eager load the 'course' relationship to get CourseName directly
        enrolled_courses = Enrollment.query.filter_by(StudentID=current_user.id).options(joinedload(Enrollment.course)).all()
        
        # We need to transform this into a format compatible with your existing template
        # The template expects 'code', 'title', 'semester'
        courses_for_template = []
        for enrollment in enrolled_courses:
            if enrollment.course: # Ensure the course relationship was loaded
                courses_for_template.append({
                    'code': enrollment.course.CourseID,
                    'title': enrollment.course.CourseName,
                    'semester': 'Semester 2, 2025' # You might want to get this dynamically from CourseAvailability/Semester
                })

        return render_template('display_courses.html', enrolled_courses=courses_for_template)
    except Exception as e:
        logging.error(f"Error in /display_courses: {e}")
        return render_template('500.html'), 500

@enrollment_bp.route('/drop_course/<course_code>')
@token_required # Protect the drop_course route
def drop_course(current_user, course_code): # Add current_user parameter
    """Allows a student to drop a course from their current session enrollment. Requires authentication."""
    try:
        # Find the enrollment record for the current student and the specified course
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
        db.session.rollback() # Rollback in case of error
        logging.error(f"Error in /drop_course/{course_code}: {e}")
        flash(f"An error occurred while dropping course {course_code}.", "error")
        return render_template('500.html'), 500

@enrollment_bp.route('/fees')
@token_required # Protect the fees route
def fees(current_user): # Add current_user parameter
    """Renders the fees overview page, showing calculated invoice details. Requires authentication."""
    try:
        # Define the fixed general services fee
        general_services_fee = 50.00  #

        # Fetch actual enrolled courses for the student
        enrolled_courses_db = Enrollment.query.filter_by(StudentID=current_user.id).options(
            joinedload(Enrollment.course).joinedload(Course.course_fees_records)
        ).all()
        
        invoice_items = []
        total_amount = 0

        for enrollment in enrolled_courses_db:
            course = enrollment.course
            if course and course.course_fees_records:
                # Assuming one fee per course for simplicity for now
                course_fee = course.course_fees_records[0] 
                subtotal = float(course_fee.amount) # Ensure subtotal is float
                invoice_items.append({
                    'code': course.CourseID,
                    'title': course.CourseName,
                    'fee': subtotal # Directly use the fee amount
                })
                total_amount += subtotal
            elif course:
                # If no fee record found for the course, provide a default fee of 0.00
                invoice_items.append({
                    'code': course.CourseID,
                    'title': course.CourseName,
                    'fee': 0.00 # Default to 0.00 if no fee record
                })
        
        # Add the general services fee to the total amount
        total_amount += general_services_fee

        # Update student_details and invoice_details dynamically
        student_data = Student.query.get(current_user.id)
        if student_data:
            student_details['name'] = f"{student_data.FirstName} {student_data.LastName}"
            student_details['id'] = student_data.StudentID
        else:
            student_details['name'] = current_user.username
            student_details['id'] = current_user.id
            
        # Generate a random invoice number
        invoice_details['number'] = f"INV-{uuid.uuid4().hex[:8].upper()}"  # Generate a random 8-character hex string
        invoice_details['date'] = datetime.now().strftime('%B %d, %Y')
        # This part ('Semester 2, 2025') is still hardcoded as your schema doesn't link enrollment to specific semester easily
        invoice_details['semester'] = 'Semester 2, 2025'
        # Determine payment status (e.g., check StudentCourseFee status)
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
            general_services_fee=general_services_fee  # Pass the general services fee to the template
        )
    except Exception as e:
        logging.error(f"Error in /fees: {e}")
        return render_template('500.html'), 500

@enrollment_bp.route('/download_invoice_pdf')
@token_required # Protect the download_invoice_pdf route
def download_invoice_pdf(current_user): # Add current_user parameter
    """Generates and provides a PDF download of the invoice. Requires authentication."""
    try:
        # Define the fixed general services fee
        general_services_fee = 50.00  #

        # Fetch actual enrolled courses for the student
        enrolled_courses_db = Enrollment.query.filter_by(StudentID=current_user.id).options(
            joinedload(Enrollment.course).joinedload(Course.course_fees_records)
        ).all()
        
        invoice_items = []
        total_amount = 0

        for enrollment in enrolled_courses_db:
            course = enrollment.course
            if course and course.course_fees_records:
                course_fee = course.course_fees_records[0] # Assuming one fee per course
                subtotal = float(course_fee.amount) # Ensure subtotal is float
                invoice_items.append({
                    'code': course.CourseID,
                    'title': course.CourseName,
                    'fee': subtotal # Directly use the fee amount
                })
                total_amount += subtotal
            elif course:
                # If no fee record found for the course, provide a default fee of 0.00
                invoice_items.append({
                    'code': course.CourseID,
                    'title': course.CourseName,
                    'fee': 0.00 # Default to 0.00 if no fee record
                })
        
        # Add the general services fee to the total amount
        total_amount += general_services_fee
        
        student_data = Student.query.get(current_user.id)
        if student_data:
            student_details['name'] = f"{student_data.FirstName} {student_data.LastName}"
            student_details['id'] = student_data.StudentID
        else:
            student_details['name'] = current_user.username
            student_details['id'] = current_user.id

        # Generate a random invoice number
        invoice_details['number'] = f"INV-{uuid.uuid4().hex[:8].upper()}"
        invoice_details['date'] = datetime.now().strftime('%B %d, %Y')
        invoice_details['semester'] = 'Semester 2, 2025' # Still hardcoded
        student_fees_records = StudentCourseFee.query.filter_by(StudentID=current_user.id, status='Outstanding').first()
        if student_fees_records:
            invoice_details['payment_status'] = 'Pending'
        else:
            invoice_details['payment_status'] = 'Paid'


        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet() # Corrected typo here

        # Build PDF content
        elements.append(Paragraph("Invoice", styles['h1']))
        elements.append(Paragraph("University of the South Pacific", styles['h2']))
        elements.append(Paragraph(f"Invoice Number: {invoice_details['number']}", styles['Normal']))
        elements.append(Paragraph(f"Date: {invoice_details['date']}", styles['Normal']))
        elements.append(Paragraph(f"Semester: {invoice_details['semester']}", styles['Normal']))

        elements.append(Paragraph("Student Details", styles['h3']))
        elements.append(Paragraph(f"Name: {student_details['name']}", styles['Normal']))
        elements.append(Paragraph(f"ID: {student_details['id']}", styles['Normal']))

        # PDF Table data: Description, Fee
        data = [['Description', 'Fee']]
        for item in invoice_items:
            fee_display = f"${item['fee']:.2f}" if isinstance(item['fee'], (int, float)) else str(item['fee'])
            data.append([f"{item['title']} ({item['code']})", fee_display])
        
        # Add General Services Fee to the table
        data.append(['General Services Fee', f"${general_services_fee:.2f}"])

        data.append(['', 'Total:', f"${total_amount:.2f}"]) # Adjust Total row

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

@enrollment_bp.route('/course_fees_api/<string:fee_id>', methods=['GET']) # Changed to string as FeeID is string
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
    if not data or not all(k in data for k in ['FeeID', 'amount', 'CourseID']): # Added FeeID to required fields
        return jsonify({"message": "Missing course fee data (requires FeeID, amount, CourseID)"}), 400

    course = Course.query.get(data['CourseID'])
    if not course:
        return jsonify({"message": "Course not found"}), 404
    
    # Check if FeeID already exists
    existing_fee = CourseFee.query.get(data['FeeID'])
    if existing_fee:
        return jsonify({"message": "Course fee with this ID already exists"}), 409

    new_fee = CourseFee(
        FeeID=data['FeeID'], # Use the provided FeeID
        amount=data['amount'],
        description=data.get('description'), # description is optional
        CourseID=data['CourseID']
    )
    db.session.add(new_fee)
    try:
        db.session.commit()
        return jsonify({"message": "Course fee added successfully", "fee_id": new_fee.FeeID}), 201
    except IntegrityError: # Catch if FeeID conflicts
        db.session.rollback()
        return jsonify({"message": "Course fee with this ID already exists"}), 409
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding course fee: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/course_fees_api/<string:fee_id>', methods=['PUT']) # Changed to string as FeeID is string
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

@enrollment_bp.route('/course_fees_api/<string:fee_id>', methods=['DELETE']) # Changed to string as FeeID is string
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
    else: # admin, sas_manager
        student_fees = StudentCourseFee.query.options(
            db.joinedload(StudentCourseFee.student),
            db.joinedload(StudentCourseFee.course),
            db.joinedload(StudentCourseFee.course_fee)
        ).all()
    return jsonify([serialize_student_course_fee(sf) for sf in student_fees])

@enrollment_bp.route('/student_course_fees_api/<string:scf_id>', methods=['GET']) # Changed to string as StudentCourseFeeID is string
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
    if not data or not all(k in data for k in ['StudentCourseFeeID', 'StudentID', 'CourseID', 'amount', 'due_date']): # Added StudentCourseFeeID and amount
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
    
    # Check if StudentCourseFeeID already exists
    existing_scf_id = StudentCourseFee.query.get(data['StudentCourseFeeID'])
    if existing_scf_id:
        return jsonify({"message": "Student Course Fee with this ID already exists"}), 409


    new_student_fee = StudentCourseFee(
        StudentCourseFeeID=data['StudentCourseFeeID'], # Use the provided ID
        StudentID=data['StudentID'],
        CourseID=data['CourseID'],
        amount=data['amount'], # Use the provided amount
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

@enrollment_bp.route('/student_course_fees_api/<string:scf_id>', methods=['PUT']) # Changed to string as StudentCourseFeeID is string
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

    if 'amount' in data: # Allow amount to be updated
        student_fee.amount = data['amount']
    if 'due_date' in data:
        student_fee.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
    if 'paid_date' in data:
        student_fee.paid_date = datetime.strptime(data['paid_date'], '%Y-%m-%d').date() if data['paid_date'] else None
    if 'status' in data:
        student_fee.status = data['status']
    if 'FeeID' in data: # Allow FeeID to be updated
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

@enrollment_bp.route('/student_course_fees_api/<string:scf_id>', methods=['DELETE']) # Changed to string as StudentCourseFeeID is string
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

@enrollment_bp.route('/holds/<string:hold_id>', methods=['GET']) # Changed to string as HoldID is string
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
    if not data or not all(k in data for k in ['HoldID', 'StudentID', 'reason']): # Added HoldID
        return jsonify({"message": "Missing hold data (requires HoldID, StudentID, reason)"}), 400

    student = Student.query.get(data['StudentID'])
    if not student:
        return jsonify({"message": "Student not found"}), 404
    
    # Check if HoldID already exists
    existing_hold = Hold.query.get(data['HoldID'])
    if existing_hold:
        return jsonify({"message": "Hold with this ID already exists"}), 409


    new_hold = Hold(
        HoldID=data['HoldID'], # Use the provided HoldID
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
    except IntegrityError: # Catch if HoldID conflicts
        db.session.rollback()
        return jsonify({"message": "Hold with this ID already exists"}), 409
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding hold: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/holds/<string:hold_id>', methods=['PUT']) # Changed to string as HoldID is string
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
    if 'StudentID' in data: # Allow updating StudentID if necessary (though generally not recommended for existing records)
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

@enrollment_bp.route('/holds/<string:hold_id>', methods=['DELETE']) # Changed to string as HoldID is string
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
    
    # Check if StudentLevelID already exists
    existing_level = StudentLevel.query.get(data['StudentLevelID'])
    if existing_level:
        return jsonify({"message": "Student level with this ID already exists"}), 409

    new_student_level = StudentLevel(
        StudentLevelID=data['StudentLevelID'],
        StudentID=data['StudentID'],
        LevelName=data.get('LevelName'), # Added LevelName
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

    if 'LevelName' in data: # Allow LevelName to be updated
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