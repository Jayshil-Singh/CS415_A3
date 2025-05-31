# enrollment_services/model.py

from .db import db
from datetime import datetime
from sqlalchemy import PrimaryKeyConstraint, UniqueConstraint
from werkzeug.security import generate_password_hash, check_password_hash

# --- User Management Entities ---
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(50), primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='student')
    FirstName = db.Column(db.String(100), nullable=True)
    LastName = db.Column(db.String(100), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} (ID: {self.id}, Role: {self.role})>'

class Program(db.Model):
    __tablename__ = 'Program'
    ProgramID = db.Column(db.String(50), primary_key=True)
    ProgramName = db.Column(db.String(255), nullable=False)

    subprograms_associated = db.relationship(
        'SubProgram',
        backref='program',
        foreign_keys='SubProgram.ProgramID',
        lazy=True
    )
    students = db.relationship(
        'Student',
        backref='program_obj',
        foreign_keys='Student.ProgramID',
        lazy=True
    )

    def __repr__(self):
        return f"<Program {self.ProgramName} (ID: {self.ProgramID})>"


class SubProgram(db.Model):
    __tablename__ = 'SubPrograms'
    SubProgramID = db.Column(db.String(50), primary_key=True)
    SubProgramName = db.Column(db.String(255), nullable=False)
    SubProgramType = db.Column(db.String(100), nullable=True)
    ProgramID = db.Column(db.String(50), db.ForeignKey('Program.ProgramID'), nullable=False)

    courses = db.relationship('Course', back_populates='subprogram', lazy=True)
    students = db.relationship(
        'Student',
        backref='subprogram_obj',
        foreign_keys='Student.SubProgramID',
        lazy=True
    )

    def __repr__(self):
        return f"<SubProgram {self.SubProgramName} ({self.SubProgramID})>"


class Semester(db.Model):
    __tablename__ = 'Semester'
    SemesterID = db.Column(db.String(50), primary_key=True)
    SemesterName = db.Column(db.String(100), nullable=False)

    course_availabilities = db.relationship('CourseAvailability', back_populates='semester', lazy=True)

    def __repr__(self):
        return f"<Semester {self.SemesterName} ({self.SemesterID})>"

class Course(db.Model):
    __tablename__ = 'Course'
    CourseID = db.Column(db.String(50), primary_key=True)
    SubProgramID = db.Column(db.String(50), db.ForeignKey('SubPrograms.SubProgramID'), nullable=False)
    CourseName = db.Column(db.String(255), nullable=False)
    PrerequisiteCourseID = db.Column(db.String(50), db.ForeignKey('Course.CourseID'), nullable=True)
    
    credit_hours = db.Column(db.Float, nullable=False, default=1.0) 

    subprogram = db.relationship('SubProgram', back_populates='courses')
    prerequisite_for = db.relationship('Course', remote_side=[CourseID], backref='prerequisite', lazy=True)
    course_availabilities = db.relationship('CourseAvailability', back_populates='course', lazy=True)
    enrollments = db.relationship('Enrollment', back_populates='course', lazy=True)
    student_course_fees = db.relationship('StudentCourseFee', back_populates='course', lazy=True)
    
    course_fees_records = db.relationship('CourseFee', back_populates='course', lazy=True)

    def __repr__(self):
        return f"<Course {self.CourseName} ({self.CourseID})>"

class CourseAvailability(db.Model):
    __tablename__ = 'CourseAvailability'
    CourseAvailabilityID = db.Column(db.String(50), primary_key=True)
    isAvailable = db.Column(db.Boolean, nullable=False, default=True) 
    CourseID = db.Column(db.String(50), db.ForeignKey('Course.CourseID'), nullable=False)
    SemesterID = db.Column(db.String(50), db.ForeignKey('Semester.SemesterID'), nullable=False)

    course = db.relationship('Course', back_populates='course_availabilities')
    semester = db.relationship('Semester', back_populates='course_availabilities')

    def __repr__(self):
        return f"<CourseAvailability Course:{self.CourseID} Semester:{self.SemesterID} Available:{self.isAvailable}>"

# --- Student Related Entities ---

