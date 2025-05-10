# File: C:\Users\yashp\Documents\CS415\CS415_A3\main_app\run_main_app.py\main_app_packages\app.py
import os
from flask import Flask, render_template

# 1. Create the Flask application instance
# __name__ helps Flask find templates and static files relative to this module's location.
# However, if your templates/static are truly at main_app/run_main_app.py/main_app_packages/templates (etc.)
# this default is fine. If they are elsewhere, you might need to adjust template_folder and static_folder.
app = Flask(__name__) # Flask will look for templates/static in folders named 'templates' and 'static'
                      # in the same directory as this app.py, OR in subdirectories of an "instance folder"
                      # OR as specified by template_folder/static_folder arguments.

# 2. Load Configurations
# IMPORTANT: Create a secure, random secret key.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_default_and_insecure_secret_key_CHANGE_ME')
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 't']

# Configuration for uploaded profile pictures
# Make sure this path is correct and your application has write permissions to it.
# It's often good to place this outside your application code, or ensure it's handled correctly by deployment.
# For development, a subfolder might be okay.
BASE_DIR = os.path.abspath(os.path.dirname(__file__)) # Gets the directory of this app.py file
UPLOAD_FOLDER_PATH = os.path.join(BASE_DIR, 'profile_pictures_storage') # Example path
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER_PATH
# You might want to create this directory if it doesn't exist when the app starts
# os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) # Do this carefully, maybe in a startup script

# Allowed extensions for profile pictures
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}


# 3. Import routes AFTER 'app' and its configurations are defined
# This is crucial to avoid circular imports if routes.py also imports 'app'.
@app.route('/')
def index():
    """Serves the main login page."""
    return render_template('templates/login.html') # Assuming login.html is in the root of templates/

# Routes for SASManager
@app.route('/sas-manager/home')
def sas_manager_home():
    """Serves the SAS Manager dashboard page."""
    return render_template('SASManager/homeSAS.html')

# Routes for SASStaff
@app.route('/sas-staff/home')
def sas_staff_home():
    """Serves the SAS Staff home page."""
    return render_template('SASStaff/homeStaff.html')

@app.route('/sas-staff/edit-student')
def sas_staff_edit_student():
    """Serves the page for editing student information."""
    return render_template('SASStaff/editST.html')

@app.route('/sas-staff/register-student')
def sas_staff_register_student():
    """Serves the page for registering a new student."""
    return render_template('SASStaff/registerST.html')

# Routes for SuperAdmin
@app.route('/super-admin/home')
def super_admin_home():
    """Serves the Super Admin dashboard page."""
    return render_template('SuperAdmin/SAdminHome.html')

@app.route('/super-admin/remove-staff')
def super_admin_remove_staff():
    """Serves the page for removing staff/managers."""
    return render_template('SuperAdmin/RemoveStaff.html')

# 4. Optional: Add any Flask extensions initialization here
# Example:
# from flask_sqlalchemy import SQLAlchemy
# db = SQLAlchemy()
# db.init_app(app)

# 5. The if __name__ == '__main__': block is for direct execution (python app.py)
# This block will NOT be executed when you use 'flask run'.
# 'flask run' imports the 'app' object and uses its own development server.
if __name__ == '__main__':
    # This direct run method often bypasses the package context that 'flask run' sets up,
    # which can lead to import errors for relative imports in a packaged application.
    # It's generally recommended to use 'flask run' for development.
    print(f"Attempting to run directly. UPLOAD_FOLDER is {app.config['UPLOAD_FOLDER']}")
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) # Ensure upload folder exists for direct run
    app.run(host='0.0.0.0', port=5000) # host='0.0.0.0' makes it accessible on your network
