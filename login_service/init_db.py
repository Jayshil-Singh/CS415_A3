from login_service_packages import create_app, db
from login_service_packages.models import User

def init_db():
    app = create_app()
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if we already have data
        if User.query.first() is not None:
            print("Database already initialized")
            return
        
        # Create sample users
        users = [
            {
                'id': 's12345678',
                'username': 'student1',
                'email': 's12345678@student.usp.ac.fj',
                'password': 'student123',
                'role': 'student'
            },
            {
                'id': 'm12345',
                'username': 'manager1',
                'email': 'manager1@usp.ac.fj',
                'password': 'manager123',
                'role': 'sas_manager'
            },
            {
                'id': 'a12345',
                'username': 'admin1',
                'email': 'admin1@usp.ac.fj',
                'password': 'admin123',
                'role': 'admin'
            }
        ]
        
        for user_data in users:
            user = User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role']
            )
            user.set_password(user_data['password'])
            db.session.add(user)
        
        # Commit all changes
        db.session.commit()
        print("Database initialized with sample users")

if __name__ == '__main__':
    init_db() 