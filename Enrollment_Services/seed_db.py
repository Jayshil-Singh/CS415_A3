# seed_db.py

import json
from datetime import datetime
import os
import random # Keep random import if you plan to move other randomizations here later, otherwise it can be removed.

# Adjust these imports based on your exact project structure and package naming
from enrollment_services.db import db
from enrollment_services.model import (
    User, Program, SubProgram, Semester, Course, CourseAvailability,
    Student, StudentLevel, Hold, CourseFee, StudentCourseFee, Enrollment
)
from flask import Flask

# Initialize a minimal Flask app context for database operations
def create_app():
    app = Flask(__name__)

    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(current_script_dir) 

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
    NOTE: CourseFee creation logic has been REMOVED from this script
    and moved to a separate seed_course_fees.py.
    """

    print("Starting data seeding...")

    # --- Create Default Program and SubProgram (if they don't exist) ---
    default_program_id = 'PROG000'
    default_subprogram_id = 'SUBPROG000'

    existing_default_program = db_instance.session.get(Program, default_program_id)
    if not existing_default_program:
        default_program = Program(ProgramID=default_program_id, ProgramName='Default Program')
        db_instance.session.add(default_program)
        db_instance.session.commit()
        print(f"Created default Program: {default_program_id}")
    program_objects = {default_program_id: db_instance.session.get(Program, default_program_id)}


    existing_default_subprogram = db_instance.session.get(SubProgram, default_subprogram_id)
    if not existing_default_subprogram:
        default_subprogram = SubProgram(
            SubProgramID=default_subprogram_id,
            SubProgramName='General Studies (Default)',
            SubProgramType='General',
            ProgramID=default_program_id
        )
        db_instance.session.add(default_subprogram)
        db_instance.session.commit()
        print(f"Created default SubProgram: {default_subprogram_id}")
    subprogram_objects = {default_subprogram_id: db_instance.session.get(SubProgram, default_subprogram_id)}


    # --- Seed Programs ---
    if 'programs' in data:
        for p_id_key, p_data in data['programs'].items():
            program_id_to_use = p_data['id']
            if program_id_to_use == default_program_id:
                continue

            existing_program = db_instance.session.get(Program, program_id_to_use)
            if existing_program:
                print(f"Skipping existing Program: {p_data['name']} (ID: {program_id_to_use})")
                program_objects[program_id_to_use] = existing_program
                continue

            program = Program(
                ProgramID=program_id_to_use,
                ProgramName=p_data['name']
            )
            db_instance.session.add(program)
            program_objects[program_id_to_use] = program
            
    db_instance.session.commit()
    print("Additional Programs seeded.")

    # --- Seed SubPrograms ---
    program_to_subprogram_linkage = {}
    if 'programs' in data:
        for p_id_key, p_data in data['programs'].items():
            subprogram_to_link = p_data['subprogramme_id']
            program_id_for_link = p_data['id']
            program_to_subprogram_linkage[subprogram_to_link] = program_id_for_link

    if 'subprogrammes' in data and 'subPrograms' in data['subprogrammes']:
        for sp_id, sp_data in data['subprogrammes']['subPrograms'].items():
            subprogram_id_to_use = sp_data['id']
            if subprogram_id_to_use == default_subprogram_id:
                continue

            existing_subprogram = db_instance.session.get(SubProgram, subprogram_id_to_use)
            if existing_subprogram:
                print(f"Skipping existing SubProgram: {sp_data['subProgramName']} (ID: {subprogram_id_to_use})")
                subprogram_objects[subprogram_id_to_use] = existing_subprogram
                continue

            linked_program_id = program_to_subprogram_linkage.get(subprogram_id_to_use)
            if not linked_program_id or linked_program_id not in program_objects:
                linked_program_id = default_program_id
                print(f"Warning: SubProgram {subprogram_id_to_use} ({sp_data['subProgramName']}) not explicitly linked to a known Program. Assigning to default program '{default_program_id}'.")
            
            subprogram = SubProgram(
                SubProgramID=subprogram_id_to_use,
                SubProgramName=sp_data['subProgramName'],
                SubProgramType='General',
                ProgramID=linked_program_id
            )
            db_instance.session.add(subprogram)
            subprogram_objects[subprogram_id_to_use] = subprogram
    db_instance.session.commit()
    print("All SubPrograms seeded.")


    # --- Seed Semesters ---
    semester_objects = {}
    if 'course_availability' in data:
        for avail_id, avail_data in data['course_availability'].items():
            sem_id = avail_data.get('semtype_id')
            sem_name = avail_data.get('semester')
            if sem_id and sem_name and sem_id != 'UNKNOWN':
                if sem_id not in semester_objects:
                    existing_semester = db_instance.session.get(Semester, sem_id)
                    if existing_semester:
                        print(f"Skipping existing Semester: {sem_name} (ID: {sem_id})")
                        semester_objects[sem_id] = existing_semester
                        continue

                    semester = Semester(
                        SemesterID=sem_id,
                        SemesterName=sem_name
                    )
                    db_instance.session.add(semester)
                    semester_objects[sem_id] = semester
            elif sem_id == 'UNKNOWN':
                print(f"Info: Skipping CourseAvailability {avail_id} due to 'UNKNOWN' semester type. No semester record created.")
            else:
                print(f"Warning: Missing or invalid semester ID or name for CourseAvailability {avail_id}. Skipping semester creation.")
    db_instance.session.commit()
    print("Semesters seeded.")

    # --- Seed Courses (without FeeID assignment here) ---
    course_objects = {}
    # Fee calculation and CourseFee creation logic moved to seed_course_fees.py
    # FeeID on Course will be set by seed_course_fees.py as part of its process.

    if 'courses' in data:
        for c_id, c_data in data['courses'].items():
            course_code = c_data['code']
            existing_course = db_instance.session.get(Course, course_code)
            if existing_course:
                print(f"Skipping existing Course: {c_data['name']} (ID: {course_code})")
                course_objects[course_code] = existing_course
                continue 

            assigned_subprogram_id = default_subprogram_id
            if assigned_subprogram_id not in subprogram_objects:
                print(f"Critical Error: Default SubProgram '{default_subprogram_id}' not found. Cannot assign a SubProgram to Course {course_code}. Skipping course.")
                continue

            course = Course(
                CourseID=course_code,
                SubProgramID=assigned_subprogram_id,
                CourseName=c_data['name'],
                PrerequisiteCourseID=None, # Will be updated in second pass
                FeeID=None # Explicitly set to None here; seed_course_fees.py will update this
            )
            db_instance.session.add(course)
            course_objects[course_code] = course
    db_instance.session.commit()
    print("Courses seeded (without fees).") # Updated message


    # Second pass to update prerequisites after all courses are added
    if 'courses' in data:
        for c_id, c_data in data['courses'].items():
            course = course_objects.get(c_data['code'])
            if course and c_data.get('course_prerequisites_id') and c_data['course_prerequisites_id'] != 'UNKNOWN':
                prereq_key_in_json = c_data['course_prerequisites_id']
                prereq_info = data['prerequisites'].get(prereq_key_in_json)
                
                if prereq_info and prereq_info.get('course_id') and prereq_info['course_id'] != 'UNKNOWN':
                    prereq_course_code = prereq_info['course_id']
                    if prereq_course_code in course_objects:
                        course.PrerequisiteCourseID = course_objects[prereq_course_code].CourseID
                    else:
                        print(f"Warning: Prerequisite course '{prereq_course_code}' not found in 'courses' data for {c_data['code']}. Skipping prerequisite assignment for this course.")
                elif prereq_info and prereq_info.get('course_id') == 'UNKNOWN':
                    print(f"Info: Prerequisite for {c_data['code']} is marked as 'UNKNOWN'. Skipping assignment.")
                else:
                    print(f"Warning: Prerequisite ID '{prereq_key_in_json}' not found in 'prerequisites' data for {c_data['code']}. Skipping prerequisite assignment.")
    db_instance.session.commit()
    print("Courses prerequisites updated.")


    # --- Seed CourseAvailability ---
    if 'course_availability' in data:
        for avail_id, avail_data in data['course_availability'].items():
            existing_avail = db_instance.session.get(CourseAvailability, avail_data['id'])
            if existing_avail:
                print(f"Skipping existing CourseAvailability: {avail_id}")
                continue

            course_code = avail_data['course_id']
            semester_id = avail_data['semtype_id']
            
            if course_code in course_objects and semester_id in semester_objects:
                course_availability = CourseAvailability(
                    CourseAvailabilityID=avail_id,
                    isAvailable=avail_data['offered'],
                    CourseID=course_objects[course_code].CourseID,
                    SemesterID=semester_objects[semester_id].SemesterID
                )
                db_instance.session.add(course_availability)
            elif course_code not in course_objects:
                print(f"Warning: Course '{course_code}' not found for CourseAvailability {avail_id}. Skipping.")
            elif semester_id not in semester_objects:
                print(f"Warning: Semester '{semester_id}' not found for CourseAvailability {avail_id}. Skipping.")
            elif semester_id == 'UNKNOWN':
                print(f"Info: Skipping CourseAvailability {avail_id} due to 'UNKNOWN' semester type.")

    db_instance.session.commit()
    print("CourseAvailability seeded.")

    # --- Seed Students and Users ---
    student_objects = {}
    student_level_id_counter = 1 # Counter for generated StudentLevelID

    if 'students' in data:
        for s_id_key, s_data in data['students'].items():
            student_id_to_use = s_data.get('id') or s_data.get('studentId') or s_id_key

            existing_student = db_instance.session.get(Student, student_id_to_use)
            if existing_student:
                print(f"Skipping existing Student: {s_data.get('firstName', '')} {s_data.get('lastName', '')} (ID: {student_id_to_use})")
                student_objects[student_id_to_use] = existing_student
                user = db_instance.session.get(User, student_id_to_use)
                if not user:
                    first_name = s_data.get('firstName', '').lower()
                    last_name = s_data.get('lastName', '').lower()
                    username = f"{first_name}{last_name}" if first_name and last_name else student_id_to_use.lower()
                    email = f"{username}@example.com"
                    user = User(id=student_id_to_use, username=username, email=email, role='student')
                    user.set_password(s_data.get('password', s_data.get('password:', 'default_password')))
                    db_instance.session.add(user)
                    db_instance.session.commit()
                continue

            first_name = s_data.get('firstName', '')
            last_name = s_data.get('lastName', '')
            raw_password = s_data.get('password') or s_data.get('password:', 'default_password')
            
            username = f"{first_name.lower()}{last_name.lower()}" if first_name and last_name else student_id_to_use.lower()
            email = f"{username}@example.com"
            
            user = User(
                id=student_id_to_use,
                username=username,
                email=email,
                role='student'
            )
            user.set_password(raw_password)
            db_instance.session.add(user)

            student_level_name = s_data.get('programLevel') or s_data.get('studentLevel')
            student_level_id = None
            if student_level_name:
                existing_level = db_instance.session.query(StudentLevel).filter_by(LevelName=student_level_name).first()
                if not existing_level:
                    new_level_id = f"LVL{student_level_id_counter:03d}"
                    while db_instance.session.get(StudentLevel, new_level_id):
                        student_level_id_counter += 1
                        new_level_id = f"LVL{student_level_id_counter:03d}"

                    new_level = StudentLevel(
                        StudentLevelID=new_level_id,
                        LevelName=student_level_name,
                        StudentID=student_id_to_use
                    )
                    db_instance.session.add(new_level)
                    db_instance.session.flush()
                    student_level_id = new_level.StudentLevelID
                    student_level_id_counter += 1
                else:
                    student_level_id = existing_level.StudentLevelID

            else:
                print(f"Warning: Student {student_id_to_use} has no programLevel/studentLevel. StudentLevelID will be NULL.")

            dob_str = s_data.get('dob') or s_data.get('dateOfBirth')
            parsed_dob = None
            if dob_str:
                try:
                    parsed_dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
                except ValueError:
                    print(f"Warning: Invalid date format for DOB '{dob_str}' for student {student_id_to_use}. Setting to None.")
            
            created_at_str = s_data.get('createdAt')
            parsed_created_at = None
            if created_at_str:
                try:
                    parsed_created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                except ValueError:
                    print(f"Warning: Invalid ISO date format for createdAt '{created_at_str}' for student {student_id_to_use}. Using current UTC datetime.")
                    parsed_created_at = datetime.utcnow()
            else:
                parsed_created_at = datetime.utcnow()

            student = Student(
                StudentID=student_id_to_use,
                FirstName=first_name,
                LastName=last_name,
                MiddleName=s_data.get('middleName'),
                DateOfBirth=parsed_dob,
                Gender=s_data.get('gender'),
                Address=s_data.get('address'),
                Contact=s_data.get('contact'),
                Citizenship=s_data.get('citizenship'),
                CampusID=s_data.get('campus'),
                ProgramID=None,
                SubProgramID=None,
                StudentLevelID=student_level_id,
                CreatedAt=parsed_created_at
            )

            program_name_from_student_data = s_data.get('programName') or s_data.get('program')
            subprogram_name_from_student_data = s_data.get('subprogram') or s_data.get('subProgram')

            if program_name_from_student_data:
                linked_program = db_instance.session.query(Program).filter_by(ProgramName=program_name_from_student_data).first()
                if linked_program:
                    student.ProgramID = linked_program.ProgramID
                else:
                    print(f"Warning: Program '{program_name_from_student_data}' for student {student_id_to_use} not found in seeded programs. Skipping ProgramID for student.")
            
            if subprogram_name_from_student_data:
                linked_subprogram = db_instance.session.query(SubProgram).filter_by(SubProgramName=subprogram_name_from_student_data).first()
                if linked_subprogram:
                    student.SubProgramID = linked_subprogram.SubProgramID
                else:
                    print(f"Warning: SubProgram '{subprogram_name_from_student_data}' for student {student_id_to_use} not found in seeded subprograms. Skipping SubProgramID for student.")

            db_instance.session.add(student)
            student_objects[student_id_to_use] = student
            
    db_instance.session.commit()
    print("Students and Users seeded.")

    # --- Seed Holds ---
    if 'holds' in data:
        for h_id_key, h_data in data['holds'].items():
            hold_id = h_data.get('id') or h_id_key
            
            existing_hold = db_instance.session.get(Hold, hold_id)
            if existing_hold:
                print(f"Skipping existing Hold: {hold_id}")
                continue

            student_id = h_data.get('studentID')
            if student_id in student_objects:
                hold_date_str = h_data.get('holdDate')
                hold_date = None
                if hold_date_str:
                    try:
                        hold_date = datetime.strptime(hold_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        print(f"Warning: Invalid date format '{hold_date_str}' for hold {hold_id}. Using current date.")
                        hold_date = datetime.utcnow().date()
                else:
                    student_original_entry = None
                    for s_key, s_val in data['students'].items():
                        if (s_val.get('id') == student_id) or (s_val.get('studentId') == student_id):
                            student_original_entry = s_val
                            break

                    if student_original_entry and student_original_entry.get('createdAt'):
                        try:
                            hold_date = datetime.fromisoformat(student_original_entry['createdAt'].replace('Z', '+00:00')).date()
                        except ValueError:
                            print(f"Warning: Invalid ISO date format '{student_original_entry['createdAt']}' for student creation date. Using current date for hold {hold_id}.")
                            hold_date = datetime.utcnow().date()
                    else:
                        hold_date = datetime.utcnow().date()
                        
                lift_date_str = h_data.get('liftDate')
                lift_date = None
                if lift_date_str:
                    try:
                        lift_date = datetime.strptime(lift_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        print(f"Warning: Invalid date format '{lift_date_str}' for liftDate of hold {hold_id}. Setting to None.")
                
                hold = Hold(
                    HoldID=hold_id,
                    reason=h_data.get('reason'),
                    status=h_data.get('status', 'Active'),
                    holdDate=hold_date,
                    liftDate=lift_date,
                    StudentID=student_objects[student_id].StudentID
                )
                db_instance.session.add(hold)
            else:
                print(f"Warning: Student '{student_id}' not found for Hold {h_id_key}. Skipping.")
    db_instance.session.commit()
    print("Holds seeded.")
    
    # --- Seed StudentCourseFee ---
    student_course_fee_counter = 1
    if 'student_course_fee' in data:
        for scf_key, scf_data in data['student_course_fee'].items():
            student_id = scf_data.get('studentID')
            course_code = scf_data.get('course_id')
            amount = scf_data.get('amount')

            if student_id in student_objects and course_code in course_objects:
                new_scf_id = f"SCF{student_course_fee_counter:05d}"
                while db_instance.session.get(StudentCourseFee, new_scf_id):
                    student_course_fee_counter += 1
                    new_scf_id = f"SCF{student_course_fee_counter:05d}"

                due_date_str = scf_data.get('dueDate')
                due_date = None
                if due_date_str:
                    try:
                        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        print(f"Warning: Invalid date format '{due_date_str}' for student_course_fee {scf_key}. Using current date.")
                        due_date = datetime.utcnow().date()
                else:
                    print(f"Warning: Missing due date for student_course_fee {scf_key}. Using current date.")
                    due_date = datetime.utcnow().date()

                paid_date = None
                status = scf_data.get('status', 'Outstanding')

                fee_id_for_link = None
                course_obj = course_objects.get(course_code)
                if course_obj and course_obj.FeeID:
                    fee_id_for_link = course_obj.FeeID
                else:
                    print(f"Warning: No CourseFee linked to Course '{course_code}'. FeeID for StudentCourseFee '{new_scf_id}' will be NULL.")


                student_course_fee = StudentCourseFee(
                    StudentCourseFeeID=new_scf_id,
                    due_date=due_date,
                    paid_date=paid_date,
                    status=status,
                    amount=float(amount) if amount is not None else 0.0,
                    StudentID=student_objects[student_id].StudentID,
                    CourseID=course_objects[course_code].CourseID,
                    FeeID=fee_id_for_link
                )
                db_instance.session.add(student_course_fee)
                student_course_fee_counter += 1
            else:
                print(f"Warning: Incomplete or invalid student/course data for StudentCourseFee entry '{scf_key}'. Skipping.")
    db_instance.session.commit()
    print("StudentCourseFees seeded.")

    # --- Seed Enrollments ---
    enrollment_counter = 1
    if 'student_course_fee' in data:
        for scf_key, scf_data in data['student_course_fee'].items():
            student_id = scf_data.get('studentID')
            course_code = scf_data.get('course_id')

            if student_id in student_objects and course_code in course_objects:
                existing_enrollment = db_instance.session.query(Enrollment).filter_by(
                    StudentID=student_objects[student_id].StudentID,
                    CourseID=course_objects[course_code].CourseID
                ).first()
                
                if existing_enrollment:
                    print(f"Skipping existing Enrollment for Student '{student_id}' in Course '{course_code}'.")
                    continue

                new_enrollment_id = f"ENR{enrollment_counter:05d}"
                while db_instance.session.get(Enrollment, new_enrollment_id):
                    enrollment_counter += 1
                    new_enrollment_id = f"ENR{enrollment_counter:05d}"

                enrollment = Enrollment(
                    EnrollmentID=new_enrollment_id,
                    EnrollmentDate=datetime.utcnow().date(),
                    StudentID=student_objects[student_id].StudentID,
                    CourseID=course_objects[course_code].CourseID
                )
                db_instance.session.add(enrollment)
                enrollment_counter += 1
            else:
                print(f"Warning: Student '{student_id}' or Course '{course_code}' not found for enrollment based on student_course_fee '{scf_key}'. Skipping enrollment.")
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

        json_file_name = 'data.json'
        
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root_dir = os.path.dirname(current_script_dir)
        json_file_path = os.path.join(project_root_dir, json_file_name)
        
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