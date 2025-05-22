from main_app_packages import create_app, db
from main_app_packages.models import User, Profile, Address, PassportVisa
from datetime import date

def init_db():
    app = create_app()
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if we already have data
        if User.query.first() is not None:
            print("Database already initialized")
            return
        
        # Create sample user
        user = User(
            id='s12345678',
            username='jane.doe',
            email='s12345678@student.usp.ac.fj',
            password_hash='dummy_hash'  # In production, use proper password hashing
        )
        db.session.add(user)
        
        # Create profile
        profile = Profile(
            user_id='s12345678',
            first_name='Jane',
            middle_name='',
            last_name='Doe',
            dob=date(2003, 5, 15),
            gender='Female',
            citizenship='Fijian',
            program='Bachelor of Science',
            student_level='Undergraduate',
            student_campus='Laucala Campus, Suva, Fiji',
            profile_pic_url='https://example.com/profile.jpg'
        )
        db.session.add(profile)
        
        # Create address
        address = Address(
            profile=profile,
            street='123 University Way',
            city='Suva',
            state='Central',
            country='Fiji',
            postal_code='0000'
        )
        db.session.add(address)
        
        # Create passport/visa info
        passport_visa = PassportVisa(
            profile=profile,
            passport_number='P123456',
            visa_status='Student Visa',
            expiry_date=date(2026, 12, 31)
        )
        db.session.add(passport_visa)
        
        # Commit all changes
        db.session.commit()
        print("Database initialized with sample data")

if __name__ == '__main__':
    init_db() 