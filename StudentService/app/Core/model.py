# StudentService/app/Core/model.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# single shared db handle
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.String(20), primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(20), nullable=False)  # 'student','sas_manager','admin'
    is_active     = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    last_login    = db.Column(db.DateTime)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

class LoginAttempt(db.Model):
    __tablename__ = 'login_attempts'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.String(20), db.ForeignKey('users.id'))
    timestamp  = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    success    = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref='login_attempts')

class Student(db.Model):
    __tablename__ = 'Student'
    StudentID = db.Column(db.String(20), primary_key=True)
    FirstName = db.Column(db.String(50), nullable=False)
    MiddleName = db.Column(db.String(50))
    LastName = db.Column(db.String(50), nullable=False)
    Contact = db.Column(db.String(20))
    Email = db.Column(db.String(120), unique=True, nullable=False)
    Password = db.Column(db.String(100), nullable=False)
    DateOfBirth = db.Column(db.Date)
    Gender = db.Column(db.String(10))
    Citizenship = db.Column(db.String(50))
    Address = db.Column(db.String(200))
    CampusID = db.Column(db.String(20))
