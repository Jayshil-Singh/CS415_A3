# File: StudentService/init_db.py

from flask import Flask
from app.API.config import Config
from app.Core.models import db, User
import os

def init_db():
    """
    Create any missing tables and, if the 'users' table is empty, insert one test user.
    We do NOT seed any Student rows here (since your studentservice.db already
    contains actual registered students).
    """
    # --- Initialize a minimal Flask app just to pull in your config ---
    app = Flask(__name__)
    app.config.from_object(Config)

    # --- Hook up SQLAlchemy with this app ---
    db.init_app(app)

    with app.app_context():
        # 1) Create all tables that do not yet exist:
        db.create_all()

        # 2) If the 'users' table has zero rows, insert one test user:
        if User.query.count() == 0:
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
            print(f"  Email:    {test_user.email}")
            print(f"  Password: password123")
        else:
            print("Database already contains users. Skipping test user creation.")

if __name__ == '__main__':
    init_db()
