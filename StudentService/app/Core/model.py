# app/Core/model.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

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

class UserPhoto(db.Model):
    __tablename__ = 'user_photos'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.String(20),
                             db.ForeignKey('users.id', ondelete='CASCADE'),
                             nullable=False)
    filename    = db.Column(db.String(256), nullable=False)
    mime_type   = db.Column(db.String(64), nullable=False)
    data        = db.Column(db.LargeBinary, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('photos', lazy='dynamic'))
