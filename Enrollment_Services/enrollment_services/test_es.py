# tests/test_enrollment_services.py
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import your Flask app creation function and db instance
from enrollment_services import create_app, db # Import db directly from __init__.py
from enrollment_services.model import (
    User, Student, Course, Enrollment, Hold,
    Grade, GradeRecheck, SpecialApplication, ServiceAccess,
    Program, SubProgram, Semester, CourseAvailability, CourseFee
)

# --- Pytest Fixtures ---

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Use an in-memory SQLite database for testing
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})

    with app.app_context():
        # db.create_all() is now handled within create_app and is idempotent.
        # No need to call db.init_app(app) or db.create_all() explicitly here anymore
        # as create_app takes care of it for the app instance it returns.
        yield app
        db.session.remove() # Clean up session
        db.drop_all() # Drop tables after test

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's commands."""
    return app.test_cli_runner()

@pytest.fixture
def auth_mock_student():
    """
    Fixture to mock the @token_required decorator for a student user.
    This bypasses actual JWT validation for testing.
    """
    mock_student = MagicMock(spec=User)
    mock_student.id = 'test_student_id_123'
    mock_student.username = 'teststudent'
    mock_student.role = 'student'
    mock_student.FirstName = 'Test'
    mock_student.LastName = 'Student'
    
    # Patch the token_required decorator
    # It should take the original function and return a decorated version
    with patch('enrollment_services.routes.token_required', 
               side_effect=lambda f: lambda *args, **kwargs: f(mock_student, *args, **kwargs)):
        yield mock_student

@pytest.fixture
def auth_mock_admin():
    """
    Fixture to mock the @token_required decorator for an admin user.
    """
    mock_admin = MagicMock(spec=User)
    mock_admin.id = 'test_admin_id_456'
    mock_admin.username = 'testadmin'
    mock_admin.role = 'admin'
    mock_admin.FirstName = 'Test'
    mock_admin.LastName = 'Admin'

    with patch('enrollment_services.routes.token_required', 
               side_effect=lambda f: lambda *args, **kwargs: f(mock_admin, *args, **kwargs)):
        yield mock_admin

