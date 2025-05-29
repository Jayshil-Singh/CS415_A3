# init_db.py

from run_ss import app           # ← your Flask() instance from run_ss.py
from app.Core.model import db, User

def init_db():
    """Create tables (users, login_attempts, user_photos) and seed one test user."""
    with app.app_context():
        db.create_all()

        if not User.query.first():
            u = User(
                id='s12345678',
                username='student1',
                email='s12345678@student.usp.ac.fj',
                role='student'
            )
            u.set_password('student123')
            db.session.add(u)
            db.session.commit()
            print("Seeded default student: s12345678 / student123")
        else:
            print("Users already exist in the database.")

if __name__ == "__main__":
    init_db()
