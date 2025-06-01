import os
from app import app, db
from models import *

def setup_database():
    # Create instance directory if it doesn't exist
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
        print(f"Created instance directory at {instance_path}")

    # Create uploads directory
    uploads_path = os.path.join(instance_path, 'uploads')
    if not os.path.exists(uploads_path):
        os.makedirs(uploads_path)
        print(f"Created uploads directory at {uploads_path}")

    # Create database
    with app.app_context():
        db.create_all()
        print("Created database tables")

if __name__ == '__main__':
    setup_database() 