@pytest.fixture
def setup_test_data(app, auth_mock_student): # Added auth_mock_student to ensure student exists
    """Populate the database with dummy data for tests."""
    with app.app_context():
        # Create a dummy student user
        student_user = User(id='test_student_id_123', username='teststudent', 
                            password_hash='dummy_hash', role='student', email='test@example.com')
        db.session.add(student_user)
        db.session.commit() # Commit to make user available for student profile

        # Create a dummy student profile
        student_profile = Student(
            StudentID='test_student_id_123',
            FirstName='Test',
            MiddleName='M',
            LastName='Student',
            DateOfBirth=datetime(2000, 1, 1).date(),
            Gender='M',
            Address='123 Test St',
            Contact='1234567',
            Citizenship='Fiji',
            CampusID='SUVA',
            ProgramID='BSC',
            SubProgramID='CS',
            StudentLevelID='UG',
            Email='teststudent@example.com'
        )
        db.session.add(student_profile)
        db.session.commit() # Commit to make student profile available

        # Create Programs and SubPrograms
        program_bsc = Program(ProgramID='BSC', ProgramName='Bachelor of Science')
        subprogram_cs = SubProgram(SubProgramID='CS', SubProgramName='Computer Science', SubProgramType='Major', ProgramID='BSC')
        db.session.add_all([program_bsc, subprogram_cs])
        db.session.commit()

        # Create some dummy courses relevant to PROGRAM_STRUCTURE in routes.py
        course_cs111 = Course(CourseID='CS111', CourseName='Introduction to C++ Programming', SubProgramID='CS', PrerequisiteCourseID=None, credit_hours=1.0)
        course_cs112 = Course(CourseID='CS112', CourseName='Data Structures and Algorithms', SubProgramID='CS', PrerequisiteCourseID='CS111', credit_hours=1.0)
        course_ma111 = Course(CourseID='MA111', CourseName='Calculus and Linear Algebra', SubProgramID='MA', PrerequisiteCourseID=None, credit_hours=1.0)
        course_cs201 = Course(CourseID='CS201', CourseName='Data Structures', SubProgramID='CS', PrerequisiteCourseID='CS101', credit_hours=1.0) # Prereq different for testing
        course_cs211 = Course(CourseID='CS211', CourseName='Object-Oriented Programming', SubProgramID='CS', PrerequisiteCourseID='CS112', credit_hours=1.0) # Year 2 course, prereq CS112
        course_uu100a = Course(CourseID='UU100A', CourseName='Communications and Information Literacy', SubProgramID='UU', PrerequisiteCourseID=None, credit_hours=0.5)
        course_uu114 = Course(CourseID='UU114', CourseName='English for Academic Purposes', SubProgramID='UU', PrerequisiteCourseID=None, credit_hours=1.0)
        course_cs001 = Course(CourseID='CS001', CourseName='Industrial Attachment (Part 1)', SubProgramID='CS', PrerequisiteCourseID=None, credit_hours=0.5)
        
        db.session.add_all([course_cs111, course_cs112, course_ma111, course_cs201, course_cs211, course_uu100a, course_uu114, course_cs001])
        db.session.commit()

        # Create dummy semesters
        semester_s1_2025 = Semester(SemesterID='S1_2025', SemesterName='Semester 1, 2025')
        semester_s2_2025 = Semester(SemesterID='S2_2025', SemesterName='Semester 2, 2025')
        db.session.add_all([semester_s1_2025, semester_s2_2025])
        db.session.commit()

        # Create course availabilities
        course_avail_cs111 = CourseAvailability(CourseID='CS111', SemesterID='S1_2025', isAvailable=True)
        course_avail_cs112 = CourseAvailability(CourseID='CS112', SemesterID='S2_2025', isAvailable=True)
        course_avail_ma111 = CourseAvailability(CourseID='MA111', SemesterID='S1_2025', isAvailable=True)
        course_avail_uu100a = CourseAvailability(CourseID='UU100A', SemesterID='S1_2025', isAvailable=True)
        course_avail_uu114 = CourseAvailability(CourseID='UU114', SemesterID='S1_2025', isAvailable=True)
        course_avail_cs211 = CourseAvailability(CourseID='CS211', SemesterID='S1_2025', isAvailable=True) # For Year 2
        course_avail_cs001 = CourseAvailability(CourseID='CS001', SemesterID='S1_2025', isAvailable=True)
        db.session.add_all([course_avail_cs111, course_avail_cs112, course_avail_ma111, course_avail_uu100a, course_avail_uu114, course_avail_cs211, course_avail_cs001])
        db.session.commit()

        # Create a dummy grade for prereq testing (CS111 for CS112)
        grade_cs111 = Grade(
            student_id=auth_mock_student.id,
            course_id='CS111',
            letter_grade='A',
            numerical_grade=90,
            year=2024,
            semester='Semester 1'
        )
        db.session.add(grade_cs111)
        db.session.commit()

        # Create service access records for hold restrictions
        service_reg = ServiceAccess(service_name='course_registration', is_available_on_hold=False)
        service_grades = ServiceAccess(service_name='view_course_grades', is_available_on_hold=False)
        service_recheck = ServiceAccess(service_name='apply_grade_recheck', is_available_on_hold=True)
        service_special_app = ServiceAccess(service_name='apply_special_application', is_available_on_hold=True) # Renamed from apply_graduation
        db.session.add_all([service_reg, service_grades, service_recheck, service_special_app])
        db.session.commit()

        # Add a course fee
        course_fee_cs111 = CourseFee(CourseID='CS111', amount=150.00, description='Course Fee')
        db.session.add(course_fee_cs111)
        db.session.commit()


        yield # Yield control to the test
        # Teardown (handled by app fixture db.drop_all())

# --- Test Cases ---

# Dashboard Tests
def test_dashboard_get(client, auth_mock_student, setup_test_data):
    """Test that the dashboard page loads for an authenticated student."""
    response = client.get('/enrollment_services/dashboard')
    assert response.status_code == 200
    assert b"Welcome to the Enrollment Services Dashboard" in response.data
    assert b"Hi, Test" in response.data # Check for dynamic greeting

def test_dashboard_get_unauthorized_role(client, auth_mock_admin, setup_test_data):
    """Test that dashboard redirects unauthorized roles."""
    response = client.get('/enrollment_services/dashboard', follow_redirects=True)
    assert response.status_code == 200 # Should redirect to login page
    assert b"Authentication required to access this page." in response.data
    assert b"Login to Your Account" in response.data # Assuming login page title

# Enrollment Tests
def test_enroll_get(client, auth_mock_student, setup_test_data):
    """Test that the enrollment page loads."""
    response = client.get('/enrollment_services/enroll')
    assert response.status_code == 200
    assert b"Course Enrollment" in response.data
    assert b"CS111 - Introduction to C++ Programming" in response.data # Check for a dummy course

