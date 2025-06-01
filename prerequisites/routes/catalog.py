from flask import Blueprint, render_template, abort
from flask import current_app as app
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

catalog_bp = Blueprint("catalog_bp", __name__, template_folder="../templates")

@catalog_bp.route("/")
def list_programs():
    """
    List all programs in the database.
    Renders: templates/catalog.html
    """
    Base = automap_base()
    Base.prepare(app.db.engine, reflect=True)
    Program = Base.classes.program

    session = Session(app.db.engine)
    programs = session.query(Program).order_by(Program.program_id).all()
    session.close()

    return render_template("catalog.html", programs=programs)

@catalog_bp.route("/<int:program_id>/courses")
def show_program_courses(program_id):
    """
    Show all courses in a given program, and list their prerequisites.
    Renders: templates/program_detail.html
    """
    Base = automap_base()
    Base.prepare(app.db.engine, reflect=True)
    Program = Base.classes.program
    ProgramCourse = Base.classes.program_course
    Course = Base.classes.course
    Prerequisite = Base.classes.prerequisite

    session = Session(app.db.engine)

    program = session.query(Program).filter_by(program_id=program_id).first()
    if not program:
        session.close()
        abort(404, f"Program with ID {program_id} not found.")

    program_courses = (
        session.query(ProgramCourse, Course)
        .join(Course, ProgramCourse.course_id == Course.course_id)
        .filter(ProgramCourse.program_id == program_id)
        .order_by(Course.course_id)
        .all()
    )

    course_map = {}
    for pc, course in program_courses:
        course_map[course.course_id] = {
            "course": course,
            "prerequisites": []
        }

    for cid in course_map.keys():
        prereq_rows = (
            session.query(Prerequisite, Course)
            .join(Course, Prerequisite.prereq_id == Course.course_id)
            .filter(Prerequisite.course_id == cid)
            .all()
        )
        for prereq_obj, prereq_course in prereq_rows:
            course_map[cid]["prerequisites"].append(prereq_course)

    session.close()

    return render_template(
        "program_detail.html",
        program=program,
        course_map=course_map
    )
