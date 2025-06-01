# File: StudentService/app/API/routes.py

from flask import (
    render_template, redirect, url_for, abort,
    request, flash, session, send_file, jsonify
)
from werkzeug.exceptions import HTTPException
from types import SimpleNamespace
import sqlite3
from datetime import datetime
import os
import io
from werkzeug.utils import secure_filename

from app.API.auth import auth_bp, login_required, get_db_path
from app.Core.models import (
    db, User, UserPhoto, Student, Program_Student, Program, 
    Addressing_Student, StudentLevel, ProgramType, SubProgram, 
    student_subprogram_association, Emergency_Contact, 
    BirthCertificate, ValidID, AcademicTranscript, Campus
)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
ALLOWED_EXTENSIONS = {
    'birth_certificate': {'pdf', 'docx'},
    'valid_id': {'pdf', 'docx', 'jpg', 'jpeg', 'png'},
    'academic_transcript': {'pdf', 'docx'}
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename, doc_type):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS[doc_type]

def register_routes(app):
    """
    Registers all routes and error handlers with the Flask app instance.
    """

    # ----------------------------------------------------------------
    # 1) Inject "current_user" into all templates
    # ----------------------------------------------------------------
    @app.context_processor
    def inject_user():
        # If the user is logged in, session['user_id'] and session['username'] exist.
        if 'user_id' in session and 'username' in session:
            u = SimpleNamespace(
                id=session['user_id'],
                username=session['username'],
                # We will attach profile_photo_url below (if they have an uploaded photo)
                profile_photo_url=url_for('static', filename='images/icon.png')
            )

            # Check if that user has any photos; if so, show the most recent
            latest = (
                UserPhoto.query
                .filter_by(student_id=u.id)
                .order_by(UserPhoto.uploaded_at.desc())
                .first()
            )
            if latest:
                u.profile_photo_url = url_for("serve_photo", photo_id=latest.id)

            return {"current_user": u}

        # If not logged in, return a very minimal "Guest" so templates don't break
        return {"current_user": SimpleNamespace(id=None, username="Guest", profile_photo_url=url_for('static', filename='images/icon.png'))}

    # ----------------------------------------------------------------
    # 2) Register the auth blueprint (login, register, etc.)
    # ----------------------------------------------------------------
    app.register_blueprint(auth_bp)

    # ----------------------------------------------------------------
    # 3) Root → redirect to login if not logged in, else to /home
    # ----------------------------------------------------------------
    @app.route("/")
    def root():
        if 'user_id' not in session:
            return redirect(url_for("auth.login"))
        return redirect(url_for("home"))

    # ----------------------------------------------------------------
    # 4) Homepage (protected)
    # ----------------------------------------------------------------
    @app.route("/home")
    @login_required
    def home():
        try:
            student_id = session.get('student_id')
            if not student_id:
                return redirect(url_for('auth.login'))
            
            student = Student.query.get_or_404(student_id)
            return render_template(
                "homepage.html",
                student_name=f"{student.FirstName} {student.LastName}"
            )
        except Exception as e:
            current_app.logger.error(f"Error in home route: {str(e)}")
            return render_template("errors/500.html"), 500

    # ----------------------------------------------------------------
    # 5) Document Upload Routes
    # ----------------------------------------------------------------
    @app.route('/upload_document', methods=['POST'])
    @login_required
    def upload_document():
        if 'action' not in request.form:
            flash('Invalid request', 'error')
            return redirect(url_for('profile'))

        action = request.form['action']
        student_id = session.get('student_id')
        
        if not student_id:
            flash('Please log in first', 'error')
            return redirect(url_for('login'))

        try:
            # Create upload folder for student if it doesn't exist
            student_folder = os.path.join(UPLOAD_FOLDER, str(student_id))
            os.makedirs(student_folder, exist_ok=True)

            if action == 'upload_birth_certificate':
                if 'birth_certificate' not in request.files:
                    flash('No file selected', 'error')
                    return redirect(url_for('profile'))
                
                file = request.files['birth_certificate']
                if file.filename == '':
                    flash('No file selected', 'error')
                    return redirect(url_for('profile'))

                if not allowed_file(file.filename, 'birth_certificate'):
                    flash('Invalid file type', 'error')
                    return redirect(url_for('profile'))

                # Create document folder
                doc_folder = os.path.join(student_folder, 'birth_certificate')
                os.makedirs(doc_folder, exist_ok=True)

                # Save file
                filename = secure_filename(file.filename)
                file_path = os.path.join(doc_folder, filename)
                file.save(file_path)

                # Remove existing birth certificate if any
                existing_doc = BirthCertificate.query.filter_by(StudentID=student_id).first()
                if existing_doc:
                    if os.path.exists(existing_doc.FilePath):
                        os.remove(existing_doc.FilePath)
                    db.session.delete(existing_doc)

                # Create new document
                new_doc = BirthCertificate(
                    StudentID=student_id,
                    FileName=filename,
                    FilePath=file_path,
                    VerificationStatus='Pending'
                )
                db.session.add(new_doc)

            elif action == 'upload_valid_id':
                if 'valid_id' not in request.files:
                    flash('No file selected', 'error')
                    return redirect(url_for('profile'))
                
                file = request.files['valid_id']
                id_type = request.form.get('id_type')

                if not all([file.filename, id_type]):
                    flash('Please fill all required fields', 'error')
                    return redirect(url_for('profile'))

                if not allowed_file(file.filename, 'valid_id'):
                    flash('Invalid file type', 'error')
                    return redirect(url_for('profile'))

                # Create document folder
                doc_folder = os.path.join(student_folder, 'valid_id')
                os.makedirs(doc_folder, exist_ok=True)

                # Save file
                filename = secure_filename(file.filename)
                file_path = os.path.join(doc_folder, filename)
                file.save(file_path)

                # Remove existing valid ID if any
                existing_doc = ValidID.query.filter_by(StudentID=student_id).first()
                if existing_doc:
                    if os.path.exists(existing_doc.FilePath):
                        os.remove(existing_doc.FilePath)
                    db.session.delete(existing_doc)

                # Create new document
                new_doc = ValidID(
                    StudentID=student_id,
                    FileName=filename,
                    FilePath=file_path,
                    IDType=id_type,
                    VerificationStatus='Pending'
                )
                db.session.add(new_doc)

            elif action == 'upload_academic_transcript':
                if 'academic_transcript' not in request.files:
                    flash('No file selected', 'error')
                    return redirect(url_for('profile'))
                
                file = request.files['academic_transcript']
                transcript_type = request.form.get('transcript_type')

                if not all([file.filename, transcript_type]):
                    flash('Please fill all required fields', 'error')
                    return redirect(url_for('profile'))

                if not allowed_file(file.filename, 'academic_transcript'):
                    flash('Invalid file type', 'error')
                    return redirect(url_for('profile'))

                # Create document folder
                doc_folder = os.path.join(student_folder, 'academic_transcript')
                os.makedirs(doc_folder, exist_ok=True)

                # Save file
                filename = secure_filename(file.filename)
                file_path = os.path.join(doc_folder, filename)
                file.save(file_path)

                # Remove existing transcript if any
                existing_doc = AcademicTranscript.query.filter_by(StudentID=student_id).first()
                if existing_doc:
                    if os.path.exists(existing_doc.FilePath):
                        os.remove(existing_doc.FilePath)
                    db.session.delete(existing_doc)

                # Create new document
                new_doc = AcademicTranscript(
                    StudentID=student_id,
                    FileName=filename,
                    FilePath=file_path,
                    TranscriptType=transcript_type,
                    VerificationStatus='Pending'
                )
                db.session.add(new_doc)

            elif action in ['remove_birth_certificate', 'remove_valid_id', 'remove_academic_transcript']:
                model_map = {
                    'remove_birth_certificate': BirthCertificate,
                    'remove_valid_id': ValidID,
                    'remove_academic_transcript': AcademicTranscript
                }
                model = model_map[action]
                document = model.query.filter_by(StudentID=student_id).first()
                if document:
                    if os.path.exists(document.FilePath):
                        os.remove(document.FilePath)
                    db.session.delete(document)
                else:
                    flash('Document not found', 'error')
                    return redirect(url_for('profile'))

            db.session.commit()
            flash('Document updated successfully', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Error processing document: {str(e)}', 'error')

        return redirect(url_for('profile'))

    # ----------------------------------------------------------------
    # 6) Profile Routes
    # ----------------------------------------------------------------
    @app.route('/profile')
    @login_required
    def profile():
        if 'student_id' not in session:
            return redirect(url_for('login'))
            
        try:
            student_id = session['student_id']
            print(f"Session data: {session}")  # Debug print
            print(f"Loading profile for student ID: {student_id}")  # Debug print
            
            # Get emergency contact information
            emergency_contact = None
            try:
                # Use SQLAlchemy to get emergency contact
                ec = Emergency_Contact.query.filter_by(StudentID=student_id).first()
                print(f"Student ID being queried: {student_id}")  # Debug print
                print(f"Emergency contact query result: {ec}")  # Debug print
                
                if ec:
                    emergency_contact = {
                        'FirstName': ec.FirstName,
                        'MiddleName': ec.MiddleName,
                        'LastName': ec.LastName,
                        'Relationship': ec.Relationship,
                        'ContactPhone': ec.ContactPhone
                    }
                    print(f"Emergency contact data created: {emergency_contact}")  # Debug print
                else:
                    print("No emergency contact found for this student")  # Debug print
                
            except Exception as e:
                print(f"Error accessing emergency contact data: {str(e)}")  # Debug print
                app.logger.error(f"Error accessing emergency contact data: {str(e)}")
            
            student = Student.query.get_or_404(student_id)
            student_level = StudentLevel.query.filter_by(StudentID=student_id).first()
            campus = Campus.query.get(student.CampusID) if student.CampusID else None
            
            # Get program enrollment (updated query)
            program_enrollment = db.session.query(
                Program_Student,
                Program
            ).join(
                Program, Program_Student.ProgramID == Program.ProgramID
            ).filter(
                Program_Student.StudentID == student_id
            ).first()
            
            # Get subprogram enrollments
            subprogram_enrollments = db.session.query(
                student_subprogram_association,
                SubProgram
            ).join(
                SubProgram,
                student_subprogram_association.c.SubProgramID == SubProgram.SubProgramID
            ).filter(
                student_subprogram_association.c.StudentID == student_id
            ).all()
            
            # Get address information
            address = {
                'street': student.Address,
                'state': student.address_info.Province if student.address_info else None,
                'country': student.address_info.Country if student.address_info else None,
                'postal_code': student.address_info.ZipCode if student.address_info else None
            }
            
            # Get passport/visa information
            passport_visa = {
                'passport_number': student.PassportNumber,
                'visa_status': student.VisaStatus,
                'expiry_date': student.VisaExpiryDate.strftime('%Y-%m-%d') if student.VisaExpiryDate else None
            }

            profile_data = {
                'student_id': student_id,
                'first_name': student.FirstName,
                'middle_name': student.MiddleName,
                'last_name': student.LastName,
                'email': student.Email,
                'phone': student.Contact,
                'dob': student.DateOfBirth.strftime('%Y-%m-%d') if student.DateOfBirth else '',
                'gender': student.Gender.value if student.Gender else '',
                'citizenship': student.Citizenship,
                
                # Academic details
                'student_level': student_level.Level.value if student_level and student_level.Level else '',
                'student_campus': campus.CampusName if campus else '',
                'program': program_enrollment[1].ProgramName if program_enrollment else '',
                'subprograms': ', '.join(sp[1].SubProgramName for sp in subprogram_enrollments) if subprogram_enrollments else '',
                
                # Address and contact
                'address': address,
                
                # Passport/Visa
                'passport_visa': passport_visa,

                # Emergency Contact
                'emergency_contact': emergency_contact
            }
            
            print("Debug: Emergency contact before template:", emergency_contact)  # Debug print
            print("Debug: Full profile data:", profile_data)  # Debug print
            return render_template('studentProfile.html', profile_data=profile_data)
            
        except Exception as e:
            print(f"Error in profile route: {str(e)}")  # Debug print
            flash(f'Error loading profile: {str(e)}', 'error')
            return redirect(url_for('login'))

    # ----------------------------------------------------------------
    # 7) Document Verification Routes
    # ----------------------------------------------------------------
    @app.route('/verify_document/<doc_type>/<int:doc_id>', methods=['POST'])
    def verify_document(doc_type, doc_id):
        # Only allow SAS staff to verify documents
        if 'role' not in session or session['role'] != 'sas_staff':
            return jsonify({'error': 'Access denied'}), 403

        if doc_type == 'birth_certificate':
            doc = BirthCertificate.query.get(doc_id)
        elif doc_type == 'valid_id':
            doc = ValidID.query.get(doc_id)
        elif doc_type == 'academic_transcript':
            doc = AcademicTranscript.query.get(doc_id)
        else:
            return jsonify({'error': 'Invalid document type'}), 400
        
        if not doc:
            return jsonify({'error': 'Document not found'}), 404
        
        doc.VerificationStatus = 'Verified'
        db.session.commit()
        
        return jsonify({'message': 'Document verified successfully'}), 200

    # ----------------------------------------------------------------
    # Other routes
    # ----------------------------------------------------------------
    @app.route("/profile/photo/<int:photo_id>")
    @login_required
    def serve_photo(photo_id):
        photo = UserPhoto.query.get_or_404(photo_id)
        return send_file(
            io.BytesIO(photo.data),
            mimetype=photo.mimetype
        )

    @app.route("/myEnrollment")
    @login_required
    def my_enrollment():
        try:
            return render_template("my_enrollment.html")
        except Exception:
            abort(500)

    @app.route("/courses")
    @login_required
    def courses():
        try:
            return render_template("courses.html")
        except Exception:
            abort(500)

    @app.route("/finance")
    @login_required
    def finance():
        try:
            return render_template("finance.html")
        except Exception:
            abort(500)

    @app.route("/logout")
    def logout():
        session.clear()
        flash('You have been logged out.', 'info')
        return redirect(url_for('auth.login'))

    @app.route("/gradeRecheck")
    @login_required
    def grade_recheck():
        try:
            return render_template("grade_recheck.html")
        except Exception:
            abort(500)

    @app.route("/specialApplications")
    @login_required
    def special_applications():
        try:
            return render_template("special_applications.html")
        except Exception:
            abort(500)

    @app.route("/holdsAccess")
    @login_required
    def holds_access():
        try:
            return render_template("holds_access.html")
        except Exception:
            abort(500)

    @app.route("/transcript")
    @login_required
    def transcript():
        try:
            return render_template("transcript.html")
        except Exception:
            abort(500)

    @app.route("/copyright")
    def copyright_page():
        return render_template("copyright.html")

    @app.route("/contact")
    def contact_page():
        return render_template("contact.html")

    # ----------------------------------------------------------------
    # Error handlers
    # ----------------------------------------------------------------
    @app.errorhandler(404)
    def handle_404(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def handle_500(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(Exception)
    def handle_all_exceptions(e):
        if isinstance(e, HTTPException):
            return render_template('errors/generic.html', error=e), e.code
        return render_template('errors/500.html'), 500 