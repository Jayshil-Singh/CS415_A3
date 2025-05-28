import json
import os
import random # Import the random module
from flask import Flask
from enrollment_services.db import db
from enrollment_services.model import Course, CourseFee

def create_app_for_seeding():
    """
    Creates a minimal Flask app context for database operations,
    targeting the database within enrollment_services/instance.
    """
    app = Flask(__name__)
    
    # Determine the current directory of this script (enrollment_services)
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # The 'instance' directory is now expected to be a direct child of 'enrollment_services'
    db_instance_dir = os.path.join(current_script_dir, 'instance')
    db_path = os.path.join(db_instance_dir, 'enrollment.db')
    
    os.makedirs(db_instance_dir, exist_ok=True) # Ensure the 'instance' directory exists

    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

def seed_course_fees_data(json_data, db_instance):
    """
    Seeds the CourseFee table with data extracted from JSON,
    randomly assigning fees between 500 and 1000.
    Assumes Course data is already present in the database.
    """
    print("Starting CourseFee data seeding (with random fees between 500-1000)...")

    course_fees_to_add = []
    fee_id_counter = 1

    if 'courses' in json_data:
        for course_key_from_json, course_info_from_json in json_data['courses'].items():
            course_code = course_info_from_json.get('code')
            
            if not course_code:
                print(f"Warning: Course entry {course_key_from_json} has no 'code'. Skipping fee creation.")
                continue

            # Check if the Course already exists in the DB
            existing_course = db_instance.session.get(Course, course_code)
            if not existing_course:
                print(f"Info: Course '{course_code}' not found in DB. Skipping CourseFee creation for it.")
                continue

            # Check if a CourseFee for this CourseID already exists to prevent duplicates
            existing_course_fee_for_course = db_instance.session.query(CourseFee).filter_by(CourseID=course_code).first()
            if existing_course_fee_for_course:
                print(f"Info: CourseFee already exists for Course '{course_code}'. Skipping creation.")
                continue

            # --- Randomly assign fee between 500 and 1000 ---
            calculated_fee = float(random.randint(500, 1000)) # Generate random fee as float

            # --- Create unique FeeID and CourseFee object ---
            new_fee_id = f"CFEE{fee_id_counter:05d}"
            while db_instance.session.get(CourseFee, new_fee_id): # Check if this generated ID already exists
                fee_id_counter += 1
                new_fee_id = f"CFEE{fee_id_counter:05d}"
            
            course_fee = CourseFee(
                FeeID=new_fee_id,
                amount=calculated_fee,
                description=f"Randomly assigned fee for {course_code}", # Update description
                CourseID=course_code # Link to the Course
            )
            course_fees_to_add.append(course_fee)
            fee_id_counter += 1 # Increment for the next potential new ID

    if course_fees_to_add:
        db_instance.session.add_all(course_fees_to_add)
        db_instance.session.commit()
        print(f"Successfully added {len(course_fees_to_add)} CourseFee records.")
    else:
        print("No new CourseFee records to add.")

    print("CourseFee data seeding complete.")

if __name__ == '__main__':
    app = create_app_for_seeding()
    with app.app_context():
        # Define the path to your main data.json file
        json_file_name = 'data.json' # Assuming data.json is still at the project root
        
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up from 'enrollment_services' to 'CS415_A3' to find data.json
        project_root_dir = os.path.dirname(current_script_dir) 
        json_file_path = os.path.join(project_root_dir, json_file_name)
        
        print(f"Attempting to load JSON from: {json_file_path}")

        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                json_data_content = json.load(f)
            
            # Ensure the Course table is populated BEFORE running this script
            if db.session.query(Course).count() == 0:
                print("Warning: Course table is empty. Please run the main seed_db.py first to populate Course data.")
                # It's highly recommended to run the main seed_db.py before this script
                # or integrate this logic directly into your main seed_db.py if you want
                # a single seeding step that handles everything.

            seed_course_fees_data(json_data_content, db)
        except FileNotFoundError:
            print(f"Error: JSON file not found at {json_file_path}")
        except Exception as e:
            print(f"An unexpected error occurred during CourseFee seeding: {type(e).__name__}: {e}")
            db.session.rollback()