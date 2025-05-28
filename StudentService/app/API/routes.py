from flask import render_template, redirect, url_for, abort
from werkzeug.exceptions import HTTPException
from types import SimpleNamespace

from app.API.auth import auth_bp  # your login/auth blueprint

def register_routes(app):
    """
    Registers all routes and error handlers with the Flask app instance.
    """

    # Optional: stub current_user everywhere
    @app.context_processor
    def inject_user():
        return {"current_user": SimpleNamespace(username="Student")}

    # 1) register the login/auth blueprint
    app.register_blueprint(auth_bp)

    # 2) redirect root → GET /login
    @app.route("/")
    def root():
        return redirect(url_for("auth.login"))

    # Homepage
    @app.route("/home")
    def home():
        try:
            return render_template("homepage.html")
        except Exception:
            abort(500)

    # Student Profile
    @app.route("/profile")
    def student_profile():
        try:
            profile_data = SimpleNamespace(
                student_id="S98765432",
                first_name="Alice",
                middle_name="M.",
                last_name="Smith",
                dob="2000-05-20",
                gender="Female",
                citizenship="Fijian",
                program="Bachelor of Arts in Literature",
                student_level="Undergraduate",
                student_campus="Laucala",
                email="s98765432@student.usp.ac.fj",
                phone="+679 9876543",
                address=SimpleNamespace(
                    street="456 Coral Way", city="Suva",
                    state="Central", country="Fiji", postal_code="0000"
                ),
                passport_visa=SimpleNamespace(
                    passport_number="FJ987654",
                    visa_status="Student Visa",
                    expiry_date="2028-11-15"
                ),
                profile_pic_url=url_for('static', filename='images/icon.png')
            )
            return render_template("studentProfile.html", profile_data=profile_data)
        except Exception as e:
            print(f"Error rendering studentProfile: {e}")
            abort(500)

    # My Enrollment
    @app.route("/myEnrollment")
    def my_enrollment():
        try:
            return render_template("myEnrollment.html")
        except Exception:
            abort(500)

    # Courses
    @app.route("/courses")
    def courses():
        try:
            return render_template("courses.html")
        except Exception:
            abort(500)

    # Finance
    @app.route("/finance")
    def finance():
        try:
            return render_template("finance.html")
        except Exception:
            abort(500)

    # Logout
    @app.route("/logout")
    def logout():
        try:
            return redirect(url_for("auth.login"))
        except Exception:
            abort(500)

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