def test_enroll_post_success(client, auth_mock_student, setup_test_data):
    """Test successful course enrollment with met prerequisites."""
    # CS111 is already graded in setup_test_data, so CS112 (prereq CS111) should be enrollable
    response = client.post('/enrollment_services/enroll', data={
        'courses': ['CS112', 'MA111']
    }, follow_redirects=True) # follow_redirects to check final page after enrollment
    
    assert response.status_code == 200
    assert b"Successfully enrolled in 2 new course(s)!" in response.data
    assert b"CS112" in response.data # Check if enrolled course is displayed on display_courses page
    assert b"MA111" in response.data

    # Verify in DB
    with client.application.app_context():
        enrollment_cs112 = Enrollment.query.filter_by(StudentID=auth_mock_student.id, CourseID='CS112').first()
        enrollment_ma111 = Enrollment.query.filter_by(StudentID=auth_mock_student.id, CourseID='MA111').first()
        assert enrollment_cs112 is not None
        assert enrollment_ma111 is not None

def test_enroll_post_exceed_units(client, auth_mock_student, setup_test_data):
    """Test enrollment fails when exceeding unit limit (max 4.0 units)."""
    # Assuming CS111, CS112, MA111, UU114, CS211 are all 1.0 unit courses as per PROGRAM_STRUCTURE.
    # Totaling 5.0 units which exceeds 4.0.
    response = client.post('/enrollment_services/enroll', data={
        'courses': ['CS111', 'CS112', 'MA111', 'UU114', 'CS211']
    }, follow_redirects=True)
    
    assert response.status_code == 200 # Redirects back to enroll page
    assert b"You have exceeded the maximum enrollment limit of 4 full units." in response.data

    # Verify no new enrollments were created for these specific courses
    with client.application.app_context():
        enrollments = Enrollment.query.filter(
            Enrollment.StudentID == auth_mock_student.id,
            Enrollment.CourseID.in_(['CS112', 'MA111', 'UU114', 'CS211']) # CS111 already has grade
        ).all()
        assert len(enrollments) == 0 # Should not have enrolled in any of these

def test_enroll_post_unmet_course_prerequisite(client, auth_mock_student, setup_test_data):
    """Test enrollment fails due to unmet course prerequisites."""
    # For this test, ensure the prerequisite (CS111 for CS112) is NOT met.
    with client.application.app_context():
        # Remove the CS111 grade if it exists for this test context to simulate unmet prereq
        grade_cs111 = Grade.query.filter_by(student_id=auth_mock_student.id, course_id='CS111').first()
        if grade_cs111:
            db.session.delete(grade_cs111)
            db.session.commit()
    
    # Now try to enroll in CS112 (prereq CS111)
    response = client.post('/enrollment_services/enroll', data={
        'courses': ['CS112']
    }, follow_redirects=True)

    assert response.status_code == 200 # Redirects back to enroll page
    assert b"Cannot enroll in: Data Structures and Algorithms (requires Introduction to C++ Programming) due to unmet prerequisites." in response.data
    
    # Verify no enrollment for CS112
    with client.application.app_context():
        enrollment = Enrollment.query.filter_by(StudentID=auth_mock_student.id, CourseID='CS112').first()
        assert enrollment is None

def test_enroll_post_unmet_year_prerequisite(client, auth_mock_student, setup_test_data):
    """Test enrollment fails due to unmet year prerequisites."""
    # Try to enroll in a Year 2 course (CS211) without Year 1 courses completed.
    # setup_test_data only provides CS111 grade. The PROGRAM_STRUCTURE defines Year 1 courses.
    # The logic in routes.py checks if `year_1_unique_courses.issubset(all_met_courses_for_prereq_check)`
    # So, with only CS111 met, Year 1 is not considered complete.
    
    response = client.post('/enrollment_services/enroll', data={
        'courses': ['CS211'] # CS211 is a Year 2 course
    }, follow_redirects=True)

    assert response.status_code == 200 # Redirects back to enroll page
    assert b"Cannot enroll in: Object-Oriented Programming (requires Completion of Year 1) due to unmet prerequisites." in response.data
    
    with client.application.app_context():
        enrollment = Enrollment.query.filter_by(StudentID=auth_mock_student.id, CourseID='CS211').first()
        assert enrollment is None

