from utils import db

class Course(db.Model):
    __tablename__ = 'course'
    id = db.Column('course_id', db.String, primary_key=True)
    name = db.Column('course_name', db.String, nullable=False)
    semester = db.Column('semester_offered', db.String)

class Program(db.Model):
    __tablename__ = 'program'
    id = db.Column('program_id', db.String, primary_key=True)
    name = db.Column('name', db.String, nullable=False)

class ProgramCourse(db.Model):
    __tablename__ = 'program_course'
    program_id = db.Column('program_id', db.String, db.ForeignKey('program.program_id'), primary_key=True)
    course_id  = db.Column('course_id',  db.String, db.ForeignKey('course.course_id'),  primary_key=True)

class Prerequisite(db.Model):
    __tablename__ = 'prerequisite'
    id = db.Column('id', db.Integer, primary_key=True)
    course_id = db.Column('course_id', db.String, db.ForeignKey('course.course_id'), nullable=False)
    prerequisite_course_id = db.Column('prerequisite_course_id', db.String, db.ForeignKey('course.course_id'), nullable=False)

class StudentCourse(db.Model):
    __tablename__ = 'student_course'
    student_id = db.Column(db.String, primary_key=True)
    course_id  = db.Column(db.String, primary_key=True)
    grade      = db.Column(db.String)
