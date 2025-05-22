# enrollment_services/model.py
from .db import db
from datetime import datetime
from sqlalchemy import PrimaryKeyConstraint # Import PrimaryKeyConstraint for composite keys
from werkzeug.security import generate_password_hash, check_password_hash # Import for password hashing
# --- Core Entities ---
# --- User Management Entities (NEW SECTION) ---
class User(db.Model):
    __tablename__ = 'users' # Good practice to name tables in plural
    id = db.Column(db.String(50), primary_key=True) # Corresponds to student_id, manager_id etc.
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False) # Store hashed password
    role = db.Column(db.String(50), nullable=False, default='student') # e.g., 'student', 'sas_manager', 'admin'

    def set_password(self, password):
        """Hashes the password and stores it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} (ID: {self.id}, Role: {self.role})>'

class Program(db.Model):
    __tablename__ = 'Program'
    # REVISED: ProgramID is now the ONLY primary key for Program
    ProgramID = db.Column(db.String(50), primary_key=True)
    # REMOVED: SubProgramID as part of Program's composite primary key

    ProgramName = db.Column(db.String(255), nullable=False)

    # Relationships:
    # This relationship assumes Program has many SubPrograms, linked by SubProgram.ProgramID.
    # The 'backref' ensures the reverse relationship is available from SubProgram.
    subprograms_associated = db.relationship(
        'SubProgram',
        backref='program', # Renamed backref to avoid potential conflict if Program had a direct 'subprograms' attribute before
        foreign_keys='SubProgram.ProgramID', # This explicitly refers to the ProgramID column in the SubProgram table
        lazy=True
    )

    def __repr__(self):
        # Changed repr to reflect ProgramID as the sole PK
        return f"<Program {self.ProgramName} (ID: {self.ProgramID})>"


class SubProgram(db.Model):
    __tablename__ = 'SubPrograms'
    SubProgramID = db.Column(db.String(50), primary_key=True)
    SubProgramName = db.Column(db.String(255), nullable=False)
    SubProgramType = db.Column(db.String(100))
    # This is the foreign key linking back to the Program table's ProgramID
    ProgramID = db.Column(db.String(50), db.ForeignKey('Program.ProgramID'), nullable=False) # This is correct and requires a non-null value

    # Relationships: Explicitly tell SQLAlchemy which foreign key to use.
    # The 'program' relationship will now be handled by the 'subprograms_associated' backref on Program.
    # No direct 'program' relationship needed here if using backref.
    # program = db.relationship('Program', back_populates='subprograms', foreign_keys='SubProgram.ProgramID') # REMOVED/ADJUSTED
    courses = db.relationship('Course', back_populates='subprogram', lazy=True)

    def __repr__(self):
        return f"<SubProgram {self.SubProgramName} ({self.SubProgramID})>"


class Semester(db.Model):
    __tablename__ = 'Semester'
    SemesterID = db.Column(db.String(50), primary_key=True)
    SemesterName = db.Column(db.String(100), nullable=False)
    # No direct FK to CourseID here, as CourseAvailability handles Course-Semester relationship
    # Relationship to CourseAvailability is implied by CourseAvailability having SemesterID

    def __repr__(self):
        return f"<Semester {self.SemesterName} ({self.SemesterID})>"

class Course(db.Model):
    __tablename__ = 'Course'
    CourseID = db.Column(db.String(50), primary_key=True)
    SubProgramID = db.Column(db.String(50), db.ForeignKey('SubPrograms.SubProgramID'), nullable=False)
    CourseName = db.Column(db.String(255), nullable=False)
    PrerequisiteCourseID = db.Column(db.String(50), db.ForeignKey('Course.CourseID'), nullable=True) # Self-referencing FK

    # Relationships
    subprogram = db.relationship('SubProgram', back_populates='courses')
    # For self-referencing relationships, remote_side is crucial.
    prerequisite_for = db.relationship('Course', remote_side=[CourseID], backref='prerequisite', lazy=True)
    course_availabilities = db.relationship('CourseAvailability', back_populates='course', lazy=True)
    course_fees = db.relationship('CourseFee', back_populates='course', lazy=True)
    enrollments = db.relationship('Enrollment', back_populates='course', lazy=True)
    student_course_fees = db.relationship('StudentCourseFee', back_populates='course', lazy=True)


    def __repr__(self):
        return f"<Course {self.CourseName} ({self.CourseID})>"

class CourseAvailability(db.Model):
    __tablename__ = 'CourseAvailability'
    CourseAvailabilityID = db.Column(db.String(50), primary_key=True)
    isAvailable = db.Column(db.Boolean, nullable=False, default=True)
    CourseID = db.Column(db.String(50), db.ForeignKey('Course.CourseID'), nullable=False)
    SemesterID = db.Column(db.String(50), db.ForeignKey('Semester.SemesterID'), nullable=False)

    # Relationships
    course = db.relationship('Course', back_populates='course_availabilities')
    semester = db.relationship('Semester') # Assuming Semester doesn't need a backref from CourseAvailability

    def __repr__(self):
        return f"<CourseAvailability Course:{self.CourseID} Semester:{self.SemesterID} Available:{self.isAvailable}>"

# --- Student Related Entities (Simplified for this microservice scope) ---

class Student(db.Model):
    __tablename__ = 'Student'
    StudentID = db.Column(db.String(50), primary_key=True)
    FirstName = db.Column(db.String(100))
    LastName = db.Column(db.String(100))
    Email = db.Column(db.String(255), unique=True)

    # Relationships
    enrollments = db.relationship('Enrollment', back_populates='student', lazy=True)
    student_course_fees = db.relationship('StudentCourseFee', back_populates='student', lazy=True)
    holds = db.relationship('Hold', back_populates='student', lazy=True)
    student_levels = db.relationship('StudentLevel', back_populates='student', lazy=True)

    def __repr__(self):
        return f"<Student {self.FirstName} {self.LastName} ({self.StudentID})>"

class StudentLevel(db.Model):
    __tablename__ = 'Student_Level'
    StudentLevelID = db.Column(db.String(50), primary_key=True)
    AttributeName1 = db.Column(db.String(255))
    AttributeName2 = db.Column(db.String(255))
    StudentID = db.Column(db.String(50), db.ForeignKey('Student.StudentID'), nullable=False)

    student = db.relationship('Student', back_populates='student_levels')

    def __repr__(self):
        return f"<StudentLevel {self.StudentLevelID} for Student {self.StudentID}>"

class Hold(db.Model):
    __tablename__ = 'Holds'
    # Changed HoldID to String as Firebase keys are strings
    HoldID = db.Column(db.String(50), primary_key=True)
    reason = db.Column(db.String(255))
    holdDate = db.Column(db.Date, default=datetime.utcnow)
    liftDate = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(50), default='Active')
    StudentID = db.Column(db.String(50), db.ForeignKey('Student.StudentID'), nullable=False)

    student = db.relationship('Student', back_populates='holds')

    def __repr__(self):
        return f"<Hold {self.HoldID} for Student {self.StudentID} - Status: {self.status}>"

# --- Enrollment & Fees Entities ---

class Enrollment(db.Model):
    __tablename__ = 'Enrollment'
    EnrollmentID = db.Column(db.String(50), primary_key=True)
    EnrollmentDate = db.Column(db.Date, default=datetime.utcnow)
    StudentID = db.Column(db.String(50), db.ForeignKey('Student.StudentID'), nullable=False)
    CourseID = db.Column(db.String(50), db.ForeignKey('Course.CourseID'), nullable=False)

    # Relationships
    student = db.relationship('Student', back_populates='enrollments')
    course = db.relationship('Course', back_populates='enrollments')

    def __repr__(self):
        return f"<Enrollment {self.EnrollmentID} Student:{self.StudentID} Course:{self.CourseID}>"

class CourseFee(db.Model):
    __tablename__ = 'Course_Fees'
    # Changed FeeID to String to align with generated IDs like FEE00001
    FeeID = db.Column(db.String(50), primary_key=True)
    amount = db.Column(db.Double, nullable=False)
    description = db.Column(db.String(255))
    CourseID = db.Column(db.String(50), db.ForeignKey('Course.CourseID'), nullable=False)

    # Relationships
    course = db.relationship('Course', back_populates='course_fees')
    student_course_fees = db.relationship('StudentCourseFee', back_populates='course_fee', lazy=True)

    def __repr__(self):
        return f"<CourseFee {self.FeeID} Amount:{self.amount} Course:{self.CourseID}>"

class StudentCourseFee(db.Model):
    __tablename__ = 'Student_Course_Fees'
    # Changed StudentCourseFeeID to String to align with generated IDs like SCF00001
    StudentCourseFeeID = db.Column(db.String(50), primary_key=True)
    due_date = db.Column(db.Date)
    paid_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(50), default='Outstanding')
    StudentID = db.Column(db.String(50), db.ForeignKey('Student.StudentID'), nullable=False)
    CourseID = db.Column(db.String(50), db.ForeignKey('Course.CourseID'), nullable=False)
    # Changed FeeID to String to match CourseFee.FeeID
    FeeID = db.Column(db.String(50), db.ForeignKey('Course_Fees.FeeID'), nullable=True)

    # Relationships
    student = db.relationship('Student', back_populates='student_course_fees')
    course = db.relationship('Course', back_populates='student_course_fees')
    course_fee = db.relationship('CourseFee', back_populates='student_course_fees')

    def __repr__(self):
        return f"<StudentCourseFee {self.StudentCourseFeeID} Student:{self.StudentID} Course:{self.CourseID} Status:{self.status}>"