from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(20), primary_key=True)  # Student ID
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Profile relationship
    profile = db.relationship('Profile', backref='user', uselist=False)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Profile(db.Model):
    __tablename__ = 'profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey('users.id'), nullable=False)
    first_name = db.Column(db.String(50))
    middle_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    dob = db.Column(db.Date)
    gender = db.Column(db.String(20))
    citizenship = db.Column(db.String(50))
    program = db.Column(db.String(100))
    student_level = db.Column(db.String(50))
    student_campus = db.Column(db.String(100))
    profile_pic_url = db.Column(db.String(200))
    
    # Address relationship
    address = db.relationship('Address', backref='profile', uselist=False)
    
    # Passport/Visa relationship
    passport_visa = db.relationship('PassportVisa', backref='profile', uselist=False)
    
    def __repr__(self):
        return f'<Profile {self.first_name} {self.last_name}>'

class Address(db.Model):
    __tablename__ = 'addresses'
    
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id'), nullable=False)
    street = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    
    def __repr__(self):
        return f'<Address {self.street}, {self.city}>'

class PassportVisa(db.Model):
    __tablename__ = 'passport_visas'
    
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id'), nullable=False)
    passport_number = db.Column(db.String(50))
    visa_status = db.Column(db.String(50))
    expiry_date = db.Column(db.Date)
    
    def __repr__(self):
        return f'<PassportVisa {self.passport_number}>'

# NOTE: Ensure db is initialized in __init__.py for this to work.