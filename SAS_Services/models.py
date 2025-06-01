from flask_sqlalchemy import SQLAlchemy
import enum
from datetime import datetime

# Define the SQLAlchemy instance HERE
# This 'db' instance will be imported by app.py and init_dp.py
db = SQLAlchemy()

# --- Enums ---
class GenderEnum(enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class StudentLevelEnum(enum.Enum):
    CERTIFICATE = "Certificate"
    DIPLOMA = "Diploma"
    BACHELOR = "Bachelor"
    POSTGRAD_CERT = "Postgraduate Certificate"
    POSTGRAD_DIP = "Postgraduate Diploma"
    MASTER = "Master"
    DOCTORATE = "Doctorate"

# --- New Lookup Table: Campus ---
class Campus(db.Model):
    __tablename__ = 'Campus'
    CampusID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    CampusName = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f'<Campus {self.CampusID} {self.CampusName}>'
    
# --- NEW Lookup Table: SubProgram ---
class SubProgram(db.Model):
    __tablename__ = 'SubProgram'
    SubProgramID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SubProgramName = db.Column(db.String(200), unique=True, nullable=False)
    # You could add a ForeignKey to Program if subprograms are always tied to a specific main program
    # ProgramID = db.Column(db.Integer, db.ForeignKey('Program.ProgramID'), nullable=True)
    # program = db.relationship('Program', backref=db.backref('sub_programs', lazy=True))


    def __repr__(self):
        return f'<SubProgram {self.SubProgramID} {self.SubProgramName}>'
    
# This table creates a many-to-many relationship between Student and SubProgram
student_subprogram_association = db.Table('Student_SubProgram',
    db.Column('spstID', db.Integer, primary_key=True, autoincrement=True), # Explicit PK for the association table itself
    db.Column('StudentID', db.String(9), db.ForeignKey('Student.StudentID'), nullable=False),
    db.Column('SubProgramID', db.Integer, db.ForeignKey('SubProgram.SubProgramID'), nullable=False),
    db.UniqueConstraint('StudentID', 'SubProgramID', name='_student_subprogram_uc') # Student takes a subprogram once
)

# --- New Lookup Table: ProgramType ---
class ProgramType(db.Model):
    __tablename__ = 'ProgramType'
    ProgramTypeID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ProgramTypeName = db.Column(db.String(100), unique=True, nullable=False) # e.g., "Single Major", "Double Major"
    Description = db.Column(db.String(255), nullable=True) # Optional: "Requires 1 subprogram"

    def __repr__(self):
        return f'<ProgramType {self.ProgramTypeID} {self.ProgramTypeName}>'

# --- Student Table (Modified) ---
class Student(db.Model):
    __tablename__ = 'Student'
    StudentID = db.Column(db.String(9), primary_key=True)
    FirstName = db.Column(db.String(100), nullable=False)
    MiddleName = db.Column(db.String(100), nullable=True)
    LastName = db.Column(db.String(100), nullable=False)
    Contact = db.Column(db.String(20), nullable=False)
    Email = db.Column(db.String(120), unique=True, nullable=False)
    DateOfBirth = db.Column(db.Date, nullable=False)
    Gender = db.Column(db.Enum(GenderEnum), nullable=False)
    Citizenship = db.Column(db.String(100), nullable=False)
    Address = db.Column(db.String(255), nullable=False)
    PasswordHash = db.Column(db.String(128), nullable=False)
    CampusID = db.Column(db.Integer, db.ForeignKey('Campus.CampusID'), nullable=True)
    
    # New passport and visa fields
    PassportNumber = db.Column(db.String(20), nullable=True)
    VisaStatus = db.Column(db.String(50), nullable=True)
    VisaExpiryDate = db.Column(db.Date, nullable=True)
    
    campus = db.relationship('Campus', backref=db.backref('students', lazy='select'))
    student_programs = db.relationship('Student_Program', back_populates='student', cascade="all, delete-orphan")
    student_levels = db.relationship('Student_Level', back_populates='student', cascade="all, delete-orphan")

    # New many-to-many relationship with SubProgram
    enrolled_subprograms = db.relationship(
        'SubProgram',
        secondary=student_subprogram_association,
        backref=db.backref('students_enrolled', lazy='dynamic'), # 'dynamic' allows further querying
        lazy='select' # Or 'dynamic' if you prefer
    )

    def __repr__(self):
        return f'<Student {self.StudentID} {self.FirstName} {self.LastName}>'

# --- Program Table ---
class Program(db.Model):
    __tablename__ = 'Program'
    ProgramID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ProgramName = db.Column(db.String(200), unique=True, nullable=False)
    # Add other program details like faculty, duration, etc.

    # Relationship
    student_programs = db.relationship('Student_Program', back_populates='program')

    def __repr__(self):
        return f'<Program {self.ProgramID} {self.ProgramName}>'

# --- Student_Program Table (Modified) ---
class Student_Program(db.Model):
    __tablename__ = 'Student_Program'
    StprID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    StudentID = db.Column(db.String(9), db.ForeignKey('Student.StudentID'), nullable=False)
    ProgramID = db.Column(db.Integer, db.ForeignKey('Program.ProgramID'), nullable=False)

    # New: Link to ProgramType
    ProgramTypeID = db.Column(db.Integer, db.ForeignKey('ProgramType.ProgramTypeID'), nullable=True)
    program_type = db.relationship('ProgramType', backref=db.backref('student_program_enrollments', lazy=True))

    student = db.relationship('Student', back_populates='student_programs')
    program = db.relationship('Program', back_populates='student_programs')
    __table_args__ = (db.UniqueConstraint('StudentID', 'ProgramID', name='_student_program_uc'),)

    def __repr__(self):
        return f'<Student_Program StprID={self.StprID} Student={self.StudentID} Program={self.ProgramID} TypeID={self.ProgramTypeID}>'

# --- Student_Level Table ---
class Student_Level(db.Model):
    __tablename__ = 'Student_Level'
    StudentLevelID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    StudentID = db.Column(db.String(9), db.ForeignKey('Student.StudentID'), nullable=False)
    StudentLevel = db.Column(db.Enum(StudentLevelEnum), nullable=False)
    # You might add effective_date or academic_year if level changes over time

    # Relationship
    student = db.relationship('Student', back_populates='student_levels')

    def __repr__(self):
        return f'<Student_Level ID={self.StudentLevelID} Student={self.StudentID} Level={self.StudentLevel.value}>'

# Document Models
class BirthCertificate(db.Model):
    __tablename__ = 'BirthCertificate'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), db.ForeignKey('Student.StudentID'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    verified = db.Column(db.Boolean, default=False)
    
    student = db.relationship('Student', backref=db.backref('birth_certificate', uselist=False))

class ValidID(db.Model):
    __tablename__ = 'ValidID'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), db.ForeignKey('Student.StudentID'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    verified = db.Column(db.Boolean, default=False)
    id_type = db.Column(db.String(50), nullable=False)
    
    student = db.relationship('Student', backref=db.backref('valid_id', uselist=False))

class AcademicTranscript(db.Model):
    __tablename__ = 'AcademicTranscript'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), db.ForeignKey('Student.StudentID'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    verified = db.Column(db.Boolean, default=False)
    year_level = db.Column(db.String(20), nullable=False)
    
    student = db.relationship('Student', backref=db.backref('academic_transcript', uselist=False))

class Addressing_Student(db.Model):
    __tablename__ = 'Addressing_Student'

    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    StudentID = db.Column(db.String(20), db.ForeignKey('Student.StudentID', ondelete='CASCADE'), nullable=False)
    Province = db.Column(db.String(100), nullable=False)
    Country = db.Column(db.String(100), nullable=False)
    ZipCode = db.Column(db.String(20))

    # Relationship with Student
    student = db.relationship('Student', backref=db.backref('address_info', uselist=False))

    def to_dict(self):
        """Convert the model instance to a dictionary."""
        return {
            'ID': self.ID,
            'StudentID': self.StudentID,
            'Province': self.Province,
            'Country': self.Country,
            'ZipCode': self.ZipCode
        }

    def __repr__(self):
        return f'<Addressing_Student ID={self.ID} StudentID={self.StudentID}>'

# --- Student Related Models ---

class Emergency_Contact(db.Model):
    __tablename__ = 'Emergency_Contact'
    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    StudentID = db.Column(db.String(20), db.ForeignKey('Student.StudentID', ondelete='CASCADE'), nullable=False)
    FirstName = db.Column(db.String(100), nullable=False)
    MiddleName = db.Column(db.String(100))
    LastName = db.Column(db.String(100), nullable=False)
    Relationship = db.Column(db.String(50), nullable=False)
    ContactPhone = db.Column(db.String(20), nullable=False)

    # Relationship with Student
    student = db.relationship('Student', backref=db.backref('emergency_contact', uselist=False))

    def __repr__(self):
        return f'<Emergency Contact {self.FirstName} {self.LastName} for Student {self.StudentID}>'
