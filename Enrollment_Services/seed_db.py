# seed_db.py

import json
from datetime import datetime
import os
import random 

# Adjust these imports based on your exact project structure and package naming
from enrollment_services.db import db
from enrollment_services.model import (
    User, Program, SubProgram, Semester, Course, CourseAvailability,
    Student, StudentLevel, Hold, CourseFee, StudentCourseFee, Enrollment,
    Grade, GradeRecheck, SpecialApplication, ServiceAccess
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
    """

    print("Starting data seeding...")

    # --- Create Default Program and SubProgram (if they don't exist) ---
    # These are used for linking programs/subprograms that are not explicitly defined in the JSON.
    default_program_id = 'PROG000'
    default_subprogram_id = 'SUBPROG000'
    default_semester_id = 'SEMTYPE_DEFAULT' # Added default semester for 'UNKNOWN' types
    default_course_id = 'DEFAULT_COURSE' # Added default course for student fees/enrollments without a course_id

    # Ensure default program exists
    existing_default_program = db_instance.session.get(Program, default_program_id)
    if not existing_default_program:
        default_program = Program(ProgramID=default_program_id, ProgramName='Default Program')
        db_instance.session.add(default_program)
        db_instance.session.flush() # Flush to make it available for SubProgram linking
        print(f"Created default Program: {default_program_id}")
    program_objects = {default_program_id: db_instance.session.get(Program, default_program_id)}


    # Ensure default subprogram exists and links to default program
    existing_default_subprogram = db_instance.session.get(SubProgram, default_subprogram_id)
    if not existing_default_subprogram:
        default_subprogram = SubProgram(
            SubProgramID=default_subprogram_id,
            SubProgramName='General Studies (Default)',
            SubProgramType='General',
            ProgramID=default_program_id # Link to the default program
        )
        db_instance.session.add(default_subprogram)
        db_instance.session.flush() # Flush to make it available for Course linking
        print(f"Created default SubProgram: {default_subprogram_id}")
    subprogram_objects = {default_subprogram_id: db_instance.session.get(SubProgram, default_subprogram_id)}

    # Ensure default semester exists
    existing_default_semester = db_instance.session.get(Semester, default_semester_id)
    if not existing_default_semester:
        default_semester = Semester(SemesterID=default_semester_id, SemesterName='Default Semester')
        db_instance.session.add(default_semester)
        db_instance.session.flush()
        print(f"Created default Semester: {default_semester_id}")
    semester_objects = {default_semester_id: db_instance.session.get(Semester, default_semester_id)}

    # Ensure default course exists (linked to default subprogram)
    existing_default_course = db_instance.session.get(Course, default_course_id)
    if not existing_default_course:
        default_course = Course(
            CourseID=default_course_id,
            SubProgramID=default_subprogram_id, # Link to default subprogram
            CourseName='Default Placeholder Course',
            credit_hours=1.0
        )
        db_instance.session.add(default_course)
        db_instance.session.flush()
        print(f"Created default Course: {default_course_id}")
    course_objects = {default_course_id: db_instance.session.get(Course, default_course_id)}


    # --- Seed Programs (FIRST - to ensure program_objects are fully populated) ---
    if 'programs' in data:
        for p_id_key, p_data in data['programs'].items():
            program_id_to_use = p_data['id']
            if program_id_to_use == default_program_id:
                continue

            existing_program = db_instance.session.get(Program, program_id_to_use)
            if existing_program:
                # print(f"Skipping existing Program: {p_data['name']} (ID: {program_id_to_use})")
                program_objects[program_id_to_use] = existing_program
                continue

            program = Program(
                ProgramID=program_id_to_use,
                ProgramName=p_data['name']
            )
            db_instance.session.add(program)
            program_objects[program_id_to_use] = program
            
    db_instance.session.commit()
    print("Programs seeded.")

    # --- Seed SubPrograms (SECOND - link to already seeded programs) ---
    # Build a reverse map from SubProgramID (in JSON) to ProgramID (from JSON)
    program_to_subprogram_linkage = {}
    if 'programs' in data:
        for p_id_key, p_data in data['programs'].items():
            program_to_subprogram_linkage[p_data['subprogramme_id']] = p_data['id'] # Map SUBPROG_ID -> PROG_ID

    if 'subprogrammes' in data and 'subPrograms' in data['subprogrammes']:
        for sp_id, sp_data in data['subprogrammes']['subPrograms'].items():
            subprogram_id_to_use = sp_data['id']
            if subprogram_id_to_use == default_subprogram_id:
                continue

            existing_subprogram = db_instance.session.get(SubProgram, subprogram_id_to_use)
            if existing_subprogram:
                # print(f"Skipping existing SubProgram: {sp_data['subProgramName']} (ID: {subprogram_id_to_use})")
                subprogram_objects[subprogram_id_to_use] = existing_subprogram
                continue

            # Link to program using the map, default to PROG000 if not found
            linked_program_id = program_to_subprogram_linkage.get(subprogram_id_to_use, default_program_id)
            if linked_program_id not in program_objects:
                # Fallback if map points to a non-existent program (shouldn't happen if programs seeded first)
                linked_program_id = default_program_id
                print(f"Warning: SubProgram {subprogram_id_to_use} ({sp_data['subProgramName']}) linked to unknown Program ID '{linked_program_id}'. Assigning to default program '{default_program_id}'.")
            
            subprogram = SubProgram(
                SubProgramID=subprogram_id_to_use,
                SubProgramName=sp_data['subProgramName'],
                SubProgramType=sp_data.get('SubProgramType', 'General'), # Use JSON type if available
                ProgramID=linked_program_id
            )
            db_instance.session.add(subprogram)
            subprogram_objects[subprogram_id_to_use] = subprogram
    db_instance.session.commit()
    print("SubPrograms seeded.")


    # --- Seed Semesters ---
    if 'course_availability' in data:
        for avail_id, avail_data in data['course_availability'].items():
            sem_id = avail_data.get('semtype_id')
            sem_name = avail_data.get('semester')
            if sem_id and sem_name and sem_id != 'UNKNOWN':
                if sem_id not in semester_objects: # Check if semester already collected/seeded
                    existing_semester = db_instance.session.get(Semester, sem_id)
                    if existing_semester:
                        semester_objects[sem_id] = existing_semester
                        continue

                    semester = Semester(
                        SemesterID=sem_id,
                        SemesterName=sem_name
                    )
                    db_instance.session.add(semester)
                    semester_objects[sem_id] = semester
            # 'UNKNOWN' semester types handled by defaulting in CourseAvailability seeding

    # Add other common semesters if not in data.json but needed for CourseAvailability
    common_semesters = [
        ('Semester 1', 'Semester 1'),
        ('Semester 2', 'Semester 2'),
        ('Summer Semester', 'Summer'),
        ('Trimester 1', 'Trimester 1'),
        ('Trimester 2', 'Trimester 2'),
        ('Trimester 3', 'Trimester 3'),
    ]
    for sem_name_full, sem_name_short in common_semesters:
        sem_id = sem_name_full.replace(' ', '') # Simple ID generation if not explicitly in JSON
        if sem_id not in semester_objects:
            existing_semester = db_instance.session.get(Semester, sem_id)
            if existing_semester:
                semester_objects[sem_id] = existing_semester
            else:
                new_sem = Semester(SemesterID=sem_id, SemesterName=sem_name_full)
                db_instance.session.add(new_sem)
                semester_objects[sem_id] = new_sem
    
    db_instance.session.commit()
    print("Semesters seeded.")

    # --- Seed Courses ---
    # First pass: Create Course objects.
    # Note: 'credit_hours' is not in data.json's courses, so we assume a default.
    # If your PROGRAM_STRUCTURE has 'units', we could try to map that.
    # For now, Course model default `credit_hours=1.0` is used.
    if 'courses' in data:
        for c_key, c_data in data['courses'].items():
            course_code = c_data['code']
            existing_course = db_instance.session.get(Course, course_code)
            if existing_course:
                # print(f"Skipping existing Course: {c_data['name']} (ID: {course_code})")
                course_objects[course_code] = existing_course
                continue 

            # Default subprogram assignment for courses not explicitly linked via Program structure in JSON
            assigned_subprogram_id = default_subprogram_id # Default course to default subprogram
            if assigned_subprogram_id not in subprogram_objects:
                 print(f"Critical Error: Default SubProgram '{default_subprogram_id}' not found. Cannot assign a SubProgram to Course {course_code}. Skipping course.")
                 continue

            course = Course(
                CourseID=course_code,
                SubProgramID=assigned_subprogram_id, # Assign to default subprogram
                CourseName=c_data['name'],
                # PrerequisiteCourseID will be updated in second pass
                # FeeID handled by seed_course_fees.py
                credit_hours=c_data.get('units', 1.0) # Use 'units' from JSON if available, else default
            )
            db_instance.session.add(course)
            course_objects[course_code] = course
    db_instance.session.commit()
    print("Courses seeded (initial pass).")

    # Second pass: Update prerequisites after all courses are added
    if 'courses' in data:
        for c_key, c_data in data['courses'].items():
            course_obj_to_update = course_objects.get(c_data['code'])
            if course_obj_to_update and c_data.get('course_prerequisites_id') and c_data['course_prerequisites_id'] != 'UNKNOWN':
                prereq_key_in_json = c_data['course_prerequisites_id']
                prereq_info = data['prerequisites'].get(prereq_key_in_json)
                
                if prereq_info and prereq_info.get('course_id') and prereq_info['course_id'] != 'UNKNOWN':
                    prereq_course_code = prereq_info['course_id']
                    if prereq_course_code in course_objects:
                        course_obj_to_update.PrerequisiteCourseID = course_objects[prereq_course_code].CourseID
                    else:
                        print(f"Warning: Prerequisite course '{prereq_course_code}' not found in 'courses' data for {c_data['code']}. Skipping prerequisite assignment for this course.")
                elif prereq_info and prereq_info.get('course_id') == 'UNKNOWN':
                    # This means the prerequisite is explicitly 'UNKNOWN' in the JSON
                    # print(f"Info: Prerequisite for {c_data['code']} is marked as 'UNKNOWN'. Skipping assignment.")
                    pass # Do nothing, PrerequisiteCourseID remains None
                else:
                    print(f"Warning: Prerequisite ID '{prereq_key_in_json}' not found in 'prerequisites' data for {c_data['code']}. Skipping prerequisite assignment.")
    db_instance.session.commit()
    print("Courses prerequisites updated.")


    # --- Seed CourseAvailability ---
    if 'course_availability' in data:
        for avail_id, avail_data in data['course_availability'].items():
            existing_avail = db_instance.session.get(CourseAvailability, avail_data['id'])
            if existing_avail:
                # print(f"Skipping existing CourseAvailability: {avail_id}")
                continue

            course_code = avail_data['course_id']
            semester_id_from_json = avail_data.get('semtype_id')
            semester_name_from_json = avail_data.get('semester')
            
            # Use default semester if 'UNKNOWN' or missing
            actual_semester_id = semester_id_from_json if semester_id_from_json and semester_id_from_json != 'UNKNOWN' else default_semester_id

            if course_code in course_objects and actual_semester_id in semester_objects:
                course_availability = CourseAvailability(
                    CourseAvailabilityID=avail_id,
                    isAvailable=avail_data['offered'],
                    CourseID=course_objects[course_code].CourseID,
                    SemesterID=semester_objects[actual_semester_id].SemesterID
                )
                db_instance.session.add(course_availability)
            elif course_code not in course_objects:
                print(f"Warning: Course '{course_code}' not found for CourseAvailability {avail_id}. Skipping CourseAvailability entry.")
            elif actual_semester_id not in semester_objects:
                print(f"Warning: Semester '{actual_semester_id}' not found for CourseAvailability {avail_id}. Skipping CourseAvailability entry.")
            else: # This else might catch cases where semtype_id is UNKNOWN and sem_name is missing.
                 # Handled by `actual_semester_id` logic above.
                 pass

    db_instance.session.commit()
    print("CourseAvailability seeded.")

    # --- Seed Students and Users ---
    student_objects = {} # Use top-level JSON key (e.g., "S001") as key, and the Student object as value
    student_level_id_counter = 1 

    if 'students' in data:
        for s_json_key, s_data in data['students'].items(): # Iterate using the key from JSON (e.g., "S001")
            student_id_from_json_data = s_data.get('id') or s_data.get('studentId') # Preferred ID from nested data
            final_student_id = student_id_from_json_data if student_id_from_json_data else s_json_key # Fallback to top-level key

            existing_student = db_instance.session.get(Student, final_student_id)
            if existing_student:
                # print(f"Skipping existing Student: {s_data.get('firstName', '')} {s_data.get('lastName', '')} (ID: {final_student_id})")
                student_objects[final_student_id] = existing_student # Store existing student
                user = db_instance.session.get(User, final_student_id)
                if not user: # If student exists but user doesn't, create user
                    first_name = s_data.get('firstName', '').lower()
                    last_name = s_data.get('lastName', '').lower()
                    username_candidate = f"{first_name}{last_name}" if first_name and last_name else final_student_id.lower()
                    email = s_data.get('email', f"{username_candidate}@example.com") 
                    user = User(id=final_student_id, username=username_candidate, email=email, role='student',
                                FirstName=first_name, LastName=last_name)
                    user.set_password(s_data.get('password', s_data.get('password:', 'default_password')))
                    db_instance.session.add(user)
                    db_instance.session.flush() # Flush user to ensure ID is available
                continue

            first_name = s_data.get('firstName', '')
            last_name = s_data.get('lastName', '')
            raw_password = s_data.get('password') or s_data.get('password:', 'default_password')
            
            username = f"{first_name.lower()}{last_name.lower()}" if first_name and last_name else final_student_id.lower()
            email = s_data.get('email', f"{username}@example.com") 
            
            user = User(
                id=final_student_id,
                username=username,
                email=email,
                role='student',
                FirstName=first_name,
                LastName=last_name
            )
            user.set_password(raw_password)
            db_instance.session.add(user)

            student_level_name = s_data.get('programLevel') or s_data.get('studentLevel')
            student_level_id_for_student = None # Local variable for student.StudentLevelID
            if student_level_name:
                existing_level = db_instance.session.query(StudentLevel).filter_by(LevelName=student_level_name).first()
                if not existing_level:
                    # Generate a unique ID for the new StudentLevel
                    new_level_id = f"LVL{student_level_id_counter:03d}"
                    while db_instance.session.get(StudentLevel, new_level_id): # Ensure uniqueness
                        student_level_id_counter += 1
                        new_level_id = f"LVL{student_level_id_counter:03d}"

                    new_level = StudentLevel(
                        StudentLevelID=new_level_id,
                        LevelName=student_level_name,
                        StudentID=None # Will link when Student object is added, or can be linked here
                    )
                    db_instance.session.add(new_level)
                    db_instance.session.flush()
                    student_level_id_for_student = new_level.StudentLevelID
                    student_level_id_counter += 1
                else:
                    student_level_id_for_student = existing_level.StudentLevelID
            else:
                print(f"Warning: Student {final_student_id} has no programLevel/studentLevel. StudentLevelID will be NULL.")

            dob_str = s_data.get('dob') or s_data.get('dateOfBirth')
            parsed_dob = None
            if dob_str:
                try:
                    parsed_dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
                except ValueError:
                    print(f"Warning: Invalid date format for DOB '{dob_str}' for student {final_student_id}. Setting to None.")
            
            created_at_str = s_data.get('createdAt')
            parsed_created_at = None
            if created_at_str:
                try:
                    # Handle Z suffix for UTC
                    parsed_created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                except ValueError:
                    print(f"Warning: Invalid ISO date format for createdAt '{created_at_str}' for student {final_student_id}. Using current UTC datetime.")
                    parsed_created_at = datetime.utcnow()
            else:
                parsed_created_at = datetime.utcnow()

            student = Student(
                StudentID=final_student_id,
                FirstName=first_name,
                LastName=last_name,
                MiddleName=s_data.get('middleName'),
                DateOfBirth=parsed_dob,
                Gender=s_data.get('gender'),
                Address=s_data.get('address'),
                Contact=s_data.get('contact'),
                Citizenship=s_data.get('citizenship'),
                CampusID=s_data.get('campus'),
                ProgramID=None, # Will link below
                SubProgramID=None, # Will link below
                StudentLevelID=student_level_id_for_student,
                CreatedAt=parsed_created_at
            )

            program_name_from_student_data = s_data.get('programName') or s_data.get('program')
            subprogram_name_from_student_data = s_data.get('subprogram') or s_data.get('subProgram')

            if program_name_from_student_data:
                linked_program = db_instance.session.query(Program).filter_by(ProgramName=program_name_from_student_data).first()
                if linked_program:
                    student.ProgramID = linked_program.ProgramID
                else:
                    print(f"Warning: Program '{program_name_from_student_data}' for student {final_student_id} not found in seeded programs. Skipping ProgramID for student.")
            
            if subprogram_name_from_student_data:
                linked_subprogram = db_instance.session.query(SubProgram).filter_by(SubProgramName=subprogram_name_from_student_data).first()
                if linked_subprogram:
                    student.SubProgramID = linked_subprogram.SubProgramID
                else:
                    print(f"Warning: SubProgram '{subprogram_name_from_student_data}' for student {final_student_id} not found in seeded subprograms. Skipping SubProgramID for student.")

            db_instance.session.add(student)
            student_objects[final_student_id] = student # Store the student object using its final_student_id
            
    db_instance.session.commit()
    print("Students and Users seeded.")

    # --- Seed Holds ---
    if 'holds' in data:
        for h_id_key, h_data in data['holds'].items():
            # Use JSON key as fallback ID if no 'id' field in nested data
            hold_id = h_data.get('id') or h_id_key
            
            existing_hold = db_instance.session.get(Hold, hold_id)
            if existing_hold:
                # print(f"Skipping existing Hold: {hold_id}")
                continue

            student_id_for_hold = h_data.get('studentID') # From JSON holds section
            
            # Use the final_student_id from student_objects for lookup consistency
            if student_id_for_hold in student_objects: 
                student_obj_for_hold = student_objects[student_id_for_hold] # Retrieve the Student object

                hold_date_str = h_data.get('holdDate')
                hold_date = None
                if hold_date_str:
                    try:
                        hold_date = datetime.strptime(hold_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        print(f"Warning: Invalid date format '{hold_date_str}' for hold {hold_id}. Using student creation date or current date.")
                        hold_date = student_obj_for_hold.CreatedAt.date() if student_obj_for_hold.CreatedAt else datetime.utcnow().date()
                else:
                    hold_date = student_obj_for_hold.CreatedAt.date() if student_obj_for_hold.CreatedAt else datetime.utcnow().date()
                        
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
                    StudentID=student_obj_for_hold.StudentID,
                    imposed_by_user_id=None # Defaulting to None as no admin info in JSON
                )
                db_instance.session.add(hold)
            else:
                print(f"Warning: Student '{student_id_for_hold}' not found in seeded students for Hold {hold_id}. Skipping.")
    db_instance.session.commit()
    print("Holds seeded.")
    
    # --- Seed Course Fees (assuming minimal data or from a separate seed_course_fees.py) ---
    # Your JSON doesn't provide CourseFee entries. This section will add a default fee
    # for `DEFAULT_COURSE_ID` if it doesn't exist, to ensure referential integrity for SCF.
    default_course_fee_id = 'FEE_DEFAULT'
    if not db_instance.session.get(CourseFee, default_course_fee_id):
        default_fee = CourseFee(
            FeeID=default_course_fee_id,
            amount=100.0,
            description="Default Fee",
            CourseID=default_course_id
        )
        db_instance.session.add(default_fee)
        db_instance.session.flush()
        print(f"Created default CourseFee: {default_course_fee_id}")
    
    # --- Seed StudentCourseFee ---
    student_course_fee_counter = 1
    if 'student_course_fee' in data:
        for scf_key, scf_data in data['student_course_fee'].items():
            # The JSON 'student_course_fee' does NOT have a 'course_id'.
            # It only has 'studentID', 'amount', 'dueDate'.
            # We must assign a course for the database.
            # We will use the default_course_id.
            student_id = scf_data.get('studentID')
            
            # Using random.choice to assign a course if no course_id is provided in JSON
            # This is a band-aid. Ideally, data.json should have course_id for SCF.
            # Otherwise, consider if CourseID in StudentCourseFee should be nullable.
            available_course_ids = list(course_objects.keys())
            if not available_course_ids:
                print("Error: No courses seeded to assign to StudentCourseFee. Skipping SCF.")
                break
            
            # Assign a course. For a real system, you'd know which course this fee is for.
            # Here, we'll pick a random one if the data is ambiguous, or use default.
            assigned_course_id_for_scf = scf_data.get('course_id') # Try to get if present (though JSON doesn't show it)
            if not assigned_course_id_for_scf or assigned_course_id_for_scf not in course_objects:
                # Fallback to default course if not found or not in JSON
                assigned_course_id_for_scf = default_course_id
                print(f"Warning: Course ID not found for StudentCourseFee '{scf_key}'. Assigning to default course '{default_course_id}'.")


            if student_id in student_objects and assigned_course_id_for_scf in course_objects:
                new_scf_id = scf_data.get('StudentCourseFeeID') or f"SCF{student_course_fee_counter:05d}"
                while db_instance.session.get(StudentCourseFee, new_scf_id):
                    student_course_fee_counter += 1
                    new_scf_id = f"SCF{student_course_fee_counter:05d}"

                due_date_str = scf_data.get('dueDate')
                due_date = None
                if due_date_str:
                    try:
                        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        print(f"Warning: Invalid date format '{due_date_str}' for student_course_fee {new_scf_id}. Using current date.")
                        due_date = datetime.utcnow().date()
                else:
                    # print(f"Warning: Missing due date for student_course_fee {new_scf_id}. Using current date.")
                    due_date = datetime.utcnow().date()

                paid_date = None # No paid_date in JSON snippet
                status = scf_data.get('status', 'Outstanding')

                fee_id_for_link = None
                # Check if a CourseFee exists for the assigned course
                # If your CourseFee table has FeeID as primary key, you need to look it up.
                # Assuming simple CourseID-to-FeeID mapping or using the default.
                course_fee_for_scf = db_instance.session.query(CourseFee).filter_by(CourseID=assigned_course_id_for_scf).first()
                if course_fee_for_scf:
                    fee_id_for_link = course_fee_for_scf.FeeID
                else:
                    fee_id_for_link = default_course_fee_id
                    print(f"Warning: No CourseFee found for Course '{assigned_course_id_for_scf}'. Linking to default fee '{default_course_fee_id}'.")


                student_course_fee = StudentCourseFee(
                    StudentCourseFeeID=new_scf_id,
                    due_date=due_date,
                    paid_date=paid_date,
                    status=status,
                    amount=float(scf_data.get('amount', 0.0)),
                    StudentID=student_objects[student_id].StudentID,
                    CourseID=course_objects[assigned_course_id_for_scf].CourseID, # Use assigned course_id
                    FeeID=fee_id_for_link
                )
                db_instance.session.add(student_course_fee)
                student_course_fee_counter += 1
            else:
                print(f"Warning: Student '{student_id}' or Course '{assigned_course_id_for_scf}' not found for StudentCourseFee entry '{scf_key}'. Skipping.")
    db_instance.session.commit()
    print("StudentCourseFees seeded.")

    # --- Seed Enrollments ---
    enrollment_counter = 1
    if 'student_course_fee' in data: # Re-using student_course_fee data to create enrollments
        for scf_key, scf_data in data['student_course_fee'].items():
            student_id = scf_data.get('studentID')
            course_code = scf_data.get('course_id') # Assume this field exists based on previous SCF logic

            # Use the same assigned course ID logic as for SCF
            assigned_course_id_for_enrollment = scf_data.get('course_id')
            if not assigned_course_id_for_enrollment or assigned_course_id_for_enrollment not in course_objects:
                assigned_course_id_for_enrollment = default_course_id
                # print(f"Warning: Course ID not found for Enrollment based on '{scf_key}'. Assigning to default course '{default_course_id}'.")


            if student_id in student_objects and assigned_course_id_for_enrollment in course_objects:
                existing_enrollment = db_instance.session.query(Enrollment).filter_by(
                    StudentID=student_objects[student_id].StudentID,
                    CourseID=course_objects[assigned_course_id_for_enrollment].CourseID
                ).first()
                
                if existing_enrollment:
                    # print(f"Skipping existing Enrollment for Student '{student_id}' in Course '{assigned_course_id_for_enrollment}'.")
                    continue

                new_enrollment_id = f"ENR{enrollment_counter:05d}"
                while db_instance.session.get(Enrollment, new_enrollment_id):
                    enrollment_counter += 1
                    new_enrollment_id = f"ENR{enrollment_counter:05d}"

                enrollment = Enrollment(
                    EnrollmentID=new_enrollment_id,
                    EnrollmentDate=datetime.utcnow().date(), # Set enrollment date to current date
                    StudentID=student_objects[student_id].StudentID,
                    CourseID=course_objects[assigned_course_id_for_enrollment].CourseID
                )
                db_instance.session.add(enrollment)
                enrollment_counter += 1
            else:
                print(f"Warning: Student '{student_id}' or Course '{assigned_course_id_for_enrollment}' not found for enrollment based on student_course_fee '{scf_key}'. Skipping enrollment.")
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

        # Ensure that ServiceAccess default entries are created here
        # This part of the seeding should happen after db.create_all() but before seeding from JSON
        # as the JSON doesn't contain ServiceAccess data.
        service_names = ['course_registration', 'view_course_grades', 'view_programme_structure',
                         'apply_grade_recheck', 'apply_graduation']
        
        for name in service_names:
            existing_service = ServiceAccess.query.filter_by(service_name=name).first()
            if not existing_service:
                db.session.add(ServiceAccess(service_name=name, is_available_on_hold=True))
                print(f"Seeding default service: {name}")
        db.session.commit()
        print("Default ServiceAccess entries seeded.")


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