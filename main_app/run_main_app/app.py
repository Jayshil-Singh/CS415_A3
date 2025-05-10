from flask import Flask, render_template, request, redirect, url_for
from types import SimpleNamespace

app = Flask(
    __name__,
    template_folder="main_app_packages/templates",
    static_folder="main_app_packages/static"
)

# ——— Stub out a “current_user” everywhere ———
@app.context_processor
def inject_user():
    # Jinja will always have a current_user.username
    return {
        "current_user": SimpleNamespace(username="Student")
    }

# ——— Login (entry point) ———
@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        # simple format check for Snnnn@student.usp.ac.fj
        if not email.lower().startswith("s") or not email.lower().endswith("@student.usp.ac.fj"):
            error = "Enter a valid S12345678@student.usp.ac.fj email"
        elif password != "password123":  # stub password
            error = "Invalid password"
        else:
            return redirect(url_for("home"))
    return render_template("login.html", error=error)

# ——— Homepage ———
@app.route("/home")
def home():
    return render_template("homepage.html")

# ——— Student Profile ———
@app.route("/profile")
def student_profile():
    return render_template("studentProfile.html")

# ——— My Enrollment ———
@app.route("/myEnrollment")
def my_enrollment():
    return render_template("myEnrollment.html")

# ——— Courses ———
@app.route("/courses")
def courses():
    return render_template("courses.html")

# ——— Finance ———
@app.route("/finance")
def finance():
    return render_template("finance.html")

# ——— Logout ———
@app.route("/logout")
def logout():
    # simply send them back to login for now
    return redirect(url_for("login"))

@app.errorhandler(404)
def handle_404(e):
    # note: return second value = HTTP status code
    return render_template("errors/404.html"), 404

@app.errorhandler(500)
def handle_500(e):
    return render_template("errors/500.html"), 500

if __name__ == "__main__":
    app.run(debug=True)