class Student(db.Model):
    __tablename__ = 'Student'
    StudentID = db.Column(db.String(50), primary_key=True)
    FirstName = db.Column(db.String(100), nullable=True)
    LastName = db.Column(db.String(100), nullable=True)
    MiddleName = db.Column(db.String(100), nullable=True)
    DateOfBirth = db.Column(db.Date, nullable=True)
    Gender = db.Column(db.String(10), nullable=True)
    Address = db.Column(db.String(255), nullable=True)
    Contact = db.Column(db.String(50), nullable=True)
    Citizenship = db.Column(db.String(100), nullable=True)
    CampusID = db.Column(db.String(50), nullable=True)
    ProgramID = db.Column(db.String(50), db.ForeignKey('Program.ProgramID'), nullable=True)
    SubProgramID = db.Column(db.String(50), db.ForeignKey('SubPrograms.SubProgramID'), nullable=True)
    StudentLevelID = db.Column(db.String(50), db.ForeignKey('Student_Level.StudentLevelID'), nullable=True) # MADE NULLABLE
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    Email = db.Column(db.String(255), unique=True, nullable=True)

    enrollments = db.relationship('Enrollment', back_populates='student', lazy=True)
    student_course_fees = db.relationship('StudentCourseFee', back_populates='student', lazy=True)
    holds = db.relationship('Hold', back_populates='student', lazy=True)
    
    student_levels_records = db.relationship(
        'StudentLevel',
        back_populates='student',
        foreign_keys='StudentLevel.StudentID',
        lazy=True,
        overlaps="student_levels_records"
    )

    program_relation = db.relationship('Program', foreign_keys=[ProgramID], overlaps="program_obj,students")
    subprogram_relation = db.relationship('SubProgram', foreign_keys=[SubProgramID], overlaps="subprogram_obj,students")


    def __repr__(self):
        return f"<Student {self.FirstName} {self.LastName} ({self.StudentID})>"

class StudentLevel(db.Model):
    __tablename__ = 'Student_Level'
    StudentLevelID = db.Column(db.String(50), primary_key=True)
    LevelName = db.Column(db.String(255), nullable=True)
    AttributeName1 = db.Column(db.String(255), nullable=True)
    AttributeName2 = db.Column(db.String(255), nullable=True)
    StudentID = db.Column(db.String(50), db.ForeignKey('Student.StudentID'), nullable=True) # CHANGED TO NULLABLE=TRUE

    student = db.relationship('Student', back_populates='student_levels_records', foreign_keys=[StudentID])

    def __repr__(self):
        return f"<StudentLevel {self.LevelName} (ID: {self.StudentLevelID}) for Student {self.StudentID}>"

class Hold(db.Model):
    __tablename__ = 'Holds'
    HoldID = db.Column(db.String(50), primary_key=True)
    reason = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default='Active')
    holdDate = db.Column(db.Date, default=datetime.utcnow)
    liftDate = db.Column(db.Date, nullable=True)
    StudentID = db.Column(db.String(50), db.ForeignKey('Student.StudentID'), nullable=False)
    imposed_by_user_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=True) 

    student = db.relationship('Student', back_populates='holds')
    imposed_by_user = db.relationship('User', foreign_keys=[imposed_by_user_id], lazy=True)

    def __repr__(self):
        return f"<Hold {self.HoldID} for Student {self.StudentID} - Status: {self.status}>"

# --- Enrollment & Fees Entities ---

class Enrollment(db.Model):
    __tablename__ = 'Enrollment'
    EnrollmentID = db.Column(db.String(50), primary_key=True)
    EnrollmentDate = db.Column(db.Date, default=datetime.utcnow)
    StudentID = db.Column(db.String(50), db.ForeignKey('Student.StudentID'), nullable=False)
    CourseID = db.Column(db.String(50), db.ForeignKey('Course.CourseID'), nullable=False)

    student = db.relationship('Student', back_populates='enrollments')
    course = db.relationship('Course', back_populates='enrollments')

    def __repr__(self):
        return f"<Enrollment {self.EnrollmentID} Student:{self.StudentID} Course:{self.CourseID}>"

