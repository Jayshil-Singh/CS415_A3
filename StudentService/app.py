import os
import sqlite3
import re
from flask import Flask, request, render_template, flash, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, Student

app = Flask(__name__, 
           template_folder='app/templates',
           static_folder='app/static')

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_change_this')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/studentservice.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'student_login'

@login_manager.user_loader
def load_user(student_id):
    return Student.query.get(student_id)

def update_password_in_sas_db(student_id, new_password_hash):
    """Update student password in SAS database."""
    try:
        # Get the path to the SAS database
        sas_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                 'SAS_Services', 'instance', 'enrollment.db')
        
        if not os.path.exists(sas_db_path):
            app.logger.error(f"SAS database not found at: {sas_db_path}")
            raise FileNotFoundError("SAS database not found")

        # Connect to the SAS database
        conn = sqlite3.connect(sas_db_path)
        cursor = conn.cursor()

        # Begin transaction
        conn.execute('BEGIN TRANSACTION')

        # Update password hash
        cursor.execute("""
            UPDATE Student 
            SET PasswordHash = ?
            WHERE StudentID = ?
        """, (new_password_hash, student_id))

        if cursor.rowcount == 0:
            conn.rollback()
            raise ValueError(f"Student {student_id} not found in SAS database")

        # Commit transaction
        conn.commit()
        app.logger.info(f"Successfully updated password for student {student_id} in SAS database")

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        app.logger.error(f"Error updating password in SAS database: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/')
def index():
    return redirect(url_for('student_login'))

@app.route('/student-login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        student_id = request.form.get('studentId')
        password = request.form.get('password')

        try:
            # Validate input
            if not all([student_id, password]):
                flash('Please provide both Student ID and password', 'error')
                return render_template('login.html')

            # Get student from database
            student = Student.query.filter_by(StudentID=student_id).first()
            if not student:
                flash('Invalid Student ID or password', 'error')
                return render_template('login.html')

            # Verify password
            if not check_password_hash(student.PasswordHash, password):
                flash('Invalid Student ID or password', 'error')
                return render_template('login.html')

            # Login successful
            login_user(student)
            return redirect(url_for('student_dashboard'))

        except Exception as e:
            app.logger.error(f"Error during login: {e}")
            flash('An error occurred during login. Please try again.', 'error')
            return render_template('login.html')

    return render_template('login.html')

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        student_id = request.form.get('studentId')
        old_password = request.form.get('oldPassword')
        new_password = request.form.get('newPassword')
        confirm_password = request.form.get('confirmPassword')

        try:
            # Validate input
            if not all([student_id, old_password, new_password, confirm_password]):
                flash('All fields are required', 'error')
                return render_template('change_password.html')

            if new_password != confirm_password:
                flash('New password and confirmation password do not match', 'error')
                return render_template('change_password.html')

            # Password strength validation
            if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', new_password):
                flash('Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one number, and one special character', 'error')
                return render_template('change_password.html')

            # Get student from StudentService database
            student = Student.query.filter_by(StudentID=student_id).first()
            if not student:
                flash('Student ID not found', 'error')
                return render_template('change_password.html')

            # Verify old password
            if not check_password_hash(student.PasswordHash, old_password):
                flash('Current password is incorrect', 'error')
                return render_template('change_password.html')

            # Generate new password hash
            new_password_hash = generate_password_hash(new_password)

            # Update password in StudentService database
            student.PasswordHash = new_password_hash
            db.session.commit()

            # Update password in SAS database
            update_password_in_sas_db(student_id, new_password_hash)

            flash('Password changed successfully', 'success')
            return redirect(url_for('student_login'))

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error changing password: {e}")
            flash('An error occurred while changing password. Please try again.', 'error')
            return render_template('change_password.html')

    return render_template('change_password.html')

@app.route('/student-dashboard')
@login_required
def student_dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('student_login')) 