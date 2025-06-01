import sqlite3
import os
from datetime import datetime

def create_document_tables(cursor, is_enrollment_db=True):
    # Common fields between both databases
    if is_enrollment_db:
        # Enrollment database schema (lowercase)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS BirthCertificate (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id VARCHAR(20) NOT NULL,
                filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(512) NOT NULL,
                upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                verified BOOLEAN DEFAULT 0,
                FOREIGN KEY (student_id) REFERENCES Student(StudentID) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ValidID (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id VARCHAR(20) NOT NULL,
                filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(512) NOT NULL,
                upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                verified BOOLEAN DEFAULT 0,
                id_type VARCHAR(50) NOT NULL,
                FOREIGN KEY (student_id) REFERENCES Student(StudentID) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS AcademicTranscript (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id VARCHAR(20) NOT NULL,
                filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(512) NOT NULL,
                upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                verified BOOLEAN DEFAULT 0,
                year_level VARCHAR(20) NOT NULL,
                FOREIGN KEY (student_id) REFERENCES Student(StudentID) ON DELETE CASCADE
            )
        """)
    else:
        # StudentService database schema (uppercase)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS BirthCertificate (
                DocumentID INTEGER PRIMARY KEY AUTOINCREMENT,
                StudentID VARCHAR(20) NOT NULL,
                FileName VARCHAR(255) NOT NULL,
                FilePath VARCHAR(512) NOT NULL,
                UploadDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                VerificationStatus VARCHAR(20) DEFAULT 'Pending',
                FOREIGN KEY (StudentID) REFERENCES Student(StudentID) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ValidID (
                DocumentID INTEGER PRIMARY KEY AUTOINCREMENT,
                StudentID VARCHAR(20) NOT NULL,
                FileName VARCHAR(255) NOT NULL,
                FilePath VARCHAR(512) NOT NULL,
                UploadDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                VerificationStatus VARCHAR(20) DEFAULT 'Pending',
                IDType VARCHAR(50) NOT NULL,
                FOREIGN KEY (StudentID) REFERENCES Student(StudentID) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS AcademicTranscript (
                DocumentID INTEGER PRIMARY KEY AUTOINCREMENT,
                StudentID VARCHAR(20) NOT NULL,
                FileName VARCHAR(255) NOT NULL,
                FilePath VARCHAR(512) NOT NULL,
                UploadDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                VerificationStatus VARCHAR(20) DEFAULT 'Pending',
                TranscriptType VARCHAR(20) NOT NULL,
                FOREIGN KEY (StudentID) REFERENCES Student(StudentID) ON DELETE CASCADE
            )
        """)

def create_address_and_emergency_tables(cursor, is_enrollment_db=True):
    # Create Addressing_Student table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Addressing_Student (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            StudentID VARCHAR(20) NOT NULL,
            Province VARCHAR(100) NOT NULL,
            Country VARCHAR(100) NOT NULL,
            ZipCode VARCHAR(20),
            FOREIGN KEY (StudentID) REFERENCES Student(StudentID) ON DELETE CASCADE
        )
    """)

    # Create Emergency_Contact table
    cursor.execute("""
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

def verify_tables(cursor, is_enrollment_db=True):
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\nExisting tables: {[table[0] for table in tables]}")
    
    # Check document tables content
    doc_tables = ['BirthCertificate', 'ValidID', 'AcademicTranscript']
    for table in doc_tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        print(f"\n{table} contents ({len(rows)} rows):")
        for row in rows:
            print(row)

def copy_existing_data(src_cursor, dest_cursor):
    # Copy data from enrollment to student service for S00000002 and S00000003
    students = ['S00000002', 'S00000003']
    
    for student_id in students:
        # Copy Birth Certificate
        src_cursor.execute("SELECT * FROM BirthCertificate WHERE student_id = ?", (student_id,))
        birth_cert = src_cursor.fetchone()
        if birth_cert:
            dest_cursor.execute("""
                INSERT OR REPLACE INTO BirthCertificate 
                (StudentID, FileName, FilePath, VerificationStatus)
                VALUES (?, ?, ?, ?)
            """, (student_id, birth_cert[2], birth_cert[3], 'Verified' if birth_cert[5] else 'Pending'))
        
        # Copy Valid ID
        src_cursor.execute("SELECT * FROM ValidID WHERE student_id = ?", (student_id,))
        valid_id = src_cursor.fetchone()
        if valid_id:
            dest_cursor.execute("""
                INSERT OR REPLACE INTO ValidID 
                (StudentID, FileName, FilePath, VerificationStatus, IDType)
                VALUES (?, ?, ?, ?, ?)
            """, (student_id, valid_id[2], valid_id[3], 'Verified' if valid_id[5] else 'Pending', valid_id[6]))
        
        # Copy Academic Transcript
        src_cursor.execute("SELECT * FROM AcademicTranscript WHERE student_id = ?", (student_id,))
        transcript = src_cursor.fetchone()
        if transcript:
            dest_cursor.execute("""
                INSERT OR REPLACE INTO AcademicTranscript 
                (StudentID, FileName, FilePath, VerificationStatus, TranscriptType)
                VALUES (?, ?, ?, ?, ?)
            """, (student_id, transcript[2], transcript[3], 'Verified' if transcript[5] else 'Pending', transcript[6]))

def main():
    # Absolute paths to databases
    enrollment_db_path = r"C:\Users\yashp\Documents\CS415\CS415_A3\SAS_Services\instance\enrollment.db"
    student_service_db_path = r"C:\Users\yashp\Documents\CS415\CS415_A3\StudentService\instance\studentservice.db"
    
    # Update enrollment database
    print("\nUpdating enrollment database schema...")
    conn_enrollment = sqlite3.connect(enrollment_db_path)
    cursor_enrollment = conn_enrollment.cursor()
    create_document_tables(cursor_enrollment, is_enrollment_db=True)
    create_address_and_emergency_tables(cursor_enrollment, is_enrollment_db=True)
    print("Verifying enrollment database tables:")
    verify_tables(cursor_enrollment, is_enrollment_db=True)
    conn_enrollment.commit()
    
    # Update student service database
    print("\nUpdating student service database schema...")
    conn_service = sqlite3.connect(student_service_db_path)
    cursor_service = conn_service.cursor()
    create_document_tables(cursor_service, is_enrollment_db=False)
    create_address_and_emergency_tables(cursor_service, is_enrollment_db=False)
    
    # Copy existing data from enrollment to student service
    print("\nCopying existing data between databases...")
    copy_existing_data(cursor_enrollment, cursor_service)
    conn_service.commit()
    
    print("\nVerifying student service database tables:")
    verify_tables(cursor_service, is_enrollment_db=False)
    
    conn_enrollment.close()
    conn_service.close()
    print("\nDatabase schema updates completed successfully")

if __name__ == '__main__':
    main() 