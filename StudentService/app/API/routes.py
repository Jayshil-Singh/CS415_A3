# app/API/routes.py

from flask import (
    render_template, redirect, url_for, abort,
    request, flash
)
from werkzeug.exceptions import HTTPException
from types import SimpleNamespace

from app.API.auth import auth_bp
from app.Core.model import db, User, UserPhoto

def register_routes(app):
    """
    Registers all routes and error handlers with the Flask app instance.
    """

    # ----------------------------------------------------------------
    # 1) Inject a “current_user” into all templates
    # ----------------------------------------------------------------
    @app.context_processor
    def inject_user():
        # get first (demo) user
        user = User.query.first()

        if not user:
            # no real user yet → show Guest + no photo
            user = SimpleNamespace(
                id=None,
                username="Guest",
                profile_photo_url=url_for('static', filename='images/icon.png')
            )
        else:
            # fetch their most recent photo
            latest = (
                UserPhoto.query
                .filter_by(user_id=user.id)
                .order_by(UserPhoto.uploaded_at.desc())
                .first()
            )

            if latest:
                # build a URL pointing to our blob‐serving route
                user.profile_photo_url = url_for("serve_photo", photo_id=latest.id)
            else:
                # no upload yet → fallback
                user.profile_photo_url = url_for('static', filename='images/icon.png')

        return {"current_user": user}

    # ----------------------------------------------------------------
    # 2) Register the auth blueprint (login, verify, etc.)
    # ----------------------------------------------------------------
    app.register_blueprint(auth_bp)

    # ----------------------------------------------------------------
    # 3) Root → login redirect
    # ----------------------------------------------------------------
    @app.route("/")
    def root():
        return redirect(url_for("auth.login"))

    # ----------------------------------------------------------------
    # 4) Homepage
    # ----------------------------------------------------------------
    @app.route("/home")
    def home():
        try:
            return render_template("homepage.html")
        except Exception:
            abort(500)

    # ----------------------------------------------------------------
    # 5) Student Profile (GET shows page; POST handles upload/remove)
    # ----------------------------------------------------------------
    @app.route("/profile", methods=["GET", "POST"])
    def student_profile():
        # fetch our single user record
        user = User.query.first()
        if not user:
            flash("No student account found. Please register first.", "error")
            return redirect(url_for("auth.login"))

        if request.method == "POST":
            # determine which button was clicked
            action = request.form.get("action", "save")

            if action == "remove":
                # remove all photos for this user
                UserPhoto.query.filter_by(user_id=user.id).delete()
                db.session.commit()
                flash("Profile photo removed.", "success")
                return redirect(url_for("student_profile"))

            # else action=="save" → handle upload
            file = request.files.get("photo")
            if file and file.filename:
                photo = UserPhoto(
                    user_id   = user.id,
                    filename  = file.filename,
                    mime_type = file.mimetype,
                    data      = file.read()
                )
                db.session.add(photo)
                db.session.commit()
                flash("Profile photo updated.", "success")
            else:
                flash("Please select an image file to upload.", "error")

            return redirect(url_for("student_profile"))

        # on GET: retrieve the most recent photo
        latest = (
            UserPhoto.query
            .filter_by(user_id=user.id)
            .order_by(UserPhoto.uploaded_at.desc())
            .first()
        )

        # build a minimal namespace for ALL the template fields
        profile_data = SimpleNamespace(
            student_id     = user.id,
            username       = user.username,
            email          = user.email,
            role           = user.role,

            # --- STUBS for personal details ---
            first_name     = "Alice",
            middle_name    = "M.",
            last_name      = "Smith",
            dob            = "2000-05-20",
            gender         = "Female",
            citizenship    = "Fijian",

            # --- STUBS for academic details ---
            program        = "Bachelor of Arts in Literature",
            student_level  = "Undergraduate",
            student_campus = "Laucala",

            # --- STUBS for email & phone ---
            phone          = "+679 9876543",

            # --- STUB for address (nested) ---
            address = SimpleNamespace(
                street      = "456 Coral Way",
                city        = "Suva",
                state       = "Central",
                country     = "Fiji",
                postal_code = "0000"
            ),

            # --- STUB for passport & visa (nested) ---
            passport_visa = SimpleNamespace(
                passport_number = "FJ987654",
                visa_status     = "Student Visa",
                expiry_date     = "2028-11-15"
            ),

            # --- profile photo id for <img> src —
            profile_pic_id = latest.id if latest else None
        )

        return render_template(
            "studentProfile.html",
            profile_data=profile_data
        )

    # ----------------------------------------------------------------
    # 6) Serve photo blobs
    # ----------------------------------------------------------------
    @app.route("/profile/photo/<int:photo_id>")
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
    # 7) Other core pages
    # ----------------------------------------------------------------
    @app.route("/myEnrollment")
    def my_enrollment():
        try:
            return render_template("myEnrollment.html")
        except Exception:
            abort(500)

    @app.route("/courses")
    def courses():
        try:
            return render_template("courses.html")
        except Exception:
            abort(500)

    @app.route("/finance")
    def finance():
        try:
            return render_template("finance.html")
        except Exception:
            abort(500)

    @app.route("/logout")
    def logout():
        try:
            return redirect(url_for("auth.login"))
        except Exception:
            abort(500)

    # ----------------------------------------------------------------
    #  new pages
    # ----------------------------------------------------------------
    @app.route("/gradeRecheck")
    def grade_recheck():
        try:
            return render_template("gradeRecheck.html")
        except Exception:
            abort(500)

    @app.route("/specialApplications")
    def special_applications():
        try:
            return render_template("specialApplications.html")
        except Exception:
            abort(500)

    @app.route("/holdsAccess")
    def holds_access():
        try:
            return render_template("holds&studentAccess.html")
        except Exception:
            abort(500)

    @app.route("/transcript")
    def transcript():
        try:
            return render_template("academicTranscript.html")
        except Exception:
            abort(500)


    # ----------------------------------------------------------------
    # 8) Copyright & Contact
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
    # 9) Error Handlers
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
