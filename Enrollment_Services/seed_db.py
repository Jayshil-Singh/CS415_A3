# seed_db.py

import json
from datetime import datetime
import os

# Adjust these imports based on your exact project structure and package naming
from enrollment_services.db import db
from enrollment_services.model import (
    User, Program, SubProgram, Semester, Course, CourseAvailability,
    Student, StudentLevel, Hold, CourseFee, StudentCourseFee
)
from flask import Flask

# Initialize a minimal Flask app context for database operations
def create_app():
    app = Flask(__name__)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_instance_dir = os.path.join(base_dir, 'instance')
    db_path = os.path.join(db_instance_dir, 'enrollment.db')
    
    os.makedirs(db_instance_dir, exist_ok=True)

    print(f"Configuring database URI: sqlite:///{db_path}")
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

# The seeding function
def seed_data(data, db_instance):
    """
    Seeds the SQLite database with relevant data from the provided JSON.
    """

    print("Starting data seeding...")

    # --- Create Default Program and SubProgram (if they don't exist) ---
    # These are crucial for handling courses/subprograms not explicitly linked in JSON
    default_program_id = 'PROG000'
    default_subprogram_id = 'SUBPROG000'

    # Create Default Program
    existing_default_program = Program.query.get(default_program_id)
    if not existing_default_program:
        default_program = Program(ProgramID=default_program_id, ProgramName='Default Program')
        db_instance.session.add(default_program)
        db_instance.session.commit()
        print(f"Created default Program: {default_program_id}")
    program_objects = {default_program_id: Program.query.get(default_program_id)} # Ensure it's in our lookup


    # Create Default SubProgram
    existing_default_subprogram = SubProgram.query.get(default_subprogram_id)
    if not existing_default_subprogram:
        default_subprogram = SubProgram(
            SubProgramID=default_subprogram_id,
            SubProgramName='General Studies (Default)',
            SubProgramType='General',
            ProgramID=default_program_id # Link to default program
        )
        db_instance.session.add(default_subprogram)
        db_instance.session.commit()
        print(f"Created default SubProgram: {default_subprogram_id}")
    subprogram_objects = {default_subprogram_id: SubProgram.query.get(default_subprogram_id)} # Ensure it's in our lookup


    # --- Seed Programs (using default if subprogram not found later) ---
    # We already added the default program. Now add others.
    if 'programs' in data:
        for p_id_key, p_data in data['programs'].items():
            program_id_to_use = p_data['id'] #
            if program_id_to_use == default_program_id: # Skip if it's our predefined default
                continue

            existing_program = Program.query.get(program_id_to_use) #
            if existing_program:
                print(f"Skipping existing Program: {p_data['name']} (ID: {program_id_to_use})") #
                program_objects[program_id_to_use] = existing_program
                continue

            program = Program(
                ProgramID=program_id_to_use, #
                ProgramName=p_data['name'] #
            )
            db_instance.session.add(program)
            program_objects[program_id_to_use] = program
            
            # Map subprogram_id to program_id for later use, preferring explicit links over defaults
            subprogram_id_from_program = p_data['subprogramme_id'] #
            if subprogram_id_from_program not in subprogram_objects: # If this subprogram hasn't been added yet
                # We'll rely on the later SubProgram seeding to handle it, but store the program link
                pass 
            # Note: This is an implicit link, the SubProgram table has the FK, not Program directly.
            # The actual ProgramID for SubProgram is assigned when SubProgram itself is seeded.

    db_instance.session.commit()
    print("Additional Programs seeded.")

    # --- Seed SubPrograms (using default program if explicit link from 'programs' not found) ---
    # We already added the default subprogram. Now add others.
    # To properly link SubPrograms to Programs, we need to build a map from 'programs' data.
    program_to_subprogram_linkage = {} # Key: subprogram_id, Value: program_id
    if 'programs' in data:
        for p_id_key, p_data in data['programs'].items():
            subprogram_to_link = p_data['subprogramme_id'] #
            program_id_for_link = p_data['id'] #
            program_to_subprogram_linkage[subprogram_to_link] = program_id_for_link # Store the first program it's linked to

    if 'subprogrammes' in data and 'subPrograms' in data['subprogrammes']:
        for sp_id, sp_data in data['subprogrammes']['subPrograms'].items():
            subprogram_id_to_use = sp_data['id'] #
            if subprogram_id_to_use == default_subprogram_id: # Skip if it's our predefined default
                continue

            existing_subprogram = SubProgram.query.get(subprogram_id_to_use) #
            if existing_subprogram:
                print(f"Skipping existing SubProgram: {sp_data['subProgramName']} (ID: {subprogram_id_to_use})") #
                subprogram_objects[subprogram_id_to_use] = existing_subprogram
                continue

            # Get the ProgramID for this subprogram from the linkage map
            linked_program_id = program_to_subprogram_linkage.get(subprogram_id_to_use)
            if not linked_program_id or linked_program_id not in program_objects:
                linked_program_id = default_program_id # Fallback to the generic default program
                print(f"Warning: SubProgram {subprogram_id_to_use} ({sp_data['subProgramName']}) not explicitly linked to a known Program. Assigning to default program '{default_program_id}'.") #
            
            subprogram = SubProgram(
                SubProgramID=subprogram_id_to_use, #
                SubProgramName=sp_data['subProgramName'], #
                SubProgramType='General', #
                ProgramID=linked_program_id #
            )
            db_instance.session.add(subprogram)
            subprogram_objects[subprogram_id_to_use] = subprogram
    db_instance.session.commit()
    print("All SubPrograms seeded.")


    # --- Seed Semesters ---
    semester_objects = {}
    if 'course_availability' in data:
        for avail_id, avail_data in data['course_availability'].items():
            sem_id = avail_data.get('semtype_id') #
            sem_name = avail_data.get('semester') #
            if sem_id and sem_name and sem_id != 'UNKNOWN':
                if sem_id not in semester_objects:
                    existing_semester = Semester.query.get(sem_id) #
                    if existing_semester:
                        print(f"Skipping existing Semester: {sem_name} (ID: {sem_id})") #
                        semester_objects[sem_id] = existing_semester
                        continue

                    semester = Semester(
                        SemesterID=sem_id, #
                        SemesterName=sem_name #
                    )
                    db_instance.session.add(semester)
                    semester_objects[sem_id] = semester
            elif sem_id == 'UNKNOWN':
                print(f"Info: Skipping CourseAvailability {avail_id} due to 'UNKNOWN' semester type. No semester record created.") #
            else:
                print(f"Warning: Missing or invalid semester ID or name for CourseAvailability {avail_id}. Skipping semester creation.") #
    db_instance.session.commit()
    print("Semesters seeded.")

    # --- Seed Courses ---
    course_objects = {}
    if 'courses' in data:
        for c_id, c_data in data['courses'].items():
            course_code = c_data['code'] #
            existing_course = Course.query.get(course_code) #
            if existing_course:
                print(f"Skipping existing Course: {c_data['name']} (ID: {course_code})") #
                course_objects[course_code] = existing_course
                continue

            # Assign course to the default subprogram.
            # If you have a more accurate mapping from course_id to subprogram_id, implement it here.
            # Based on the provided JSON, there's no direct 'subprogram_id' field in 'courses' data.
            assigned_subprogram_id = default_subprogram_id
            if assigned_subprogram_id not in subprogram_objects:
                 print(f"Critical Error: Default SubProgram '{default_subprogram_id}' not found. Cannot assign a SubProgram to Course {course_code}. Skipping course.")
                 continue # This should not happen if default_subprogram_id is properly created and added to subprogram_objects.

            course = Course(
                CourseID=course_code, #
                SubProgramID=assigned_subprogram_id, #
                CourseName=c_data['name'], #
                PrerequisiteCourseID=None # Initialize as None, will be updated in second pass
            )
            db_instance.session.add(course)
            course_objects[course_code] = course
    db_instance.session.commit()
    print("Courses seeded.")

    # Second pass to update prerequisites after all courses are added
    if 'courses' in data:
        for c_id, c_data in data['courses'].items():
            course = course_objects.get(c_data['code']) #
            if course and c_data.get('course_prerequisites_id') and c_data['course_prerequisites_id'] != 'UNKNOWN': #
                prereq_key_in_json = c_data['course_prerequisites_id'] #
                prereq_info = data['prerequisites'].get(prereq_key_in_json) #
                
                if prereq_info and prereq_info.get('course_id') and prereq_info['course_id'] != 'UNKNOWN': #
                    prereq_course_code = prereq_info['course_id'] #
                    if prereq_course_code in course_objects:
                        course.PrerequisiteCourseID = course_objects[prereq_course_code].CourseID #
                    else:
                        print(f"Warning: Prerequisite course '{prereq_course_code}' not found in 'courses' data for {c_data['code']}. Skipping prerequisite assignment for this course.") #
                elif prereq_info and prereq_info.get('course_id') == 'UNKNOWN':
                     print(f"Info: Prerequisite for {c_data['code']} is marked as 'UNKNOWN'. Skipping assignment.") #
                else:
                    print(f"Warning: Prerequisite ID '{prereq_key_in_json}' not found in 'prerequisites' data for {c_data['code']}. Skipping prerequisite assignment.") #
    db_instance.session.commit()
    print("Courses prerequisites updated.")


    # --- Seed CourseAvailability ---
    if 'course_availability' in data:
        for avail_id, avail_data in data['course_availability'].items():
            existing_avail = CourseAvailability.query.get(avail_data['id']) #
            if existing_avail:
                print(f"Skipping existing CourseAvailability: {avail_id}")
                continue

            course_code = avail_data['course_id'] #
            semester_id = avail_data['semtype_id'] #
            
            if course_code in course_objects and semester_id in semester_objects:
                course_availability = CourseAvailability(
                    CourseAvailabilityID=avail_id, #
                    isAvailable=avail_data['offered'], #
                    CourseID=course_objects[course_code].CourseID, #
                    SemesterID=semester_objects[semester_id].SemesterID #
                )
                db_instance.session.add(course_availability)
            elif course_code not in course_objects:
                print(f"Warning: Course '{course_code}' not found for CourseAvailability {avail_id}. Skipping.") #
            elif semester_id not in semester_objects:
                print(f"Warning: Semester '{semester_id}' not found for CourseAvailability {avail_id}. Skipping.") #
            elif semester_id == 'UNKNOWN':
                print(f"Info: Skipping CourseAvailability {avail_id} due to 'UNKNOWN' semester type.") #

    db_instance.session.commit()
    print("CourseAvailability seeded.")

    # --- Seed Students and Users ---
    student_objects = {}
    if 'students' in data:
        for s_id_key, s_data in data['students'].items():
            # Use a consistent student ID. Prioritize 'id' > 'studentId' > JSON key
            student_id_to_use = s_data.get('id') or s_data.get('studentId') or s_id_key

            existing_student = Student.query.get(student_id_to_use) #
            if existing_student:
                print(f"Skipping existing Student: {s_data.get('firstName', '')} {s_data.get('lastName', '')} (ID: {student_id_to_use})") #
                student_objects[student_id_to_use] = existing_student
                # Ensure the user object for this student also exists/is updated
                user = User.query.get(student_id_to_use) #
                if not user:
                    # Create user if student exists but user doesn't (data inconsistency)
                    first_name = s_data.get('firstName', '').lower() #
                    last_name = s_data.get('lastName', '').lower() #
                    username = f"{first_name}{last_name}" if first_name and last_name else student_id_to_use.lower()
                    email = f"{username}@example.com"
                    user = User(id=student_id_to_use, username=username, email=email, role='student') #
                    user.set_password(s_data.get('password', s_data.get('password:', 'default_password'))) #
                    db_instance.session.add(user)
                    db_instance.session.commit()
                continue # Skip to next student since this one is already in the DB

            first_name = s_data.get('firstName', '') #
            last_name = s_data.get('lastName', '') #
            # Handle inconsistent password key
            raw_password = s_data.get('password') or s_data.get('password:') or 'default_password' #
            
            # Generate email and username
            username = f"{first_name.lower()}{last_name.lower()}" if first_name and last_name else student_id_to_use.lower()
            email = f"{username}@example.com" # Placeholder email
            
            # Create User
            user = User(
                id=student_id_to_use, #
                username=username, #
                email=email, #
                role='student' # Assuming default role is 'student'
            )
            user.set_password(raw_password) #
            db_instance.session.add(user)

            # Create Student object
            student = Student(
                StudentID=student_id_to_use, #
                FirstName=first_name, #
                LastName=last_name, #
                Email=email # Use the generated email for consistency
            )
            db_instance.session.add(student)
            student_objects[student_id_to_use] = student
            
    db_instance.session.commit()
    print("Students and Users seeded.")

    # --- Seed Holds ---
    if 'holds' in data:
        for h_id_key, h_data in data['holds'].items():
            # Generate a unique HoldID if it's not present (your JSON uses Firebase keys for Holds)
            hold_id = h_data.get('id') or h_id_key
            
            existing_hold = Hold.query.get(hold_id) #
            if existing_hold:
                print(f"Skipping existing Hold: {hold_id}")
                continue

            student_id = h_data.get('studentID') #
            if student_id in student_objects:
                # Attempt to get actual date from JSON, fallback to current or student createdAt
                hold_date_str = h_data.get('holdDate') #
                if hold_date_str:
                    try:
                        hold_date = datetime.strptime(hold_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        print(f"Warning: Invalid date format '{hold_date_str}' for hold {hold_id}. Using current date.")
                        hold_date = datetime.utcnow().date()
                else:
                    # Look up original student data for createdAt
                    student_original_entry = next((s for s in data['students'].values() if (s.get('id') == student_id or s.get('studentId') == student_id)), None) #
                    if student_original_entry and student_original_entry.get('createdAt'): #
                        # Handle ISO format with 'Z' for UTC
                        try:
                            hold_date = datetime.fromisoformat(student_original_entry['createdAt'].replace('Z', '+00:00')).date() #
                        except ValueError:
                            print(f"Warning: Invalid ISO date format '{student_original_entry['createdAt']}' for student creation date. Using current date for hold {hold_id}.") #
                            hold_date = datetime.utcnow().date()
                    else:
                        hold_date = datetime.utcnow().date() # Default to current UTC date if no specific date found
                        
                lift_date_str = h_data.get('liftDate') #
                lift_date = None
                if lift_date_str:
                    try:
                        lift_date = datetime.strptime(lift_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        print(f"Warning: Invalid date format '{lift_date_str}' for liftDate of hold {hold_id}. Setting to None.")
                
                hold = Hold(
                    HoldID=hold_id, #
                    reason=h_data.get('reason'), #
                    status=h_data.get('status', 'Active'), #
                    holdDate=hold_date, #
                    liftDate=lift_date, #
                    StudentID=student_objects[student_id].StudentID #
                )
                db_instance.session.add(hold)
            else:
                print(f"Warning: Student '{student_id}' not found for Hold {h_id_key}. Skipping.") #
    db_instance.session.commit()
    print("Holds seeded.")
    
    # --- Seed Course Fees (from student_course_fee to extract unique Fee information) ---
    # This approach assumes that an 'amount' associated with a 'course_id' in 'student_course_fee'
    # can be considered a unique 'CourseFee' record.
    course_fee_objects = {} # Key: (CourseID, Amount) -> CourseFee object
    fee_id_counter = 1
    if 'student_course_fee' in data:
        for scf_key, scf_data in data['student_course_fee'].items():
            course_code = scf_data.get('course_id') #
            amount = scf_data.get('amount') #

            if course_code and course_code in course_objects and amount is not None:
                fee_lookup_key = (course_code, amount)
                if fee_lookup_key not in course_fee_objects:
                    # Generate a simple, incrementing FeeID
                    new_fee_id = f"FEE{fee_id_counter:05d}" # Padded with zeros for sorting
                    
                    # Ensure this generated FeeID is unique in the database
                    while CourseFee.query.get(new_fee_id): #
                        fee_id_counter += 1
                        new_fee_id = f"FEE{fee_id_counter:05d}"

                    course_fee = CourseFee(
                        FeeID=new_fee_id, #
                        amount=amount, #
                        description=f"Course fee for {course_code}", # Generic description
                        CourseID=course_objects[course_code].CourseID #
                    )
                    db_instance.session.add(course_fee)
                    course_fee_objects[fee_lookup_key] = course_fee
                    fee_id_counter += 1
            elif course_code and course_code not in course_objects:
                print(f"Warning: Course '{course_code}' not found for CourseFee inference from student_course_fee entry '{scf_key}'. Skipping.") #
            else:
                print(f"Warning: Missing course_id or amount in student_course_fee entry '{scf_key}'. Skipping CourseFee creation.") #
    db_instance.session.commit()
    print("CourseFees seeded.")

    # --- Seed StudentCourseFee ---
    student_course_fee_counter = 1
    if 'student_course_fee' in data:
        for scf_key, scf_data in data['student_course_fee'].items():
            student_id = scf_data.get('studentID') #
            course_code = scf_data.get('course_id') #
            amount = scf_data.get('amount') #
            due_date_str = scf_data.get('dueDate') #

            if student_id in student_objects and course_code in course_objects and due_date_str:
                # Generate a unique StudentCourseFeeID
                new_scf_id = f"SCF{student_course_fee_counter:05d}"
                while StudentCourseFee.query.get(new_scf_id): # Ensure ID is truly unique
                    student_course_fee_counter += 1
                    new_scf_id = f"SCF{student_course_fee_counter:05d}"

                try:
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                except ValueError:
                    print(f"Warning: Invalid date format '{due_date_str}' for student_course_fee {scf_key}. Using current date.")
                    due_date = datetime.utcnow().date() #

                paid_date = None # No 'paidDate' in your sample JSON for this record
                status = scf_data.get('status', 'Outstanding') # No 'status' in your sample JSON, default to 'Outstanding'

                # Find the matching FeeID using the CourseID and Amount
                fee_id_for_link = None
                fee_lookup_key = (course_code, amount)
                if fee_lookup_key in course_fee_objects:
                    fee_id_for_link = course_fee_objects[fee_lookup_key].FeeID
                else:
                    print(f"Warning: Could not find matching CourseFee for student {student_id}, course {course_code}, amount {amount}. FeeID will be NULL.")

                student_course_fee = StudentCourseFee(
                    StudentCourseFeeID=new_scf_id, #
                    due_date=due_date, #
                    paid_date=paid_date, #
                    status=status, #
                    StudentID=student_objects[student_id].StudentID, #
                    CourseID=course_objects[course_code].CourseID, #
                    FeeID=fee_id_for_link #
                )
                db_instance.session.add(student_course_fee)
                student_course_fee_counter += 1
            else:
                print(f"Warning: Incomplete or invalid student/course/date data for StudentCourseFee entry '{scf_key}'. Skipping.") #
    db_instance.session.commit()
    print("StudentCourseFees seeded.")

    # --- Seed Enrollments ---
    enrollment_counter = 1
    # Iterate through student_course_fee to infer enrollments
    if 'student_course_fee' in data:
        for scf_key, scf_data in data['student_course_fee'].items():
            student_id = scf_data.get('studentID') #
            course_code = scf_data.get('course_id') #

            if student_id in student_objects and course_code in course_objects:
                # Check if enrollment already exists (important for idempotency)
                existing_enrollment = Enrollment.query.filter_by(
                    StudentID=student_objects[student_id].StudentID, #
                    CourseID=course_objects[course_code].CourseID #
                ).first()
                
                if existing_enrollment:
                    print(f"Skipping existing Enrollment for Student '{student_id}' in Course '{course_code}'.") #
                    continue

                new_enrollment_id = f"ENR{enrollment_counter:05d}"
                # Ensure generated ID is unique
                while Enrollment.query.get(new_enrollment_id): #
                    enrollment_counter += 1
                    new_enrollment_id = f"ENR{enrollment_counter:05d}"

                enrollment = Enrollment(
                    EnrollmentID=new_enrollment_id, #
                    EnrollmentDate=datetime.utcnow().date(), # Use current date as enrollment date
                    StudentID=student_objects[student_id].StudentID, #
                    CourseID=course_objects[course_code].CourseID #
                )
                db_instance.session.add(enrollment)
                enrollment_counter += 1
            else:
                print(f"Warning: Student '{student_id}' or Course '{course_code}' not found for enrollment based on student_course_fee '{scf_key}'. Skipping enrollment.") #
    db_instance.session.commit()
    print("Enrollments seeded.")

    print("All data seeding complete.")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        print("Dropping all existing tables...")
        db.drop_all()
        print("Creating new tables...")
        db.create_all()
        print("Tables created.")

        json_file_name = 'usp-enrollment-system-database-default-rtdb-export.json'
        json_file_path = os.path.join(os.path.dirname(__file__), json_file_name)
        print(f"Attempting to load JSON from: {json_file_path}")

        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            seed_data(json_data, db)
        except FileNotFoundError:
            print(f"Error: JSON file not found at {json_file_path}")
        except Exception as e:
            print(f"An unexpected error occurred during seeding: {type(e).__name__}: {e}")
            db.session.rollback()