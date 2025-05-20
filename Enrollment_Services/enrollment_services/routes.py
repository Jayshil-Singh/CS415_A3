# enrollment_services/routes.py
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session, send_file, make_response
import logging
from io import BytesIO # For in-memory PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import datetime
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.orm import joinedload # For eager loading relationships

# Import db and models from your package. These assume db.py and model.py exist in the same directory.
from .db import db
from .model import (
    Program, SubProgram, Semester, Course, CourseAvailability,
    Student, StudentLevel, Hold,
    Enrollment, CourseFee, StudentCourseFee
)

# --- Blueprint Initialization ---
# Create a Blueprint for all enrollment service routes.
# 'enrollment' is the blueprint's name, used for url_for.
# '__name__' tells Flask where to find resources relative to this file.
# 'template_folder' specifies where to find HTML templates relative to this blueprint's root.
enrollment_bp = Blueprint('enrollment', __name__, template_folder='templates')

# --- Logging Setup ---
# Configure basic logging to catch errors.
logging.basicConfig(level=logging.ERROR)

# --- Mock Data (IMPORTANT: To be Replaced with Actual Database Interactions) ---
# These global variables currently simulate data that would typically be fetched
# dynamically from your SQLite database using SQLAlchemy ORM.
# For demonstration purposes, they allow the frontend routes to function.

# Simulates courses completed by the logged-in student.
student_completed_courses = {'CS111'}