def test_enroll_post_on_hold_restricted_service(client, auth_mock_student, setup_test_data):
    """Test that enrollment is restricted when student has an active hold and service is not available on hold."""
    with client.application.app_context():
        # Add an active hold
        hold = Hold(
            HoldID='HOLD_ENROLL',
            StudentID=auth_mock_student.id,
            reason='Outstanding Fees',
            holdDate=datetime.utcnow().date(),
            status='Active'
        )
        db.session.add(hold)
        db.session.commit()

    response = client.post('/enrollment_services/enroll', data={
        'courses': ['MA111']
    }, follow_redirects=True) # Follow redirects to the hold status page

    assert response.status_code == 200
    assert b"You have an active hold on your account (Outstanding Fees). Course registration is currently restricted." in response.data
    assert b"Your Student Hold Status" in response.data # Check if redirected to hold status page
    
    # Verify no enrollment
    with client.application.app_context():
        enrollment = Enrollment.query.filter_by(StudentID=auth_mock_student.id, CourseID='MA111').first()
        assert enrollment is None

# Display Courses Tests
def test_display_courses_get(client, auth_mock_student, setup_test_data):
    """Test that the display courses page shows enrolled courses."""
    with client.application.app_context():
        # Manually enroll a course for this test
        enrollment = Enrollment(
            EnrollmentID='enr_test_1',
            StudentID=auth_mock_student.id,
            CourseID='CS111',
            EnrollmentDate=datetime.utcnow().date()
        )
        db.session.add(enrollment)
        db.session.commit()

    response = client.get('/enrollment_services/display_courses')
    assert response.status_code == 200
    assert b"Your Enrolled Courses" in response.data
    assert b"CS111" in response.data
    assert b"Introduction to C++ Programming" in response.data

# Drop Course Tests
def test_drop_course_success(client, auth_mock_student, setup_test_data):
    """Test successfully dropping a course."""
    with client.application.app_context():
        # Manually enroll a course to drop
        enrollment = Enrollment(
            EnrollmentID='enr_drop_test',
            StudentID=auth_mock_student.id,
            CourseID='MA111',
            EnrollmentDate=datetime.utcnow().date()
        )
        db.session.add(enrollment)
        db.session.commit()

    response = client.get('/enrollment_services/drop_course/MA111', follow_redirects=True)
    assert response.status_code == 200
    assert b"Course MA111 dropped successfully." in response.data
    assert b"MA111" not in response.data # Should no longer be on the display courses page

    # Verify in DB
    with client.application.app_context():
        enrollment_check = Enrollment.query.filter_by(StudentID=auth_mock_student.id, CourseID='MA111').first()
        assert enrollment_check is None

def test_drop_course_not_found(client, auth_mock_student, setup_test_data):
    """Test dropping a course that was not enrolled."""
    response = client.get('/enrollment_services/drop_course/NONEXISTENT', follow_redirects=True)
    assert response.status_code == 200
    assert b"Enrollment for course NONEXISTENT not found." in response.data
    # Should stay on display_courses page, or redirect there without error

# Fees Tests
def test_fees_get(client, auth_mock_student, setup_test_data):
    """Test that the fees page loads and displays correct info."""
    with client.application.app_context():
        # Manually enroll a course to see fees (CS111, which has a custom fee)
        enrollment = Enrollment(
            EnrollmentID='enr_fee_test',
            StudentID=auth_mock_student.id,
            CourseID='CS111',
            EnrollmentDate=datetime.utcnow().date()
        )
        db.session.add(enrollment)
        db.session.commit()

    response = client.get('/enrollment_services/fees')
    assert response.status_code == 200
    assert b"Invoice" in response.data
    assert b"Student Name: Test Student" in response.data
    assert b"Introduction to C++ Programming (CS111)" in response.data
    assert b"$150.00" in response.data # Check for the custom course fee
    assert b"General Services Fee" in response.data
    # Total should be 150 (CS111) + 50 (general) = 200
    assert b"Total: $200.00" in response.data
    assert b"Payment Status: Paid" in response.data # Default status is Paid unless StudentCourseFee is outstanding

def test_download_invoice_pdf(client, auth_mock_student, setup_test_data):
    """Test that the invoice PDF can be generated and downloaded."""
    with client.application.app_context():
        # Manually enroll a course for the invoice
        enrollment = Enrollment(
            EnrollmentID='enr_pdf_test',
            StudentID=auth_mock_student.id,
            CourseID='MA111',
            EnrollmentDate=datetime.utcnow().date()
        )
        db.session.add(enrollment)
        db.session.commit()

    response = client.get('/enrollment_services/download_invoice_pdf')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/pdf'
    assert 'attachment;filename=invoice_test_student_id_123' in response.headers['Content-Disposition']
    assert len(response.data) > 1000 # Check if PDF content exists