class CourseFee(db.Model):
    __tablename__ = 'Course_Fees'
    FeeID = db.Column(db.String(50), primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    CourseID = db.Column(db.String(50), db.ForeignKey('Course.CourseID'), nullable=False)

    course = db.relationship('Course', back_populates='course_fees_records', foreign_keys=[CourseID])
    student_course_fees = db.relationship('StudentCourseFee', back_populates='course_fee', lazy=True)

    def __repr__(self):
        return f"<CourseFee {self.FeeID} Amount:{self.amount} Course:{self.CourseID}>"

class StudentCourseFee(db.Model):
    __tablename__ = 'Student_Course_Fees'
    StudentCourseFeeID = db.Column(db.String(50), primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    paid_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(50), default='Outstanding')
    StudentID = db.Column(db.String(50), db.ForeignKey('Student.StudentID'), nullable=False)
    CourseID = db.Column(db.String(50), db.ForeignKey('Course.CourseID'), nullable=True) # CourseID is now nullable for cases where it's not present in JSON
    FeeID = db.Column(db.String(50), db.ForeignKey('Course_Fees.FeeID'), nullable=True)

    student = db.relationship('Student', back_populates='student_course_fees')
    course = db.relationship('Course', back_populates='student_course_fees')
    course_fee = db.relationship('CourseFee', back_populates='student_course_fees')

    def __repr__(self):
        return f"<StudentCourseFee {self.StudentCourseFeeID} Student:{self.StudentID} Course:{self.CourseID} Status:{self.status}>"

# --- New Models (not directly from JSON, but defined for the system) ---

class Grade(db.Model):
    __tablename__ = 'grades'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), db.ForeignKey('Student.StudentID'), nullable=False)
    course_id = db.Column(db.String(50), db.ForeignKey('Course.CourseID'), nullable=False)
    letter_grade = db.Column(db.String(5), nullable=False)
    numerical_grade = db.Column(db.Float, nullable=True)
    year = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.String(20), nullable=False)

    student = db.relationship('Student', backref='grades_records', lazy=True)
    course = db.relationship('Course', backref='course_grades_records', lazy=True)

    __table_args__ = (UniqueConstraint('student_id', 'course_id', 'year', 'semester', name='_student_course_year_semester_uc'),)

    def __repr__(self):
        return f"<Grade {self.id} | Student: {self.student_id}, Course: {self.course_id}, Grade: {self.letter_grade}>"


class GradeRecheck(db.Model):
    __tablename__ = 'grade_rechecks'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), db.ForeignKey('Student.StudentID'), nullable=False)
    grade_id = db.Column(db.Integer, db.ForeignKey('grades.id'), nullable=False)
    course_id = db.Column(db.String(50), db.ForeignKey('Course.CourseID'), nullable=False)
    original_grade = db.Column(db.String(5), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Pending', nullable=False)
    admin_notes = db.Column(db.Text, nullable=True)
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    date_resolved = db.Column(db.DateTime, nullable=True)
    new_grade_if_changed = db.Column(db.String(5), nullable=True)

    student = db.relationship('Student', backref='grade_rechecks', lazy=True)
    grade = db.relationship('Grade', backref='recheck_requests', lazy=True)
    course = db.relationship('Course', backref='recheck_requests_for_course', lazy=True)

    def __repr__(self):
        return f"<GradeRecheck {self.id} | Student: {self.student_id}, Grade: {self.grade_id}, Status: {self.status}>"


class SpecialApplication(db.Model):
    __tablename__ = 'special_applications'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), db.ForeignKey('Student.StudentID'), nullable=False)
    application_type = db.Column(db.String(50), nullable=False)
    course_id = db.Column(db.String(50), db.ForeignKey('Course.CourseID'), nullable=True)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Pending', nullable=False)
    admin_notes = db.Column(db.Text, nullable=True)
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    date_resolved = db.Column(db.DateTime, nullable=True)
    external_form_path = db.Column(db.String(255), nullable=True)

    student = db.relationship('Student', backref='special_applications', lazy=True)
    course = db.relationship('Course', backref='special_applications_for_course', lazy=True)

    def __repr__(self):
        return f"<SpecialApplication {self.id} | Student: {self.student_id}, Type: {self.application_type}, Status: {self.status}>"


class ServiceAccess(db.Model):
    __tablename__ = 'service_access'
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(100), unique=True, nullable=False)
    is_available_on_hold = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<ServiceAccess {self.id} | Name: {self.service_name}, AvailableOnHold: {self.is_available_on_hold}>"