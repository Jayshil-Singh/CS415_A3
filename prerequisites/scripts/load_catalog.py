
"""One-off script to load course catalog, programs, mappings, and prerequisites.
Expects four CSV files in the same folder:
    - courses.csv          id,name,semester
    - programs.csv         id,name
    - program_courses.csv  program_id,course_id
    - prereq.csv           course_id,prereq_id
Adjust paths as necessary.
"""
import csv, pathlib
from app import create_app
from models import db, Course, Program, ProgramCourse, Prerequisite

BASE = pathlib.Path(__file__).parent

def load_csv(name):
    with open(BASE / f"{name}.csv", newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def main():
    courses   = load_csv("courses")
    programs  = load_csv("programs")
    prog_map  = load_csv("program_courses")
    prereqs   = load_csv("prereq")

    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        db.session.bulk_save_objects([Course(**row) for row in courses])
        db.session.bulk_save_objects([Program(**row) for row in programs])
        db.session.bulk_save_objects([ProgramCourse(**row) for row in prog_map])
        db.session.bulk_save_objects([Prerequisite(**row) for row in prereqs])

        db.session.commit()
        print("✅ Catalog & prerequisite graph loaded.")

if __name__ == "__main__":
    main()
