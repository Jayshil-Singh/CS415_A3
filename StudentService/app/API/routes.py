from flask import render_template, redirect, url_for, abort, request, session
from werkzeug.exceptions import HTTPException
from types import SimpleNamespace
import sqlite3
from datetime import datetime
import os

from app.API.auth import auth_bp, login_required, get_student_db_path  # your login/auth blueprint

def register_routes(app):
    """
    Registers all routes and error handlers with the Flask app instance.
    """

    # Optional: stub current_user everywhere
    @app.context_processor
    def inject_user():
        if 'username' in session:
            return {"current_user": SimpleNamespace(username=session['username'])}
        return {"current_user": SimpleNamespace(username="Student")}

    # 1) register the login/auth blueprint
    app.register_blueprint(auth_bp)

    # 2) redirect root → GET /login
    @app.route("/")
    def root():
        if 'user_id' not in session:
            return redirect(url_for("auth.login"))
        return redirect(url_for("home"))

    # Homepage
    @app.route("/home")
    @login_required
    def home():
        try:
            return render_template("homepage.html")
        except Exception:
            abort(500)

    # Student Profile
    @app.route("/profile")
    @login_required
    def student_profile():
        try:
            student_id = session.get('user_id')
            if not student_id:
                return redirect(url_for('auth.login'))

            # Connect to StudentService database
            db_path = get_student_db_path()
            if not os.path.exists(db_path):
                abort(500)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get student details
            cursor.execute("""
                SELECT StudentID, FirstName, MiddleName, LastName, 
                       Contact, Email, DateOfBirth, Gender, 
                       Citizenship, Address, PassportNumber, VisaStatus, VisaExpiryDate
                FROM Student
                WHERE StudentID = ?
            """, (student_id,))
            
            student_data = cursor.fetchone()
            if not student_data:
                abort(404)

            # Parse the data
            (student_id, first_name, middle_name, last_name, contact, email,
             dob, gender, citizenship, address, passport_number, visa_status, visa_expiry) = student_data

            # Split address into components (assuming format: "street, city, state, country, postal_code")
            address_parts = address.split(',') if address else ['', '', '', '', '']
            address_obj = SimpleNamespace(
                street=address_parts[0].strip() if len(address_parts) > 0 else '',
                city=address_parts[1].strip() if len(address_parts) > 1 else '',
                state=address_parts[2].strip() if len(address_parts) > 2 else '',
                country=address_parts[3].strip() if len(address_parts) > 3 else '',
                postal_code=address_parts[4].strip() if len(address_parts) > 4 else ''
            )

            # Create passport/visa object
            passport_visa_obj = SimpleNamespace(
                passport_number=passport_number or '',
                visa_status=visa_status or '',
                expiry_date=datetime.strptime(visa_expiry, '%Y-%m-%d').strftime('%Y-%m-%d') if visa_expiry else ''
            )

            # Create profile data object
            profile_data = SimpleNamespace(
                student_id=student_id,
                first_name=first_name,
                middle_name=middle_name or '',
                last_name=last_name,
                dob=datetime.strptime(dob, '%Y-%m-%d').strftime('%Y-%m-%d') if dob else '',
                gender=gender or '',
                citizenship=citizenship or '',
                email=email,
                phone=contact or '',
                address=address_obj,
                passport_visa=passport_visa_obj,
                profile_pic_url=url_for('static', filename='images/icon.png')
            )

            return render_template("studentProfile.html", profile_data=profile_data)

        except Exception as e:
            print(f"Error rendering studentProfile: {e}")
            abort(500)

        finally:
            if 'conn' in locals():
                conn.close()

    # My Enrollment
    @app.route("/myEnrollment")
    @login_required
    def my_enrollment():
        try:
            return render_template("myEnrollment.html")
        except Exception:
            abort(500)

    # Courses
    @app.route("/courses")
    @login_required
    def courses():
        try:
            return render_template("courses.html")
        except Exception:
            abort(500)

    # Finance
    @app.route("/finance")
    @login_required
    def finance():
        try:
            return render_template("finance.html")
        except Exception:
            abort(500)

    # Logout
    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("auth.login"))

    # Error Handlers
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
