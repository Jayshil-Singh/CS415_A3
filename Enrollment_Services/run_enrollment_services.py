# run_enrollment_services.py
from enrollment_services.routes import app

if __name__ == "__main__":
    app.run(debug=True, port=5000)
