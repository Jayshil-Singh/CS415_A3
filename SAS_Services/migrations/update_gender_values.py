"""Update gender values to uppercase

This migration updates all existing gender values in the Student table
to use uppercase values (MALE, FEMALE, OTHER) to match the GenderEnum.
"""

import os
import sqlite3

def update_database(db_path, gender_mapping):
    """Helper function to update gender values in a specific database."""
    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Update each gender value
        for old_value, new_value in gender_mapping.items():
            cursor.execute(
                "UPDATE Student SET Gender = ? WHERE Gender = ?",
                (new_value, old_value)
            )
        
        conn.commit()
        print(f"Successfully updated gender values to uppercase in {os.path.basename(db_path)}")
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error updating gender values in {os.path.basename(db_path)}: {e}")
        raise
    finally:
        if conn:
            conn.close()

def upgrade():
    # Get the paths to both databases
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    enrollment_db_path = os.path.join(base_dir, 'instance', 'enrollment.db')
    student_service_db_path = os.path.join(os.path.dirname(base_dir), 'StudentService', 'instance', 'studentservice.db')
    
    # Create a temporary mapping of old to new values
    gender_mapping = {
        'Male': 'MALE',
        'Female': 'FEMALE',
        'Other': 'OTHER'
    }
    
    # Update both databases
    update_database(enrollment_db_path, gender_mapping)
    update_database(student_service_db_path, gender_mapping)

def downgrade():
    # Get the paths to both databases
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    enrollment_db_path = os.path.join(base_dir, 'instance', 'enrollment.db')
    student_service_db_path = os.path.join(os.path.dirname(base_dir), 'StudentService', 'instance', 'studentservice.db')
    
    # Create a temporary mapping of new to old values
    gender_mapping = {
        'MALE': 'Male',
        'FEMALE': 'Female',
        'OTHER': 'Other'
    }
    
    # Update both databases
    update_database(enrollment_db_path, gender_mapping)
    update_database(student_service_db_path, gender_mapping) 