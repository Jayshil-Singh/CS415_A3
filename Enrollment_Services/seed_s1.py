# seed_single_student_enrollment.py (or seed_s1.py)

import os
from datetime import datetime, UTC
import uuid
from flask import Flask
from sqlalchemy.exc import IntegrityError # Import IntegrityError

from enrollment_services.db import db
from enrollment_services.model import User, Student, Enrollment, Course, Program, SubProgram, StudentLevel

def create_app_for_seeding():
    """
    Creates a minimal Flask app context for database operations.
    """
    app = Flask(__name__)

    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    # Assuming this script is in the project root (CS415_A3)
    db_instance_dir = os.path.join(current_script_dir, 'instance')
    db_path = os.path.join(db_instance_dir, 'enrollment.db')

    os.makedirs(db_instance_dir, exist_ok=True)

    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Print the database path being used for verification
    print(f"Database path configured: {db_path}")

    db.init_app(app)
    return app

def seed_single_student_and_enrollment(db_instance):
    """
    Seeds a single mock student and enrolls them in a specific course.
    Assumes necessary Programs, SubPrograms, and at least one Course exist.
    """
    print("Starting single student and enrollment seeding...")

    # --- Student Mock Data ---
    # !! DOUBLE-CHECK THIS ID if you intend to create s00000001 !!
    # If s00000001 already exists from previous runs (e.g., in your image),
    # change this ID to something unique like "s00000005" to see a new entry.
    student_id = "s11207070" # Or change to "s00000005" if s00000001 is already there
    first_name = "Yash"
    last_name = "Prasad"
    email = f"{first_name.lower()}.{last_name.lower()}@gmail.com"
    username = f"{first_name.lower()}{last_name.lower()}"
    password = "psw123" # This will be hashedS

    # --- Course to Enroll In ---
    # As per previous discussions, ensure this CourseID actually exists
    # by running seed_db.py first.
    course_to_enroll_id = "CS111" # Make sure this CourseID exists in your DB

    with db_instance.session.no_autoflush: # Use no_autoflush for granular control

        try: # Added try-except for the entire seeding process
            # 1. Check/Create Program and SubProgram (if they don't exist, to link student)
            default_program = db_instance.session.get(Program, "PROG000")
            if not default_program:
                default_program = Program(ProgramID="PROG000", ProgramName="Default Program for Test")
                db_instance.session.add(default_program)
                db_instance.session.flush() # Flush to make it available for relationship
                print(f"Created default Program: {default_program.ProgramID}")
            else:
                print(f"Default Program {default_program.ProgramID} already exists.")

            default_subprogram = db_instance.session.get(SubProgram, "SUBPROG000")
            if not default_subprogram:
                default_subprogram = SubProgram(
                    SubProgramID="SUBPROG000",
                    SubProgramName="General Studies (Test)",
                    ProgramID=default_program.ProgramID # Link to default program
                )
                db_instance.session.add(default_subprogram)
                db_instance.session.flush() # Flush to make it available for relationship
                print(f"Created default SubProgram: {default_subprogram.SubProgramID}")
            else:
                print(f"Default SubProgram {default_subprogram.SubProgramID} already exists.")

            # 2. Add or Get User
            user = db_instance.session.get(User, student_id) # Using Session.get() directly
            if not user:
                user = User(id=student_id, username=username, email=email, role='student')
                user.set_password(password)
                db_instance.session.add(user)
                print(f"Attempting to create User: {username} with ID {student_id}")
            else:
                print(f"User {username} (ID: {student_id}) already exists. Skipping user creation.")

            # 3. Add or Get Student
            student = db_instance.session.get(Student, student_id) # Using Session.get() directly
            if not student:
                # Create a simple StudentLevel entry if needed for the new student
                student_level_id = f"LVL{student_id}"
                student_level = db_instance.session.get(StudentLevel, student_level_id) # Using Session.get() directly
                if not student_level:
                    student_level = StudentLevel(
                        StudentLevelID=student_level_id,
                        LevelName="Undergraduate (Test)",
                        StudentID=student_id # Link to the student ID
                    )
                    db_instance.session.add(student_level)
                    db_instance.session.flush() # Make the level ID available for student object
                    print(f"Created StudentLevel: {student_level_id}")
                else:
                    print(f"StudentLevel {student_level_id} already exists.")

                student = Student(
                    StudentID=student_id,
                    FirstName=first_name,
                    LastName=last_name,
                    Email=email,
                    DateOfBirth=datetime(2000, 1, 1).date(),
                    Gender="Male",
                    Address="123 Test St, Test City",
                    Contact="123-456-7890",
                    Citizenship="Testland",
                    CampusID="CAMP001",
                    ProgramID=default_program.ProgramID,
                    SubProgramID=default_subprogram.SubProgramID,
                    StudentLevelID=student_level.StudentLevelID,
                    CreatedAt=datetime.now(UTC)
                )
                db_instance.session.add(student)
                print(f"Attempting to create Student: {first_name} {last_name} (ID: {student_id})")
            else:
                print(f"Student {student_id} already exists. Skipping student creation.")


            # 4. Check if the course exists
            course = db_instance.session.get(Course, course_to_enroll_id) # Using Session.get() directly
            if not course:
                print(f"Error: Course '{course_to_enroll_id}' not found in the database. Please ensure it exists before attempting enrollment.")
                print("Skipping enrollment for this student.")
                db_instance.session.rollback() # Rollback any changes
                return

            # 5. Create Enrollment
            existing_enrollment = Enrollment.query.filter_by(StudentID=student_id, CourseID=course_to_enroll_id).first()
            if not existing_enrollment:
                enrollment_id = f"ENR_{str(uuid.uuid4())[:8]}" # Generate a unique ID for enrollment
                enrollment = Enrollment(
                    EnrollmentID=enrollment_id,
                    StudentID=student_id,
                    CourseID=course_to_enroll_id,
                    EnrollmentDate=datetime.now(UTC).date()
                )
                db_instance.session.add(enrollment)
                print(f"Attempting to enroll student {student_id} in course {course_to_enroll_id} (Enrollment ID: {enrollment_id})")
            else:
                print(f"Student {student_id} is already enrolled in {course_to_enroll_id}. Skipping enrollment.")

            print("Attempting to commit changes to the database...")
            db_instance.session.commit()
            print("Changes committed successfully.")
            print("Single student and enrollment seeding complete.")

        except IntegrityError as e:
            db_instance.session.rollback()
            print(f"Integrity Error: {e}. A record with this ID or unique constraint already exists. Rolling back.")
        except Exception as e:
            db_instance.session.rollback()
            print(f"An unexpected error occurred during seeding: {type(e).__name__}: {e}")
        finally:
            # Ensure the session is closed, although Flask-SQLAlchemy usually handles this.
            db_instance.session.close()


if __name__ == '__main__':
    app = create_app_for_seeding()
    with app.app_context():
        # It's generally recommended to run seed_db.py first to ensure
        # all base data (like courses) is present.
        print("Ensuring database tables exist. (Run seed_db.py for full data setup).")
        # db.drop_all() # ONLY UNCOMMENT FOR FULL RESET AND THEN RUN seed_db.py
        db.create_all() # Ensure tables are created if not already

        seed_single_student_and_enrollment(db)