# Transcript Tests
def test_view_transcript_get_with_grades(client, auth_mock_student, setup_test_data):
    """Test that the transcript page loads and shows grades when they exist."""
    # setup_test_data already adds a grade for CS111
    response = client.get('/enrollment_services/student/view_transcript')
    assert response.status_code == 200
    assert b"Your Academic Transcript" in response.data
    assert b"CS111" in response.data
    assert b"Introduction to C++ Programming" in response.data
    assert b"Grade: A" in response.data # Check for the grade added in setup_test_data

def test_view_transcript_get_no_grades_generates_dummy(client, auth_mock_student, app):
    """Test that the transcript page generates dummy grades if none exist."""
    # Use 'app' fixture directly without 'setup_test_data' to start with an empty grades table
    with app.app_context():
        # Create user and student without grades
        student_user = User(id='test_student_id_123', username='teststudent', password_hash='dummy_hash', role='student')
        db.session.add(student_user)
        student_profile = Student(
            StudentID='test_student_id_123', FirstName='Test', LastName='Student', Email='teststudent@example.com',
            DateOfBirth=datetime(2000, 1, 1).date(), Gender='M', Address='123 Test St', Contact='1234567',
            Citizenship='Fiji', CampusID='SUVA', ProgramID='BSC', SubProgramID='CS', StudentLevelID='UG'
        )
        db.session.add(student_profile)

        # Add essential courses for dummy generation to pick up
        course_cs111 = Course(CourseID='CS111', CourseName='Introduction to C++ Programming', SubProgramID='CS', PrerequisiteCourseID=None, credit_hours=1.0)
        course_ma111 = Course(CourseID='MA111', CourseName='Calculus and Linear Algebra', SubProgramID='MA', PrerequisiteCourseID=None, credit_hours=1.0)
        db.session.add_all([course_cs111, course_ma111])

        # Add necessary ServiceAccess entries for hold checks
        service_grades = ServiceAccess(service_name='view_course_grades', is_available_on_hold=False)
        db.session.add(service_grades)

        db.session.commit()
    
    # Now make the request, which should trigger dummy grade generation
    response = client.get('/enrollment_services/student/view_transcript')
    assert response.status_code == 200
    assert b"Your Academic Transcript" in response.data
    assert b"Dummy grades generated successfully for your account!" in response.data
    
    # Verify that grades were actually created in DB
    with app.app_context():
        grades_after_request = Grade.query.filter_by(student_id='test_student_id_123').all()
        assert len(grades_after_request) > 0 # Should have some grades now

def test_view_transcript_get_on_hold_restricted(client, auth_mock_student, setup_test_data):
    """Test that viewing transcript is restricted when student has an active hold and service is not available on hold."""
    with client.application.app_context():
        # Add an active hold
        hold = Hold(
            HoldID='HOLD_TRANSCRIPT',
            StudentID=auth_mock_student.id,
            reason='Outstanding Library Fines',
            holdDate=datetime.utcnow().date(),
            status='Active'
        )
        db.session.add(hold)
        db.session.commit()

    response = client.get('/enrollment_services/student/view_transcript', follow_redirects=True)
    assert response.status_code == 200
    assert b"You have an active hold on your account (Outstanding Library Fines). Viewing your academic transcript is currently restricted." in response.data
    assert b"Your Student Hold Status" in response.data # Check if redirected to hold status page

def test_download_transcript_pdf(client, auth_mock_student, setup_test_data):
    """Test that the academic transcript PDF can be generated and downloaded."""
    response = client.get('/enrollment_services/student/download_transcript_pdf')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/pdf'
    assert 'attachment;filename=Academic_Transcript_test_student_id_123' in response.headers['Content-Disposition']
    assert len(response.data) > 1000 # Check if PDF content exists

