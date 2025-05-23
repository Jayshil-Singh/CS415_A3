# SAS_Services/init_dp.py

import os
import xml.etree.ElementTree as ET
from sqlalchemy import text
from app import app # Import the Flask 'app' instance
# Import ALL models, including the new SubProgram and the association table (though SQLAlchemy handles association table creation)
from models import db, Student, Program, Student_Program, Student_Level, Campus, ProgramType, SubProgram

DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'xml_data')

def get_xml_data_for_init(filename, list_element_name, item_element_name, value_attribute):
    xml_file_path = os.path.join(DATA_FOLDER, filename)
    data_list = []
    if not os.path.exists(xml_file_path):
        print(f"Warning: XML file not found at {xml_file_path}")
        return data_list
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        container = root.find(list_element_name) if root.tag != list_element_name else root
        if container is not None:
            for item_node in container.findall(item_element_name):
                item_text = item_node.get(value_attribute) if value_attribute else (item_node.text.strip() if item_node.text else None)
                if item_text:
                    data_list.append(item_text)
    except Exception as e:
        print(f"Error parsing XML file {filename}: {e}")
    return data_list

def populate_initial_data():
    """Populates Campus, ProgramType, and SubProgram tables."""
    # Populate Campuses
    print("Populating Campus table...")
    campus_names_from_xml = get_xml_data_for_init(
        filename='campuses.xml', list_element_name='campuses',
        item_element_name='campus', value_attribute='campusName'
    )
    added_campuses = 0
    for name in campus_names_from_xml:
        if name and not Campus.query.filter_by(CampusName=name).first():
            campus = Campus(CampusName=name)
            db.session.add(campus)
            added_campuses += 1
    if added_campuses > 0:
        db.session.commit()
    print(f"Campus table populated/updated. {added_campuses} new campuses added. Total: {Campus.query.count()}.")

    # Populate Program Types
    print("\nPopulating ProgramType table...")
    program_types_data = [
        {"name": "Single Major", "desc": "Requires one primary area of study (major/subprogram)."},
        {"name": "Double Major", "desc": "Requires two primary areas of study (majors/subprograms)."},
        {"name": "Prescribed Program", "desc": "A structured program with a fixed set of courses."}
    ]
    added_program_types = 0
    for pt_data in program_types_data:
        if not ProgramType.query.filter_by(ProgramTypeName=pt_data["name"]).first():
            program_type = ProgramType(ProgramTypeName=pt_data["name"], Description=pt_data["desc"])
            db.session.add(program_type)
            added_program_types +=1
    if added_program_types > 0:
        db.session.commit()
    print(f"ProgramType table populated/updated. {added_program_types} new types added. Total: {ProgramType.query.count()}.")

    # NEW: Populate SubProgram table
    print("\nPopulating SubProgram table...")
    subprogram_names_from_xml = get_xml_data_for_init(
        filename='subprogrammes.xml', # Corrected filename
        list_element_name='subprograms',
        item_element_name='subprogram',
        value_attribute='subprogramName'
    )
    added_subprograms = 0
    for name in subprogram_names_from_xml:
        if name and not SubProgram.query.filter_by(SubProgramName=name).first():
            sub_program = SubProgram(SubProgramName=name)
            db.session.add(sub_program)
            added_subprograms += 1
    if added_subprograms > 0:
        db.session.commit()
    print(f"SubProgram table populated/updated. {added_subprograms} new subprograms added. Total: {SubProgram.query.count()}.")


def update_schema_and_populate(): # Renamed function for clarity
    with app.app_context():
        print("Ensuring all tables defined in models are created (if they don't exist)...")
        # db.create_all() will create new tables (Campus, ProgramType, SubProgram, Student_SubProgram)
        # and will NOT modify existing tables if their schema changed.
        # For schema changes on existing tables, manual ALTER or migrations are needed.
        # Since we added columns to Student and Student_Program, we need to handle that.
        
        # For simplicity in development, if you're okay with resetting data:
        # 1. Drop all tables
        # 2. Create all tables
        # This is the easiest if you don't need to preserve existing student data.
        # Otherwise, you'd need ALTER TABLE commands like in message #36.
        
        # Option A: Full Reset (DELETES ALL DATA) - Uncomment if you want this
        # print("Attempting to DROP ALL TABLES for a clean schema...")
        # db.drop_all()
        # print("All tables dropped.")
        # db.create_all()
        # print("All tables recreated.")
        # populate_initial_data()
        # print("Initial data populated.")

        # Option B: Create new tables and attempt to ALTER existing ones (more complex)
        # This assumes you ran the ALTER TABLE logic from message #36 for CampusID and ProgramTypeID previously.
        # Now we just need to ensure the new SubProgram and Student_SubProgram tables are created.
        db.create_all() # This will create SubProgram and Student_SubProgram if they don't exist.
        print("New tables (SubProgram, Student_SubProgram) created if they didn't exist.")
        populate_initial_data() # Populate lookup tables (Campus, ProgramType, SubProgram)

        print("\n--------------------------------------------------------------------")
        print("Database schema update and initial data population process finished.")
        print(f"Database is located at: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print("--------------------------------------------------------------------")


if __name__ == '__main__':
    print("This script will ensure all tables are created and lookup tables are populated.")
    print("If you chose the full reset option (uncommented in the script), it will delete all existing data.")
    confirm = input(f"Are you sure you want to proceed with schema setup/update at '{app.config['SQLALCHEMY_DATABASE_URI']}'? (yes/no): ")
    if confirm.lower() == 'yes':
        update_schema_and_populate()
    else:
        print("Database operation cancelled by user.")
