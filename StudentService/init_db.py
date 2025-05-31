# StudentService/init_db.py

from flask import Flask
from app.API.config import Config
from app.Core.model import db, User
import os

def init_db():
    # Initialize Flask app
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize database
    db.init_app(app)

    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if we already have any users
        if User.query.count() == 0:
            # Create a test user
            test_user = User(
                id='S12345678',
                username='test_student',
                email='s12345678@student.usp.ac.fj',
                role='student'
            )
            test_user.set_password('password123')
            db.session.add(test_user)
            db.session.commit()
            print("Created test user:")
            print(f"Email: {test_user.email}")
            print(f"Password: password123")
        else:
            print("Database already contains users. Skipping test user creation.")

if __name__ == '__main__':
    init_db()
