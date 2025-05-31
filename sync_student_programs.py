import sqlite3
import os

def sync_student_programs():
    """
    Syncs student program data from enrollment.db to studentservice.db
    """
    # Get absolute paths based on current file location
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    enrollment_db = os.path.join(current_dir, 'SAS_Services', 'instance', 'enrollment.db')
    student_service_db = os.path.join(current_dir, 'StudentService', 'instance', 'studentservice.db')

    # Validate database files exist
    if not os.path.exists(enrollment_db):
        raise FileNotFoundError(f"Enrollment database not found at: {enrollment_db}")
    
    if not os.path.exists(student_service_db):
        raise FileNotFoundError(f"Student service database not found at: {student_service_db}")

    try:
        # Connect to both databases
        enroll_conn = sqlite3.connect(enrollment_db)
        service_conn = sqlite3.connect(student_service_db)
        
        enroll_cursor = enroll_conn.cursor()
        service_cursor = service_conn.cursor()

        # Create tables in studentservice.db if they don't exist
        service_cursor.execute("""
            CREATE TABLE IF NOT EXISTS Program_Student (
                ProgramID INTEGER PRIMARY KEY AUTOINCREMENT,
                ProgramName VARCHAR(100) NOT NULL,
                StudentID VARCHAR(20) NOT NULL
            )
        """)

        service_cursor.execute("""
            CREATE TABLE IF NOT EXISTS Subprogram_Student (
                SubProgramID INTEGER PRIMARY KEY AUTOINCREMENT,
                SubProgramName VARCHAR(100) NOT NULL,
                StudentID VARCHAR(20) NOT NULL
            )
        """)

        service_cursor.execute("""
            CREATE TABLE IF NOT EXISTS Type_Student (
                TypeID INTEGER PRIMARY KEY AUTOINCREMENT,
                ProgramType VARCHAR(100) NOT NULL,
                StudentID VARCHAR(20) NOT NULL
            )
        """)

        # Clear existing data in studentservice.db tables
        service_cursor.execute("DELETE FROM Program_Student")
        service_cursor.execute("DELETE FROM Subprogram_Student")

        # Get Student_Program data from enrollment.db
        enroll_cursor.execute("""
            SELECT sp.StudentID, p.ProgramName 
            FROM Student_Program sp
            JOIN Program p ON sp.ProgramID = p.ProgramID
        """)
        program_data = enroll_cursor.fetchall()

        # Insert program data into studentservice.db
        service_cursor.executemany(
            "INSERT INTO Program_Student (StudentID, ProgramName) VALUES (?, ?)",
            program_data
        )

        # Initialize empty list for all subprogram data
        all_subprogram_data = []

        # Get Student_Subprogram data from student_subprogram_association table
        enroll_cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='student_subprogram_association'
        """)
        if enroll_cursor.fetchone():
            enroll_cursor.execute("""
                SELECT ss.StudentID, sp.SubProgramName
                FROM student_subprogram_association ss
                JOIN SubProgram sp ON ss.SubProgramID = sp.SubProgramID
            """)
            all_subprogram_data.extend(enroll_cursor.fetchall())
            print("Retrieved data from student_subprogram_association table")

        # Get Student_Subprogram data from Student_SubProgram table
        enroll_cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='Student_SubProgram'
        """)
        if enroll_cursor.fetchone():
            enroll_cursor.execute("""
                SELECT ss.StudentID, sp.SubProgramName
                FROM Student_SubProgram ss
                JOIN SubProgram sp ON ss.SubProgramID = sp.SubProgramID
            """)
            all_subprogram_data.extend(enroll_cursor.fetchall())
            print("Retrieved data from Student_SubProgram table")

        # Remove duplicates from subprogram data (if any)
        all_subprogram_data = list(set(all_subprogram_data))

        # Insert all subprogram data into studentservice.db
        if all_subprogram_data:
            service_cursor.executemany(
                "INSERT INTO Subprogram_Student (StudentID, SubProgramName) VALUES (?, ?)",
                all_subprogram_data
            )
            print(f"Inserted {len(all_subprogram_data)} subprogram entries")
        else:
            print("No subprogram data found in either table")

        # Add the specific Type_Student entry
        service_cursor.execute("""
            INSERT INTO Type_Student (ProgramType, StudentID)
            VALUES (?, ?)
        """, ("Certificate", "S00000002"))

        # Commit changes and close connections
        service_conn.commit()
        print("Successfully synced student program data and added Type_Student entry")

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        if service_conn:
            service_conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
        if service_conn:
            service_conn.rollback()
    finally:
        if enroll_conn:
            enroll_conn.close()
        if service_conn:
            service_conn.close()

if __name__ == "__main__":
    sync_student_programs() 