import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.Core.models import db, Student, Campus, StudentLevel, Program, ProgramType, SubProgram
from werkzeug.security import generate_password_hash

def init_db():
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()

        # Check if we need to add test data
        if not Student.query.first():
            # Add a test student
            test_student = Student(
                StudentID='S12345678',
                FirstName='Test',
                LastName='Student',
                Email='test@student.usp.ac.fj',
                PasswordHash=generate_password_hash('password123')
            )
            db.session.add(test_student)
            db.session.commit()

if __name__ == '__main__':
    init_db() 