def get_mock_courses_data():
    """
    This function currently returns hardcoded course data.
    In a production application, this should be replaced with database queries
    to fetch 'Course' entities along with their 'SubProgram', 'CourseAvailability',
    'CourseFee', and 'PrerequisiteCourse' relationships.
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

# Mock student details and invoice details.
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

# --- Helper Functions for Data Processing ---

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

# --- Serialization Functions for API Responses ---

def serialize_program(program):
    return {
        "ProgramID": program.ProgramID,
        "ProgramName": program.ProgramName,
        # The SubProgramID here should be carefully considered based on the ERD.
        # If Program.SubProgramID is a composite PK part, or a FK, ensure its purpose.
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


# --- Frontend-facing Routes (HTML Rendering) ---

@enrollment_bp.route('/')
@enrollment_bp.route('/dashboard')
def dashboard():
    """Renders the dashboard page."""
    return render_template('dashboard.html')

@enrollment_bp.route('/enroll', methods=['GET', 'POST'])
def enroll():
    try:
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
def display_courses():
    """Displays the courses currently selected/enrolled by the student (from session)."""
    try:
        courses_data = get_mock_courses_data()
        enrolled_courses_codes = session.get('enrolled_courses', [])
        enrolled_courses = [course_mock for course_mock in courses_data if course_mock['code'] in enrolled_courses_codes]
        return render_template('display_courses.html', enrolled_courses=enrolled_courses)
    except Exception as e:
        logging.error(f"Error in /display_courses: {e}")
        return render_template('500.html'), 500

@enrollment_bp.route('/drop_course/<course_code>')
def drop_course(course_code):
    """Allows a student to drop a course from their current session enrollment."""
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
def fees():
    """Renders the fees overview page, showing calculated invoice details."""
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
def download_invoice_pdf():
    """Generates and provides a PDF download of the invoice."""
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
    return render_template('404.html'), 404

# --- API Endpoints (JSON Responses) ---

# Program Endpoints
@enrollment_bp.route('/programs', methods=['GET'])
def get_programs():
    """Retrieves all programs from the database."""
    programs = Program.query.all()
    return jsonify([serialize_program(p) for p in programs])

@enrollment_bp.route('/programs/<string:program_id>', methods=['GET'])
def get_program(program_id):
    """Retrieves a single program by its ID."""
    program = Program.query.get(program_id)
    if not program:
        return jsonify({"message": "Program not found"}), 404
    return jsonify(serialize_program(program))

@enrollment_bp.route('/programs', methods=['POST'])
def add_program():
    """Adds a new program to the database."""
    data = request.json
    if not data or not all(k in data for k in ['ProgramID', 'ProgramName', 'SubProgramID']):
        return jsonify({"message": "Missing program data (requires ProgramID, ProgramName, SubProgramID)"}), 400

    new_program = Program(
        ProgramID=data['ProgramID'],
        ProgramName=data['ProgramName'],
        SubProgramID=data['SubProgramID']
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
def update_program(program_id):
    """Updates an existing program by its ID."""
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
def delete_program(program_id):
    """Deletes a program by its ID."""
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
def get_subprograms():
    """Retrieves all subprograms from the database."""
    subprograms = SubProgram.query.all()
    return jsonify([serialize_subprogram(s) for s in subprograms])

@enrollment_bp.route('/subprograms/<string:subprogram_id>', methods=['GET'])
def get_subprogram(subprogram_id):
    """Retrieves a single subprogram by its ID."""
    subprogram = SubProgram.query.get(subprogram_id)
    if not subprogram:
        return jsonify({"message": "SubProgram not found"}), 404
    return jsonify(serialize_subprogram(subprogram))

@enrollment_bp.route('/subprograms', methods=['POST'])
def add_subprogram():
    """Adds a new subprogram to the database."""
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
def update_subprogram(subprogram_id):
    """Updates an existing subprogram by its ID."""
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
def delete_subprogram(subprogram_id):
    """Deletes a subprogram by its ID."""
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
def get_semesters():
    """Retrieves all semesters from the database."""
    semesters = Semester.query.all()
    return jsonify([serialize_semester(s) for s in semesters])

@enrollment_bp.route('/semesters/<string:semester_id>', methods=['GET'])
def get_semester(semester_id):
    """Retrieves a single semester by its ID."""
    semester = Semester.query.get(semester_id)
    if not semester:
        return jsonify({"message": "Semester not found"}), 404
    return jsonify(serialize_semester(semester))

@enrollment_bp.route('/semesters', methods=['POST'])
def add_semester():
    """Adds a new semester to the database."""
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
def update_semester(semester_id):
    """Updates an existing semester by its ID."""
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
def delete_semester(semester_id):
    """Deletes a semester by its ID."""
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


# Student Endpoints
@enrollment_bp.route('/students', methods=['GET'])
def get_students():
    """Retrieves all students from the database."""
    students = Student.query.all()
    return jsonify([serialize_student(s) for s in students])

@enrollment_bp.route('/students', methods=['POST'])
def create_student():
    """Creates a new student record in the database."""
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
def get_student(student_id):
    """Retrieves a single student by their ID."""
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"message": "Student not found"}), 404
    return jsonify(serialize_student(student))

@enrollment_bp.route('/students/<string:student_id>', methods=['PUT'])
def update_student(student_id):
    """Updates an existing student's details."""
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"message": "Student not found"}), 404

    data = request.json
    if not data:
        return jsonify({"message": "No data provided for update"}), 400

    if 'FirstName' in data:
        student.FirstName = data['FirstName']
    if 'LastName' in data:
        student.LastName = data['LastName']
    if 'Email' in data:
        if Student.query.filter(Student.Email == data['Email'], Student.StudentID != student_id).first():
            return jsonify({"message": "Email already registered to another student"}), 409
        student.Email = data['Email']

    try:
        db.session.commit()
        return jsonify({"message": "Student updated successfully", "student_id": student.StudentID}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating student {student_id}: {e}")
        return jsonify({"message": "Internal server error: " + str(e)}), 500

@enrollment_bp.route('/students/<string:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Deletes a student and associated records (enrollments, fees, holds, levels)."""
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
@enrollment_bp.route('/courses_api', methods=['GET'])
def get_courses_api():
    """Retrieves all courses with their subprogram and availability details."""
    courses = Course.query.options(db.joinedload(Course.subprogram), db.joinedload(Course.course_availabilities).joinedload(CourseAvailability.semester)).all()
    return jsonify([serialize_course(course) for course in courses])

@enrollment_bp.route('/courses_api/<string:course_id>', methods=['GET'])
def get_course_api(course_id):
    """Retrieves a single course by its ID with subprogram and availability details."""
    course = Course.query.options(db.joinedload(Course.subprogram), db.joinedload(Course.course_availabilities).joinedload(CourseAvailability.semester)).get(course_id)
    if not course:
        return jsonify({"message": "Course not found"}), 404
    return jsonify(serialize_course(course))

@enrollment_bp.route('/courses_api', methods=['POST'])
def add_course_api():
    """Adds a new course to the database."""
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
def update_course_api(course_id):
    """Updates an existing course by its ID."""
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
def delete_course_api(course_id):
    """Deletes a course by its ID."""
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
def get_course_availabilities():
    """Retrieves all course availabilities, with related course and semester details."""
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
def get_course_availability(ca_id):
    """Retrieves a single course availability by its ID."""
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
def add_course_availability():
    """Adds a new course availability record."""
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
def update_course_availability(ca_id):
    """Updates an existing course availability record."""
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
def delete_course_availability(ca_id):
    """Deletes a course availability record."""
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

# Enrollment Endpoints
@enrollment_bp.route('/enrollments_api', methods=['GET'])
def get_enrollments_api():
    """Retrieves all enrollments with related student and course details."""
    enrollments = Enrollment.query.options(db.joinedload(Enrollment.student), db.joinedload(Enrollment.course)).all()
    return jsonify([serialize_enrollment(e) for e in enrollments])

@enrollment_bp.route('/enrollments_api/<string:enrollment_id>', methods=['GET'])
def get_enrollment_api(enrollment_id):
    """Retrieves a single enrollment by its ID."""
    enrollment = Enrollment.query.options(db.joinedload(Enrollment.student), db.joinedload(Enrollment.course)).get(enrollment_id)
    if not enrollment:
        return jsonify({"message": "Enrollment not found"}), 404
    return jsonify(serialize_enrollment(enrollment))

@enrollment_bp.route('/enrollments_api', methods=['POST'])
def create_enrollment_api():
    """Creates a new enrollment record."""
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
def update_enrollment_api(enrollment_id):
    """Updates an existing enrollment record."""
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
def delete_enrollment_api(enrollment_id):
    """Deletes an enrollment record."""
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
def get_course_fees_api():
    """Retrieves all course fees with related course details."""
    fees = CourseFee.query.options(db.joinedload(CourseFee.course)).all()
    return jsonify([serialize_course_fee(f) for f in fees])

@enrollment_bp.route('/course_fees_api/<int:fee_id>', methods=['GET'])
def get_course_fee_api(fee_id):
    """Retrieves a single course fee by its ID."""
    fee = CourseFee.query.options(db.joinedload(CourseFee.course)).get(fee_id)
    if not fee:
        return jsonify({"message": "Course fee not found"}), 404
    return jsonify(serialize_course_fee(fee))

@enrollment_bp.route('/course_fees_api', methods=['POST'])
def add_course_fee_api():
    """Adds a new course fee record."""
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
def update_course_fee_api(fee_id):
    """Updates an existing course fee record."""
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
def delete_course_fee_api(fee_id):
    """Deletes a course fee record."""
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
def get_student_course_fees_api():
    """Retrieves all student course fee records with related student, course, and course fee details."""
    student_fees = StudentCourseFee.query.options(
        db.joinedload(StudentCourseFee.student),
        db.joinedload(StudentCourseFee.course),
        db.joinedload(StudentCourseFee.course_fee)
    ).all()
    return jsonify([serialize_student_course_fee(sf) for sf in student_fees])

@enrollment_bp.route('/student_course_fees_api/<int:scf_id>', methods=['GET'])
def get_student_course_fee_api(scf_id):
    """Retrieves a single student course fee record by its ID."""
    student_fee = StudentCourseFee.query.options(
        db.joinedload(StudentCourseFee.student),
        db.joinedload(StudentCourseFee.course),
        db.joinedload(StudentCourseFee.course_fee)
    ).get(scf_id)
    if not student_fee:
        return jsonify({"message": "Student course fee not found"}), 404
    return jsonify(serialize_student_course_fee(student_fee))

@enrollment_bp.route('/student_course_fees_api', methods=['POST'])
def assign_student_course_fee_api():
    """Assigns a course fee to a specific student for a specific course."""
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
def update_student_course_fee_api(scf_id):
    """Updates an existing student course fee record."""
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
def delete_student_course_fee_api(scf_id):
    """Deletes a student course fee record."""
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
def get_holds():
    """Retrieves all hold records with related student details."""
    holds = Hold.query.options(db.joinedload(Hold.student)).all()
    return jsonify([serialize_hold(h) for h in holds])

@enrollment_bp.route('/holds/<int:hold_id>', methods=['GET'])
def get_hold(hold_id):
    """Retrieves a single hold record by its ID."""
    hold = Hold.query.options(db.joinedload(Hold.student)).get(hold_id)
    if not hold:
        return jsonify({"message": "Hold not found"}), 404
    return jsonify(serialize_hold(hold))

@enrollment_bp.route('/holds', methods=['POST'])
def add_hold():
    """Adds a new hold record for a student."""
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
def update_hold(hold_id):
    """Updates an existing hold record."""
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
def delete_hold(hold_id):
    """Deletes a hold record."""
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
def get_student_levels():
    """Retrieves all student level records with related student details."""
    student_levels = StudentLevel.query.options(db.joinedload(StudentLevel.student)).all()
    return jsonify([serialize_student_level(sl) for sl in student_levels])

@enrollment_bp.route('/student_levels/<string:student_level_id>', methods=['GET'])
def get_student_level(student_level_id):
    """Retrieves a single student level record by its ID."""
    student_level = StudentLevel.query.options(db.joinedload(StudentLevel.student)).get(student_level_id)
    if not student_level:
        return jsonify({"message": "Student level not found"}), 404
    return jsonify(serialize_student_level(student_level))

@enrollment_bp.route('/student_levels', methods=['POST'])
def add_student_level():
    """Adds a new student level record."""
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
def update_student_level(student_level_id):
    """Updates an existing student level record."""
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
def delete_student_level(student_level_id):
    """Deletes a student level record."""
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