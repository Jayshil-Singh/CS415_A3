import os
import sqlite3

def sync_student_data():
    try:
        # Database paths
        enrollment_db = os.path.join("C:", os.sep, "Users", "yashp", "Documents", "CS415", "CS415_A3", 
                                   "SAS_Services", "instance", "enrollment.db")
        student_service_db = os.path.join("C:", os.sep, "Users", "yashp", "Documents", "CS415", "CS415_A3", 
                                        "StudentService", "instance", "studentservice.db")

        # Verify both databases exist
        if not os.path.exists(enrollment_db):
            print(f"Error: enrollment.db not found at {enrollment_db}")
            return
        if not os.path.exists(student_service_db):
            print(f"Error: studentservice.db not found at {student_service_db}")
            return

        print("Connecting to databases...")
        enrollment_conn = sqlite3.connect(enrollment_db)
        student_service_conn = sqlite3.connect(student_service_db)
        
        e_cursor = enrollment_conn.cursor()
        s_cursor = student_service_conn.cursor()

        # Get all student addresses from enrollment.db
        print("\nFetching student address data from enrollment.db...")
        e_cursor.execute("""
            SELECT StudentID, Province, Country, ZipCode
            FROM Addressing_Student
            ORDER BY StudentID
        """)
        enrollment_students = e_cursor.fetchall()
        
        print("\nCurrent records in enrollment.db:")
        print("StudentID | Province | Country | ZipCode")
        print("-" * 50)
        for student in enrollment_students:
            print(f"{student[0]} | {student[1]} | {student[2]} | {student[3] if student[3] else ''}")

        # Get existing students from studentservice.db
        s_cursor.execute("SELECT StudentID FROM Addressing_Student")
        existing_students = {row[0] for row in s_cursor.fetchall()}

        # Insert or update records in studentservice.db
        print("\nSyncing data to studentservice.db...")
        for student in enrollment_students:
            student_id, province, country, zipcode = student
            
            if student_id in existing_students:
                # Update existing record
                s_cursor.execute("""
                    UPDATE Addressing_Student 
                    SET Province = ?, Country = ?, ZipCode = ?
                    WHERE StudentID = ?
                """, (province, country, zipcode, student_id))
            else:
                # Insert new record
                s_cursor.execute("""
                    INSERT INTO Addressing_Student (StudentID, Province, Country, ZipCode)
                    VALUES (?, ?, ?, ?)
                """, (student_id, province, country, zipcode))

        # Verify the sync
        print("\nVerifying synced data in studentservice.db...")
        s_cursor.execute("SELECT * FROM Addressing_Student ORDER BY StudentID")
        synced_students = s_cursor.fetchall()
        
        print("\nUpdated records in studentservice.db:")
        print("ID | StudentID | Province | Country | ZipCode")
        print("-" * 50)
        for student in synced_students:
            print(f"{student[0]} | {student[1]} | {student[2]} | {student[3]} | {student[4] if student[4] else ''}")

        # Commit changes
        student_service_conn.commit()
        print("\nSync completed successfully!")

    except Exception as e:
        print(f"Error during sync: {str(e)}")
        if 'student_service_conn' in locals():
            student_service_conn.rollback()
    finally:
        if 'enrollment_conn' in locals():
            enrollment_conn.close()
        if 'student_service_conn' in locals():
            student_service_conn.close()

if __name__ == "__main__":
    sync_student_data() 