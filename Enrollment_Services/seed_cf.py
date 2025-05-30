import json
import os
import random
import re
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

def get_year_from_course_code(course_code):
    """
    Extracts the first digit from a course code to determine the year level.
    Returns 0 if no digit is found or for special cases.
    """
    if course_code in ['CS001', 'UU100A']:
        return 0  # Special case for free units
    
    # Use regex to find the first digit in the string
    match = re.search(r'(\d)', course_code)
    if match:
        return int(match.group(1))
    return None  # Return None if no digit is found

def assign_fee_by_year(year):
    """
    Assigns a random fee based on the year level.
    """
    if year == 0:  # For 'CS001' and 'UU100A'
        return 0.0
    elif year == 1: # Year 1 units randomly store fee in between 400 to 500
        return float(random.randint(400, 500))
    elif year == 2: # Year 2 units randomly store fee in between 600 to 700
        return float(random.randint(600, 700))
    elif year == 3: # Year 3 units randomly store fee in between 700 to 800
        return float(random.randint(700, 800))
    elif year == 4: # Year 4 units randomly store fee in between 1000 to 1500
        return float(random.randint(1000, 1500))
    else:  # Any unit greater than year 4 store them to 1500 fixed.
        return 1500.0

def seed_course_fees_data(json_data, db_instance):
    """
    Deletes existing CourseFee data and then seeds the CourseFee table with new data
    extracted from JSON, assigning fees based on the extracted year from the course code.
    Assumes Course data is already present in the database.
    """
    print("Starting CourseFee data seeding (with year-based fees)...")

    # --- Step 1: Delete existing CourseFee records ---
    try:
        num_deleted = db_instance.session.query(CourseFee).delete()
        db_instance.session.commit()
        print(f"Successfully deleted {num_deleted} existing CourseFee records.")
    except Exception as e:
        db_instance.session.rollback()
        print(f"Error deleting existing CourseFee records: {e}")
        return # Exit if deletion fails to prevent inconsistent state

    course_fees_to_add = []
    fee_id_counter = 1

    if 'courses' in json_data:
        for course_key_from_json, course_info_from_json in json_data['courses'].items():
            course_code = course_info_from_json.get('code')
            
            if not course_code:
                print(f"Warning: Course entry {course_key_from_json} has no 'code'. Skipping fee creation.")
                continue

            # Check if the Course already exists in the DB
            # We now only check for existence, not for pre-existing fees, since we cleared them.
            existing_course = db_instance.session.get(Course, course_code)
            if not existing_course:
                print(f"Info: Course '{course_code}' not found in DB. Skipping CourseFee creation for it.")
                continue

            # Extract year from course code
            year = get_year_from_course_code(course_code)
            if year is None:
                print(f"Warning: Could not determine year for course code '{course_code}'. Skipping fee assignment.")
                continue
            
            # Assign fee based on the determined year
            calculated_fee = assign_fee_by_year(year)

            # Create unique FeeID and CourseFee object
            new_fee_id = f"CFEE{fee_id_counter:05d}"
            # No need to check for existing new_fee_id in DB, as we deleted all.
            # But we keep the loop just in case new_fee_id_generation becomes more complex
            # or if this function is called multiple times without a full DB reset.
            # For this specific scenario (fresh delete), a simple increment is fine.
            
            course_fee = CourseFee(
                FeeID=new_fee_id,
                amount=calculated_fee,
                description=f"Fee for Year {year} unit {course_code}",
                CourseID=course_code
            )
            
            # Special description for free units
            if year == 0:
                course_fee.description = f"Free unit: {course_code}"

            course_fees_to_add.append(course_fee)
            fee_id_counter += 1

    if course_fees_to_add:
        db_instance.session.add_all(course_fees_to_add)
        try:
            db_instance.session.commit()
            print(f"Successfully added {len(course_fees_to_add)} CourseFee records.")
        except Exception as e:
            db_instance.session.rollback()
            print(f"An error occurred during CourseFee insertion: {e}")
    else:
        print("No new CourseFee records to add.")

    print("CourseFee data seeding complete.")

if __name__ == '__main__':
    app = create_app_for_seeding()
    with app.app_context():
        json_file_name = 'data.json'
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root_dir = os.path.dirname(current_script_dir)
        json_file_path = os.path.join(project_root_dir, json_file_name)
        
        print(f"Attempting to load JSON from: {json_file_path}")

        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                json_data_content = json.load(f)
            
            if db.session.query(Course).count() == 0:
                print("Warning: Course table is empty. Please run the main seed_db.py first to populate Course data.")
                # You might want to exit here or call the main seeding script if this is a critical dependency.

            seed_course_fees_data(json_data_content, db)
        except FileNotFoundError:
            print(f"Error: JSON file not found at {json_file_path}")
        except Exception as e:
            print(f"An unexpected error occurred during CourseFee seeding: {type(e).__name__}: {e}")
            db.session.rollback()