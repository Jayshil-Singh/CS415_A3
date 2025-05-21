# seed_db.py
import os
from dotenv import load_dotenv
from run_es import create_app # Import your app factory
from enrollment_services.db import db
from enrollment_services.model import User # Import the new User model

# Load environment variables (needed for SECRET_KEY if create_app uses it)
load_dotenv()

def seed_users():
    """
    Initializes the database and adds sample users.
    Run this script once to populate your database with test users.
    """
    app = create_app()
    with app.app_context():
        # Ensure all tables are created, including the new 'users' table
        db.create_all()

        # Check if we already have users to avoid re-seeding
        if User.query.first() is not None:
            print("Users already exist in the database. Skipping seeding.")
            return

        # Sample users with their passwords
        users_to_add = [
            {
                'id': 's12345678',
                'username': 'student1',
                'email': 's12345678@student.usp.ac.fj',
                'password': 'student123', # This will be hashed
                'role': 'student'
            },
            {
                'id': 'm12345',
                'username': 'manager1',
                'email': 'manager1@usp.ac.fj',
                'password': 'manager123', # This will be hashed
                'role': 'sas_manager'
            },
            {
                'id': 'a12345',
                'username': 'admin1',
                'email': 'admin1@usp.ac.fj',
                'password': 'admin123', # This will be hashed
                'role': 'admin'
            }
        ]

        for user_data in users_to_add:
            user = User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role']
            )
            user.set_password(user_data['password']) # Hash the password
            db.session.add(user)

        db.session.commit()
        print("Database seeded successfully with sample users.")

if __name__ == '__main__':
    seed_users()