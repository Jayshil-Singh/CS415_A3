from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

db = SQLAlchemy()

def verify_student_in_databases(student_id, email):
    """
    Verify if student exists in both enrollment.db and studentservice.db
    Returns (exists_in_enrollment, exists_in_student_service)
    """
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    enrollment_db_path = os.path.join(root_dir, 'SAS_Services', 'instance', 'enrollment.db')
    student_service_db_path = os.path.join(root_dir, 'StudentService', 'instance', 'studentservice.db')
    
    exists_in_enrollment = False
    exists_in_student_service = False
    
    # Check enrollment.db
    try:
        conn = sqlite3.connect(enrollment_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT StudentID FROM Student WHERE StudentID = ? AND Email = ?", (student_id, email))
        exists_in_enrollment = cursor.fetchone() is not None
        conn.close()
    except Exception as e:
        print(f"Error checking enrollment.db: {e}")
    
    # Check studentservice.db
    try:
        conn = sqlite3.connect(student_service_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT StudentID FROM Student WHERE StudentID = ? AND Email = ?", (student_id, email))
        exists_in_student_service = cursor.fetchone() is not None
        conn.close()
    except Exception as e:
        print(f"Error checking studentservice.db: {e}")
    
    return exists_in_enrollment, exists_in_student_service

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(20), primary_key=True)  # Student ID or Staff ID
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student', 'sas_manager', 'admin'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def verify_student_exists(student_id, email):
        """
        Verify if a student exists in both required databases
        Returns tuple (exists, message)
        """
        enroll_exists, service_exists = verify_student_in_databases(student_id, email)
        
        if not enroll_exists and not service_exists:
            return False, "Student not found in any database"
        elif not enroll_exists:
            return False, "Student not found in enrollment database"
        elif not service_exists:
            return False, "Student not found in student service database"
        return True, "Student verified in both databases"
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class LoginAttempt(db.Model):
    __tablename__ = 'login_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    success = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref='login_attempts')
    
    def __repr__(self):
        return f'<LoginAttempt {self.user_id} at {self.timestamp}>' 