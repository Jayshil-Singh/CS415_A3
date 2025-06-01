# enrollment_services/db.py
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

db = SQLAlchemy()

def init_db(app: Flask):
    """Initializes the SQLAlchemy database with the Flask app."""
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///enrollment.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    with app.app_context():
        db.create_all() # Create tables if they don't exist
    print("Database initialized successfully.")