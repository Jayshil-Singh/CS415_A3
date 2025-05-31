import sqlite3
import os
from werkzeug.security import generate_password_hash
from login_service_packages.models import db, User
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_student_data():
    """
    Syncs student data from enrollment.db and studentservice.db into the login service database
    """
    # Get absolute paths based on current file location
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    
    enrollment_db = os.path.join(root_dir, 'SAS_Services', 'instance', 'enrollment.db')
    student_service_db = os.path.join(root_dir, 'StudentService', 'instance', 'studentservice.db')
    login_db = os.path.join(current_dir, 'instance', 'login.db')

    # Ensure the instance directory exists
    os.makedirs(os.path.join(current_dir, 'instance'), exist_ok=True)

    # Validate database files exist
    if not os.path.exists(enrollment_db):
        logger.error(f"Enrollment database not found at: {enrollment_db}")
        raise FileNotFoundError(f"Enrollment database not found")
    
    if not os.path.exists(student_service_db):
        logger.error(f"Student service database not found at: {student_service_db}")
        raise FileNotFoundError(f"Student service database not found")

    enroll_conn = None
    service_conn = None
    try:
        # Connect to source databases
        enroll_conn = sqlite3.connect(enrollment_db)
        service_conn = sqlite3.connect(student_service_db)
        enroll_cursor = enroll_conn.cursor()
        service_cursor = service_conn.cursor()

        # Get students from enrollment.db
        enroll_cursor.execute("""
            SELECT StudentID, FirstName, LastName, Email, PasswordHash
            FROM Student
        """)
        enrollment_students = {row[0]: row for row in enroll_cursor.fetchall()}
        logger.info(f"Found {len(enrollment_students)} students in enrollment database")

        # Get students from studentservice.db
        service_cursor.execute("""
            SELECT StudentID, FirstName, LastName, Email, PasswordHash
            FROM Student
        """)
        service_students = {row[0]: row for row in service_cursor.fetchall()}
        logger.info(f"Found {len(service_students)} students in student service database")

        # Find students that exist in both databases
        common_student_ids = set(enrollment_students.keys()) & set(service_students.keys())
        logger.info(f"Found {len(common_student_ids)} students in both databases")

        # Create or update users in login service database
        updated_count = 0
        created_count = 0
        for student_id in common_student_ids:
            student = enrollment_students[student_id]  # Use enrollment.db as primary source
            
            # Check if user already exists
            existing_user = User.query.get(student_id)
            
            if existing_user:
                # Update existing user
                existing_user.username = f"{student[1].lower()}.{student[2].lower()}"  # firstname.lastname
                existing_user.email = student[3]
                existing_user.password_hash = student[4]  # Use the hash from enrollment.db
                existing_user.role = 'student'
                existing_user.is_active = True
                updated_count += 1
            else:
                # Create new user
                new_user = User(
                    id=student_id,
                    username=f"{student[1].lower()}.{student[2].lower()}",  # firstname.lastname
                    email=student[3],
                    password_hash=student[4],  # Use the hash from enrollment.db
                    role='student',
                    is_active=True
                )
                db.session.add(new_user)
                created_count += 1

        db.session.commit()
        logger.info(f"Successfully synced students: {created_count} created, {updated_count} updated")

    except sqlite3.Error as e:
        logger.error(f"SQLite error during sync: {e}")
        db.session.rollback()
        raise
    except Exception as e:
        logger.error(f"Error during sync: {e}")
        db.session.rollback()
        raise
    finally:
        if enroll_conn:
            enroll_conn.close()
        if service_conn:
            service_conn.close()

if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from login_service_packages import create_app
    app = create_app()
    with app.app_context():
        db.create_all()  # Ensure tables exist
        sync_student_data() 