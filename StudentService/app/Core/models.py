# File: StudentService/app/Core/models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum

db = SQLAlchemy()

class StudentLevelEnum(Enum):
    UNDERGRADUATE = 'Undergraduate'
    POSTGRADUATE = 'Postgraduate'
    DOCTORATE = 'Doctorate'

class GenderEnum(Enum):
    MALE = 'Male'
    FEMALE = 'Female'
    OTHER = 'Other'

# -----------------------------------------------------------------------------
# 1) User Model (authentication)
# -----------------------------------------------------------------------------
class User(db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.String(20), primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(20), nullable=False)   # 'student','sas_manager','admin'
    is_active     = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    last_login    = db.Column(db.DateTime)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)


# -----------------------------------------------------------------------------
# 2) LoginAttempt Model
# -----------------------------------------------------------------------------
class LoginAttempt(db.Model):
    __tablename__ = 'login_attempts'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.String(20), db.ForeignKey('users.id'))
    timestamp  = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    success    = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref='login_attempts')


# -----------------------------------------------------------------------------
# 3) Student Model (Yash's schema)
# -----------------------------------------------------------------------------
class Student(db.Model):
    __tablename__ = 'Student'

    StudentID    = db.Column(db.String(20), primary_key=True)
    FirstName    = db.Column(db.String(50), nullable=False)
    MiddleName   = db.Column(db.String(50))
    LastName     = db.Column(db.String(50), nullable=False)
    Contact      = db.Column(db.String(20))
    Email        = db.Column(db.String(120), unique=True, nullable=False)
    DateOfBirth  = db.Column(db.Date)
    Gender       = db.Column(db.Enum(GenderEnum))
    Citizenship  = db.Column(db.String(50))
    Address      = db.Column(db.String(200))
    CampusID     = db.Column(db.String(20), db.ForeignKey('Campus.CampusID'))
    PasswordHash = db.Column(db.String(128))
    PassportNumber = db.Column(db.String(20))
    VisaStatus = db.Column(db.String(50))
    VisaExpiryDate = db.Column(db.Date)

    # Add password-related methods
    def set_password(self, password):
        """Set the password hash for the student."""
        self.PasswordHash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the hash."""
        if self.PasswordHash is None:
            return False
        return check_password_hash(self.PasswordHash, password)

    # Relationship with Program through Program_Student table
    programs = db.relationship('Program', secondary='Program_Student', backref='students')
    
    # Relationship with Campus
    campus = db.relationship('Campus', backref='students')

class Campus(db.Model):
    __tablename__ = 'Campus'
    
    CampusID = db.Column(db.String(20), primary_key=True)
    CampusName = db.Column(db.String(100), nullable=False)
    Location = db.Column(db.String(200))

class StudentLevel(db.Model):
    __tablename__ = 'StudentLevel'
    
    ID = db.Column(db.Integer, primary_key=True)
    StudentID = db.Column(db.String(20), db.ForeignKey('Student.StudentID'), nullable=False)
    Level = db.Column(db.Enum(StudentLevelEnum), nullable=False)
    StartDate = db.Column(db.Date)
    EndDate = db.Column(db.Date)
    
    student = db.relationship('Student', backref=db.backref('level', uselist=False))

class ProgramType(db.Model):
    __tablename__ = 'ProgramType'
    
    ProgramTypeID = db.Column(db.String(20), primary_key=True)
    ProgramTypeName = db.Column(db.String(100), nullable=False)

class SubProgram(db.Model):
    __tablename__ = 'SubProgram'
    
    SubProgramID = db.Column(db.String(20), primary_key=True)
    SubProgramName = db.Column(db.String(100), nullable=False)
    ProgramID = db.Column(db.String(20), db.ForeignKey('Program.ProgramID'))

# Association table for Student-SubProgram many-to-many relationship
student_subprogram_association = db.Table('student_subprogram_association',
    db.Column('StudentID', db.String(20), db.ForeignKey('Student.StudentID'), primary_key=True),
    db.Column('SubProgramID', db.String(20), db.ForeignKey('SubProgram.SubProgramID'), primary_key=True)
)


# -----------------------------------------------------------------------------
# 4) UserPhoto Model (linked to Student.StudentID)
# -----------------------------------------------------------------------------
class UserPhoto(db.Model):
    __tablename__ = 'user_photos'

    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # This foreign key *does* exist in user_photos → Student(StudentID):
    student_id  = db.Column(
                    db.String(20),
                    db.ForeignKey('Student.StudentID', ondelete='CASCADE'),
                    nullable=False
                  )

    filename    = db.Column(db.String(256), nullable=False)
    mime_type   = db.Column(db.String(64), nullable=False)
    data        = db.Column(db.LargeBinary, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # We *can* keep this relationship to Student,
    # because student_id → Student.StudentID does exist:
    student = db.relationship('Student', backref=db.backref('photos', lazy='dynamic'))

    # Note: we removed `user = db.relationship('User', back_populates='photos')`
    # because user_photos.student_id does not reference users.id directly.


# Program model
class Program(db.Model):
    __tablename__ = 'Program'
    
    ProgramID = db.Column(db.String(20), primary_key=True)
    ProgramName = db.Column(db.String(100), nullable=False)


# Program_Student association table
class Program_Student(db.Model):
    __tablename__ = 'Program_Student'
    
    ProgramID = db.Column(db.String(20), db.ForeignKey('Program.ProgramID'), primary_key=True)
    StudentID = db.Column(db.String(20), db.ForeignKey('Student.StudentID'), primary_key=True)


# Add after the existing models

class BirthCertificate(db.Model):
    __tablename__ = 'BirthCertificate'
    DocumentID = db.Column(db.Integer, primary_key=True)
    StudentID = db.Column(db.String(20), db.ForeignKey('Student.StudentID'), nullable=False)
    FileName = db.Column(db.String(255), nullable=False)
    FilePath = db.Column(db.String(512), nullable=False)
    UploadDate = db.Column(db.DateTime, default=datetime.utcnow)
    VerificationStatus = db.Column(db.String(20), default='Pending')
    
    student = db.relationship('Student', backref=db.backref('birth_certificate', uselist=False))

class ValidID(db.Model):
    __tablename__ = 'ValidID'
    DocumentID = db.Column(db.Integer, primary_key=True)
    StudentID = db.Column(db.String(20), db.ForeignKey('Student.StudentID'), nullable=False)
    FileName = db.Column(db.String(255), nullable=False)
    FilePath = db.Column(db.String(512), nullable=False)
    UploadDate = db.Column(db.DateTime, default=datetime.utcnow)
    VerificationStatus = db.Column(db.String(20), default='Pending')
    IDType = db.Column(db.String(50), nullable=False)
    
    student = db.relationship('Student', backref=db.backref('valid_id', uselist=False))

class AcademicTranscript(db.Model):
    __tablename__ = 'AcademicTranscript'
    DocumentID = db.Column(db.Integer, primary_key=True)
    StudentID = db.Column(db.String(20), db.ForeignKey('Student.StudentID'), nullable=False)
    FileName = db.Column(db.String(255), nullable=False)
    FilePath = db.Column(db.String(512), nullable=False)
    UploadDate = db.Column(db.DateTime, default=datetime.utcnow)
    VerificationStatus = db.Column(db.String(20), default='Pending')
    TranscriptType = db.Column(db.String(20), nullable=False)
    
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

    def to_dict(self):
        """Convert the model instance to a dictionary."""
        return {
            'ID': self.ID,
            'StudentID': self.StudentID,
            'FirstName': self.FirstName,
            'MiddleName': self.MiddleName,
            'LastName': self.LastName,
            'Relationship': self.Relationship,
            'ContactPhone': self.ContactPhone
        }

    def __repr__(self):
        return f'<Emergency_Contact ID={self.ID} StudentID={self.StudentID}>'
