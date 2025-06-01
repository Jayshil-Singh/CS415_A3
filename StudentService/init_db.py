# File: StudentService/init_db.py

from flask import Flask
from app.API.config import Config
from app.Core.models import db, User, Student
import os
from datetime import datetime
from werkzeug.security import generate_password_hash
from app import create_app

def init_db():
    """
    Create any missing tables and, if the 'users' table is empty, insert one test user.
    We do NOT seed any Student rows here (since your studentservice.db already
    contains actual registered students).
    """
    # --- Initialize a minimal Flask app just to pull in your config ---
    app = Flask(__name__)
    app.config.from_object(Config)

    # --- Hook up SQLAlchemy with this app ---
    db.init_app(app)

    with app.app_context():
        # 1) Create all tables that do not yet exist:
        db.create_all()

        # 2) If the 'users' table has zero rows, insert one test user:
        if User.query.count() == 0:
            test_user = User(
                id='S12345678',
                username='test_student',
                email='s12345678@student.usp.ac.fj',
                role='student'
            )
            test_user.set_password('password123')
            db.session.add(test_user)
            db.session.commit()
            print("Created test user:")
            print(f"  Email:    {test_user.email}")
            print(f"  Password: password123")
        else:
            print("Database already contains users. Skipping test user creation.")

        # Check if test student exists
        test_student = Student.query.filter_by(StudentID='S12345678').first()
        if not test_student:
            # Create a test student
            test_student = Student(
                StudentID='S12345678',
                FirstName='Test',
                LastName='Student',
                Contact='1234567890',
                Email='s12345678@student.usp.ac.fj',
                DateOfBirth=datetime.strptime('2000-01-01', '%Y-%m-%d'),
                Gender='Male',
                Citizenship='Fiji',
                Address='123 Test Street',
                PasswordHash=generate_password_hash('Test@123'),
                CampusID='LAUCALA'
            )
            db.session.add(test_student)
            db.session.commit()
            print("Created test student with ID: S12345678 and password: Test@123")
        else:
            print("Test student already exists")

if __name__ == '__main__':
    init_db()
