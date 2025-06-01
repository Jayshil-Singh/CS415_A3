# File: StudentService/app/API/routes.py

from flask import (
    render_template, redirect, url_for, abort,
    request, flash, session
)
from werkzeug.exceptions import HTTPException
from types import SimpleNamespace
import sqlite3
from datetime import datetime
import os

from app.API.auth import auth_bp, login_required, get_student_db_path
from app.Core.models import db, User, UserPhoto, Student


def register_routes(app):
    """
    Registers all routes and error handlers with the Flask app instance.
    """

    # ----------------------------------------------------------------
    # 1) Inject “current_user” into all templates
    # ----------------------------------------------------------------
    @app.context_processor
    def inject_user():
        # If the user is logged in, session['user_id'] and session['username'] exist.
        if 'user_id' in session and 'username' in session:
            u = SimpleNamespace(
                id            = session['user_id'],
                username      = session['username'],
                # We will attach profile_photo_url below (if they have an uploaded photo)
                profile_photo_url = url_for('static', filename='images/icon.png')
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

        # If not logged in, return a very minimal “Guest” so templates don’t break
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
            return render_template("homepage.html")
        except Exception:
            abort(500)


    # ----------------------------------------------------------------
    # 5) Student Profile (GET: show page with real student data; 
    #                   POST: upload/remove photo)
    # ----------------------------------------------------------------
    @app.route("/profile", methods=["GET", "POST"])
    @login_required
    def student_profile():
        # 1) Determine which student is logged in
        student_id = session.get('user_id')
        if not student_id:
            flash("Please log in to view your profile.", "error")
            return redirect(url_for("auth.login"))

        # 2) For POST: handle upload or removal of photo
        if request.method == "POST":
            action = request.form.get("action", "save")

            if action == "remove":
                # Delete all photos for this student
                UserPhoto.query.filter_by(student_id=student_id).delete()
                db.session.commit()
                flash("Profile photo removed.", "success")
                return redirect(url_for("student_profile"))

            # Otherwise, action == "save": handle a new upload
            file = request.files.get("photo")
            if file and file.filename:
                filename = file.filename
                mime_type = file.mimetype
                blob_data = file.read()

                new_photo = UserPhoto(
                    student_id = student_id,
                    filename   = filename,
                    mime_type  = mime_type,
                    data       = blob_data
                    # uploaded_at will default to datetime.utcnow()
                )
                db.session.add(new_photo)
                db.session.commit()
                flash("Profile photo updated.", "success")
            else:
                flash("Please select an image file to upload.", "error")

            return redirect(url_for("student_profile"))

        # 3) For GET: fetch student details from Yash’s Student table via raw sqlite3
        db_path = get_student_db_path()
        if not os.path.exists(db_path):
            abort(500)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT StudentID, FirstName, MiddleName, LastName,
                       Contact, Email, DateOfBirth, Gender,
                       Citizenship, Address, PassportNumber, VisaStatus, VisaExpiryDate
                FROM Student
                WHERE StudentID = ?
            """, (student_id,))
            row = cursor.fetchone()
            if not row:
                abort(404)

            (sid, first_name, middle_name, last_name, contact, email,
             dob, gender, citizenship, address, passport_number, visa_status, visa_expiry) = row

            # Split address (stored as "street, city, state, country, postal_code")
            address_parts = address.split(',') if address else ['', '', '', '', '']
            address_obj = SimpleNamespace(
                street      = address_parts[0].strip() if len(address_parts) > 0 else '',
                city        = address_parts[1].strip() if len(address_parts) > 1 else '',
                state       = address_parts[2].strip() if len(address_parts) > 2 else '',
                country     = address_parts[3].strip() if len(address_parts) > 3 else '',
                postal_code = address_parts[4].strip() if len(address_parts) > 4 else ''
            )

            # Build passport/visa object
            visa_expiry_str = ""
            if visa_expiry:
                try:
                    visa_expiry_str = datetime.strptime(visa_expiry, '%Y-%m-%d').strftime('%Y-%m-%d')
                except Exception:
                    visa_expiry_str = visa_expiry

            passport_visa_obj = SimpleNamespace(
                passport_number = passport_number or '',
                visa_status     = visa_status or '',
                expiry_date     = visa_expiry_str
            )

            # Fetch latest photo (if any) via SQLAlchemy
            latest = (
                UserPhoto.query
                .filter_by(student_id=student_id)
                .order_by(UserPhoto.uploaded_at.desc())
                .first()
            )

            # Assemble profile_data for the template
            profile_data = SimpleNamespace(
                student_id     = sid,
                username       = session.get('username', ''),
                email          = email or session.get('email', ''),
                role           = session.get('role', ''),

                # Actual personal details from the Student row
                first_name     = first_name,
                middle_name    = middle_name or '',
                last_name      = last_name,
                dob            = dob or '',
                gender         = gender or '',
                citizenship    = citizenship or '',

                # (If you have program/campus/level, add them here; using stubs if not)
                program        = None,
                student_level  = None,
                student_campus = None,

                phone          = contact or '',

                address        = address_obj,

                passport_visa  = passport_visa_obj,

                # photo ID (or None)
                profile_pic_id = latest.id if latest else None
            )

        except Exception as e:
            print(f"Error fetching student data: {e}")
            abort(500)

        finally:
            conn.close()

        return render_template("studentProfile.html", profile_data=profile_data)


    # ----------------------------------------------------------------
    # 6) Serve photo blobs
    # ----------------------------------------------------------------
    @app.route("/profile/photo/<int:photo_id>")
    @login_required
    def serve_photo(photo_id):
        photo = UserPhoto.query.get_or_404(photo_id)
        return (
            photo.data, 200,
            {
                "Content-Type": photo.mime_type,
                "Content-Disposition": f'inline; filename="{photo.filename}"'
            }
        )


    # ----------------------------------------------------------------
    # 7) My Enrollment (protected)
    # ----------------------------------------------------------------
    @app.route("/myEnrollment")
    @login_required
    def my_enrollment():
        try:
            return render_template("myEnrollment.html")
        except Exception:
            abort(500)


    # ----------------------------------------------------------------
    # 8) Courses (protected)
    # ----------------------------------------------------------------
    @app.route("/courses")
    @login_required
    def courses():
        try:
            return render_template("courses.html")
        except Exception:
            abort(500)


    # ----------------------------------------------------------------
    # 9) Finance (protected)
    # ----------------------------------------------------------------
    @app.route("/finance")
    @login_required
    def finance():
        try:
            return render_template("finance.html")
        except Exception:
            abort(500)


    # ----------------------------------------------------------------
    # 10) Logout
    # ----------------------------------------------------------------
    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("auth.login"))


    # ----------------------------------------------------------------
    # 11) Grade Recheck (protected)
    # ----------------------------------------------------------------
    @app.route("/gradeRecheck")
    @login_required
    def grade_recheck():
        try:
            return render_template("gradeRecheck.html")
        except Exception:
            abort(500)


    # ----------------------------------------------------------------
    # 12) Special Applications (protected)
    # ----------------------------------------------------------------
    @app.route("/specialApplications")
    @login_required
    def special_applications():
        try:
            return render_template("specialApplications.html")
        except Exception:
            abort(500)


    # ----------------------------------------------------------------
    # 13) Holds Access (protected)
    # ----------------------------------------------------------------
    @app.route("/holdsAccess")
    @login_required
    def holds_access():
        try:
            return render_template("holds&studentAccess.html")
        except Exception:
            abort(500)


    # ----------------------------------------------------------------
    # 14) Transcript (protected)
    # ----------------------------------------------------------------
    @app.route("/transcript")
    @login_required
    def transcript():
        try:
            return render_template("academicTranscript.html")
        except Exception:
            abort(500)


    # ----------------------------------------------------------------
    # 15) Copyright & Contact (unprotected)
    # ----------------------------------------------------------------
    @app.route("/copyright")
    def copyright_page():
        try:
            return render_template("copyright.html")
        except Exception:
            abort(500)

    @app.route("/contact")
    def contact_page():
        try:
            return render_template("contact.html")
        except Exception:
            abort(500)


    # ----------------------------------------------------------------
    # 16) Error Handlers
    # ----------------------------------------------------------------
    @app.errorhandler(404)
    def handle_404(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def handle_500(e):
        return render_template("errors/500.html"), 500

    @app.errorhandler(Exception)
    def handle_all_exceptions(e):
        if isinstance(e, HTTPException):
            return e
        return render_template("errors/500.html"), 500
