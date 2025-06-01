import sqlite3
import os

def replicate_data():
    """
    Replicates address and emergency contact data from enrollment.db to studentservice.db
    """
    # Get absolute paths based on current file location
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    
    enrollment_db = os.path.join(os.path.dirname(root_dir), 'SAS_Services', 'instance', 'enrollment.db')
    student_service_db = os.path.join(root_dir, 'instance', 'studentservice.db')

    # Validate database files exist
    if not os.path.exists(enrollment_db):
        raise FileNotFoundError(f"Enrollment database not found at: {enrollment_db}")
    
    if not os.path.exists(student_service_db):
        raise FileNotFoundError(f"Student service database not found at: {student_service_db}")

    # Connect to both databases
    enrollment_conn = sqlite3.connect(enrollment_db)
    service_conn = sqlite3.connect(student_service_db)
    
    try:
        # Create tables if they don't exist in studentservice.db
        service_cursor = service_conn.cursor()
        service_cursor.execute("""
            CREATE TABLE IF NOT EXISTS Addressing_Student (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                StudentID VARCHAR(20) NOT NULL,
                Province VARCHAR(100) NOT NULL,
                Country VARCHAR(100) NOT NULL,
                ZipCode VARCHAR(20),
                FOREIGN KEY (StudentID) REFERENCES Student(StudentID) ON DELETE CASCADE
            )
        """)

        service_cursor.execute("""
            CREATE TABLE IF NOT EXISTS Emergency_Contact (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                StudentID VARCHAR(20) NOT NULL,
                FirstName VARCHAR(100) NOT NULL,
                MiddleName VARCHAR(100),
                LastName VARCHAR(100) NOT NULL,
                Relationship VARCHAR(50) NOT NULL,
                ContactPhone VARCHAR(20) NOT NULL,
                FOREIGN KEY (StudentID) REFERENCES Student(StudentID) ON DELETE CASCADE
            )
        """)

        # Replicate address data
        print("Replicating address data...")
        enrollment_cursor = enrollment_conn.cursor()

        # Get all address data from enrollment.db
        enrollment_cursor.execute("SELECT * FROM Addressing_Student")
        address_data = enrollment_cursor.fetchall()

        # Clear existing data in studentservice.db
        service_cursor.execute("DELETE FROM Addressing_Student")

        # Insert address data in studentservice.db
        for row in address_data:
            service_cursor.execute("""
                INSERT INTO Addressing_Student 
                (ID, StudentID, Province, Country, ZipCode)
                VALUES (?, ?, ?, ?, ?)
            """, row)

        # Replicate emergency contact data
        print("Replicating emergency contact data...")
        # Get all emergency contact data from enrollment.db
        enrollment_cursor.execute("SELECT * FROM Emergency_Contact")
        emergency_contact_data = enrollment_cursor.fetchall()

        # Clear existing data in studentservice.db
        service_cursor.execute("DELETE FROM Emergency_Contact")

        # Insert emergency contact data in studentservice.db
        for row in emergency_contact_data:
            service_cursor.execute("""
                INSERT INTO Emergency_Contact 
                (ID, StudentID, FirstName, MiddleName, LastName, Relationship, ContactPhone)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, row)

        # Commit changes
        service_conn.commit()
        print("Data replication completed successfully!")

    except Exception as e:
        print(f"Error during replication: {str(e)}")
        service_conn.rollback()
        raise
    finally:
        enrollment_conn.close()
        service_conn.close()

if __name__ == "__main__":
    replicate_data() 