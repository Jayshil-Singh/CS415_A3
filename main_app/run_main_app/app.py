from flask import Flask, render_template, request, redirect, url_for, abort
from werkzeug.exceptions import HTTPException
from types import SimpleNamespace

app = Flask(
    __name__,
    template_folder="main_app_packages/templates",
    static_folder="main_app_packages/static"
)

# ——— Stub out a “current_user” everywhere ———
@app.context_processor
def inject_user():
    return {"current_user": SimpleNamespace(username="Student")}

# ——— Login (entry point) ———
@app.route("/", methods=["GET", "POST"])
def login():
    try:
        error = None
        if request.method == "POST":
            email    = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            if not email.lower().startswith("s") or not email.lower().endswith("@student.usp.ac.fj"):
                error = "Enter a valid S12345678@student.usp.ac.fj email"
            elif password != "password123":
                error = "Invalid password"
            else:
                return redirect(url_for("home"))
        return render_template("login.html", error=error)
    except Exception:
        # any unexpected exception here becomes a 500
        abort(500)

# ——— Homepage ———
@app.route("/home")
def home():
    try:
        return render_template("homepage.html")
    except Exception:
        abort(500)

# ——— Student Profile ———
@app.route("/profile")
def student_profile():
    try:
        return render_template("studentProfile.html")
    except Exception:
        abort(500)

# ——— My Enrollment ———
@app.route("/myEnrollment")
def my_enrollment():
    try:
        return render_template("myEnrollment.html")
    except Exception:
        abort(500)

# ——— Courses ———
@app.route("/courses")
def courses():
    try:
        return render_template("courses.html")
    except Exception:
        abort(500)

# ——— Finance ———
@app.route("/finance")
def finance():
    try:
        return render_template("finance.html")
    except Exception:
        abort(500)

# ——— Logout ———
@app.route("/logout")
def logout():
    try:
        return redirect(url_for("login"))
    except Exception:
        abort(500)

# ——— Error Handlers ———
@app.errorhandler(404)
def handle_404(e):
    return render_template("errors/404.html"), 404

@app.errorhandler(500)
def handle_500(e):
    return render_template("errors/500.html"), 500

# Catch-all for any other uncaught exceptions (optional)
@app.errorhandler(Exception)
def handle_all_exceptions(e):
    # If it's an HTTPException (like abort(403)), let Flask handle it
    if isinstance(e, HTTPException):
        return e
    # Otherwise show our 500 page
    return render_template("errors/500.html"), 500

if __name__ == "__main__":
    app.run(debug=True)