def test_download_transcript_pdf_on_hold_restricted(client, auth_mock_student, setup_test_data):
    """Test that downloading transcript PDF is restricted when student has an active hold."""
    with client.application.app_context():
        # Add an active hold
        hold = Hold(
            HoldID='HOLD_PDF',
            StudentID=auth_mock_student.id,
            reason='Unreturned Equipment',
            holdDate=datetime.utcnow().date(),
            status='Active'
        )
        db.session.add(hold)
        db.session.commit()

    response = client.get('/enrollment_services/student/download_transcript_pdf', follow_redirects=True)
    assert response.status_code == 200
    assert b"Your academic transcript download is currently restricted due to an active hold (Unreturned Equipment)." in response.data
    assert b"Your Student Hold Status" in response.data # Check if redirected to hold status page

# Grade Recheck Tests
def test_apply_grade_recheck_get(client, auth_mock_student, setup_test_data):
    """Test that the grade recheck application page loads."""
    response = client.get('/enrollment_services/student/apply_grade_recheck')
    assert response.status_code == 200
    assert b"Apply for Grade Recheck" in response.data
    assert b"CS111 - Introduction to C++ Programming (Grade: A)" in response.data # Should show available grade

def test_apply_grade_recheck_post_success(client, auth_mock_student, setup_test_data):
    """Test successful submission of a grade recheck request."""
    with client.application.app_context():
        grade = Grade.query.filter_by(student_id=auth_mock_student.id, course_id='CS111').first()
        assert grade is not None

    response = client.post('/enrollment_services/student/apply_grade_recheck', data={
        'course_grade': str(grade.id),
        'reason': 'I believe there was an error in the grading of my final exam. I reviewed my responses and compared them to the course material, and I am confident that I deserve a higher mark. I would appreciate a thorough re-evaluation of my exam paper. This reason is long enough for the character limit.'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Your grade recheck request has been submitted successfully!" in response.data
    assert b"Grade Recheck Request Confirmed!" in response.data
    assert b"Introduction to C++ Programming" in response.data # Course name on confirmation

    # Verify in DB
    with client.application.app_context():
        recheck = GradeRecheck.query.filter_by(student_id=auth_mock_student.id, grade_id=grade.id).first()
        assert recheck is not None
        assert recheck.status == 'Pending'
        assert "I believe there was an error" in recheck.reason

def test_apply_grade_recheck_post_validation_error_short_reason(client, auth_mock_student, setup_test_data):
    """Test grade recheck submission fails with too short reason."""
    with client.application.app_context():
        grade = Grade.query.filter_by(student_id=auth_mock_student.id, course_id='CS111').first()
        assert grade is not None

    response = client.post('/enrollment_services/student/apply_grade_recheck', data={
        'course_grade': str(grade.id),
        'reason': 'Too short.' # Less than 50 chars
    }, follow_redirects=True)

    assert response.status_code == 200 # Redirects back to form
    assert b"Error in Reason: Reason must be between 50 and 500 characters." in response.data
    
    with client.application.app_context():
        recheck = GradeRecheck.query.filter_by(student_id=auth_mock_student.id, grade_id=grade.id).first()
        assert recheck is None # No recheck should be created

def test_apply_grade_recheck_post_already_pending(client, auth_mock_student, setup_test_data):
    """Test grade recheck submission fails if a pending request already exists."""
    with client.application.app_context():
        grade = Grade.query.filter_by(student_id=auth_mock_student.id, course_id='CS111').first()
        assert grade is not None
        # Manually create a pending recheck
        existing_recheck = GradeRecheck(
            student_id=auth_mock_student.id, grade_id=grade.id, course_id='CS111',
            original_grade='A', reason='Initial pending request', status='Pending', date_submitted=datetime.utcnow()
        )
        db.session.add(existing_recheck)
        db.session.commit()

    response = client.post('/enrollment_services/student/apply_grade_recheck', data={
        'course_grade': str(grade.id),
        'reason': 'This is another request for the same grade, hoping it will be processed.'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"A recheck request for this grade is already pending." in response.data
    assert b"Your Recheck History" in response.data # Should redirect to history

def test_apply_grade_recheck_on_hold_restricted(client, auth_mock_student, setup_test_data):
    """Test that applying for grade recheck is restricted when student has an active hold and service is restricted."""
    with client.application.app_context():
        # Add an active hold
        hold = Hold(
            HoldID='HOLD_RECHECK',
            StudentID=auth_mock_student.id,
            reason='Academic Misconduct',
            holdDate=datetime.utcnow().date(),
            status='Active'
        )
        db.session.add(hold)
        # Set grade recheck service to be NOT available on hold (default in setup_test_data is True, need to override or create new)
        # In routes.py, it's set to True by default, so this test should pass (allow application)
        # If the intention is to restrict this, ServiceAccess(is_available_on_hold=False) needs to be set for 'apply_grade_recheck'
        service_recheck = ServiceAccess.query.filter_by(service_name='apply_grade_recheck').first()
        if service_recheck:
            service_recheck.is_available_on_hold = False
        else:
            db.session.add(ServiceAccess(service_name='apply_grade_recheck', is_available_on_hold=False))
        db.session.commit()

        grade = Grade.query.filter_by(student_id=auth_mock_student.id, course_id='CS111').first()

    response = client.post('/enrollment_services/student/apply_grade_recheck', data={
        'course_grade': str(grade.id),
        'reason': 'This is a reason that should be long enough to pass validation.'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"You have an active hold on your account (Academic Misconduct). Applying for grade recheck is currently restricted." in response.data
    assert b"Your Student Hold Status" in response.data # Check if redirected to hold status page

def test_view_recheck_history_get(client, auth_mock_student, setup_test_data):
    """Test that the recheck history page loads and shows past requests."""
    with client.application.app_context():
        grade = Grade.query.filter_by(student_id=auth_mock_student.id, course_id='CS111').first()
        # Create a recheck request
        recheck = GradeRecheck(
            student_id=auth_mock_student.id, grade_id=grade.id, course_id='CS111',
            original_grade='A', reason='Test request', status='Pending', date_submitted=datetime.utcnow()
        )
        db.session.add(recheck)
        db.session.commit()

    response = client.get('/enrollment_services/student/recheck_history')
    assert response.status_code == 200
    assert b"Your Recheck History" in response.data
    assert b"CS111 - Introduction to C++ Programming" in response.data
    assert b"Pending" in response.data

# Special Application Tests
def test_apply_special_application_get(client, auth_mock_student, setup_test_data):
    """Test that the special application page loads."""
    response = client.get('/enrollment_services/student/apply_special_application')
    assert response.status_code == 200
    assert b"Apply for Special Application" in response.data
    assert b"Application for Graduation" in response.data

def test_apply_special_application_post_graduation_success(client, auth_mock_student, setup_test_data):
    """Test successful submission of a graduation application."""
    response = client.post('/enrollment_services/student/apply_special_application', data={
        'application_type': 'Graduation',
        'reason': 'I have completed all my program requirements and wish to apply for graduation in the upcoming ceremony. I have checked my academic record and confirmed all credits are met. This reason is long enough for the character limit.'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Your application has been successfully submitted!" in response.data
    assert b"Welcome to the Enrollment Services Dashboard" in response.data # Redirects to dashboard

    # Verify in DB
    with client.application.app_context():
        app = SpecialApplication.query.filter_by(student_id=auth_mock_student.id, application_type='Graduation').first()
        assert app is not None
        assert app.status == 'Pending'
        assert app.course_id is None # Graduation should not have a course_id

def test_apply_special_application_post_compassionate_pass_success(client, auth_mock_student, setup_test_data):
    """Test successful submission of a compassionate pass application."""
    response = client.post('/enrollment_services/student/apply_special_application', data={
        'application_type': 'Compassionate Pass',
        'course': 'MA111', # MA111 exists in dummy data
        'reason': 'Due to unforeseen medical circumstances during the exam period, I was unable to perform to my full potential in this course. I have supporting documentation for my medical condition. This reason is long enough for the character limit.'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Your application has been successfully submitted!" in response.data
    assert b"Welcome to the Enrollment Services Dashboard" in response.data

    # Verify in DB
    with client.application.app_context():
        app = SpecialApplication.query.filter_by(student_id=auth_mock_student.id, application_type='Compassionate Pass').first()
        assert app is not None
        assert app.status == 'Pending'
        assert app.course_id == 'MA111'

def test_apply_special_application_post_validation_error_missing_course(client, auth_mock_student, setup_test_data):
    """Test special application submission fails if course is missing for relevant types."""
    response = client.post('/enrollment_services/student/apply_special_application', data={
        'application_type': 'Compassionate Pass',
        'course': '', # Missing course
        'reason': 'This is a reason that should be long enough to pass validation in other cases but not this one.'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Error in Course: Please select a course for this application type." in response.data

def test_apply_special_application_post_validation_error_short_reason(client, auth_mock_student, setup_test_data):
    """Test special application submission fails with too short reason."""
    response = client.post('/enrollment_services/student/apply_special_application', data={
        'application_type': 'Graduation',
        'reason': 'Short reason.' # Less than 50 chars
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Error in Reason: Reason must be between 50 and 1000 characters." in response.data

def test_apply_special_application_on_hold_restricted(client, auth_mock_student, setup_test_data):
    """Test that applying for special application is restricted when student has an active hold and service is restricted."""
    with client.application.app_context():
        # Add an active hold
        hold = Hold(
            HoldID='HOLD_SPECIAL_APP',
            StudentID=auth_mock_student.id,
            reason='Financial Arrears',
            holdDate=datetime.utcnow().date(),
            status='Active'
        )
        db.session.add(hold)
        
        # Set special application service to be NOT available on hold
        service_special_app = ServiceAccess.query.filter_by(service_name='apply_special_application').first()
        if service_special_app:
            service_special_app.is_available_on_hold = False
        else:
            db.session.add(ServiceAccess(service_name='apply_special_application', is_available_on_hold=False))
        db.session.commit()

    response = client.post('/enrollment_services/student/apply_special_application', data={
        'application_type': 'Graduation',
        'reason': 'This is a reason that should be long enough to pass validation but will be blocked by hold.'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"You have an active hold on your account (Financial Arrears). Applying for special applications is currently restricted." in response.data
    assert b"Your Student Hold Status" in response.data # Check if redirected to hold status page

def test_view_special_applications_history_get(client, auth_mock_student, setup_test_data):
    """Test that the special applications history page loads and shows past applications."""
    with client.application.app_context():
        # Create a special application
        app = SpecialApplication(
            student_id=auth_mock_student.id, application_type='Graduation', course_id=None,
            reason='Applied for graduation', status='Pending', date_submitted=datetime.utcnow()
        )
        db.session.add(app)
        db.session.commit()

    response = client.get('/enrollment_services/student/applications_history')
    assert response.status_code == 200
    assert b"Your Special Applications History" in response.data
    assert b"Graduation" in response.data
    assert b"Pending" in response.data

# Student Hold Status Tests
def test_student_hold_status_get_no_hold(client, auth_mock_student, setup_test_data):
    """Test hold status page when there is no active hold."""
    response = client.get('/enrollment_services/student/hold_status')
    assert response.status_code == 200
    assert b"Student Hold Status" in response.data
    assert b"No Active Holds Found" in response.data
    assert b"Your account currently has no active holds. You have full access to all student services." in response.data

def test_student_hold_status_get_with_hold(client, auth_mock_student, setup_test_data):
    """Test hold status page when there is an active hold."""
    with client.application.app_context():
        # Add an active hold
        hold = Hold(
            HoldID='HOLD123',
            StudentID=auth_mock_student.id,
            reason='Outstanding Fees',
            holdDate=datetime.utcnow().date(),
            status='Active'
        )
        db.session.add(hold)
        db.session.commit()

    response = client.get('/enrollment_services/student/hold_status')
    assert response.status_code == 200
    assert b"Student Hold Status" in response.data
    assert b"You have an ACTIVE HOLD on your account!" in response.data
    assert b"Reason: Outstanding Fees" in response.data
    assert b"Course Registration" in response.data # Check for a restricted service (default from setup_test_data)

# API Endpoints Tests
def test_get_courses_api(client, auth_mock_student, setup_test_data):
    """Test the API endpoint for getting all courses."""
    response = client.get('/enrollment_services/api/courses')
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 8 # Number of courses added in setup_test_data
    assert any(c['CourseID'] == 'CS111' for c in data)

def test_get_students_api(client, auth_mock_student, setup_test_data):
    """Test the API endpoint for getting all students."""
    response = client.get('/enrollment_services/api/students')
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1 # At least the test student
    assert any(s['StudentID'] == 'test_student_id_123' for s in data)

def test_get_enrollments_api(client, auth_mock_student, setup_test_data):
    """Test the API endpoint for getting all enrollments."""
    with client.application.app_context():
        # Manually create an enrollment for API test
        enrollment = Enrollment(
            EnrollmentID='api_enr_test',
            StudentID=auth_mock_student.id,
            CourseID='CS111',
            EnrollmentDate=datetime.utcnow().date()
        )
        db.session.add(enrollment)
        db.session.commit()

    response = client.get('/enrollment_services/api/enrollments')
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1 # At least one enrollment
    assert any(e['EnrollmentID'] == 'api_enr_test' for e in data)
    assert any(e['CourseID'] == 'CS111' and e['StudentID'] == 'test_student_id_123' for e in data)
