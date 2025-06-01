"""Add document tables migration"""
from yoyo import step

__depends__ = {}

steps = [
    step("""
        DROP TABLE IF EXISTS BirthCertificate;
        CREATE TABLE BirthCertificate (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id VARCHAR(20) NOT NULL,
            filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(512) NOT NULL,
            upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            verified BOOLEAN DEFAULT 0,
            FOREIGN KEY (student_id) REFERENCES Student(StudentID) ON DELETE CASCADE
        );
    """,
    """
        DROP TABLE IF EXISTS BirthCertificate;
    """),
    
    step("""
        DROP TABLE IF EXISTS ValidID;
        CREATE TABLE ValidID (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id VARCHAR(20) NOT NULL,
            filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(512) NOT NULL,
            upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            verified BOOLEAN DEFAULT 0,
            id_type VARCHAR(50) NOT NULL,
            FOREIGN KEY (student_id) REFERENCES Student(StudentID) ON DELETE CASCADE
        );
    """,
    """
        DROP TABLE IF EXISTS ValidID;
    """),
    
    step("""
        DROP TABLE IF EXISTS AcademicTranscript;
        CREATE TABLE AcademicTranscript (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id VARCHAR(20) NOT NULL,
            filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(512) NOT NULL,
            upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            verified BOOLEAN DEFAULT 0,
            year_level VARCHAR(20) NOT NULL,
            FOREIGN KEY (student_id) REFERENCES Student(StudentID) ON DELETE CASCADE
        );
    """,
    """
        DROP TABLE IF EXISTS AcademicTranscript;
    """)
] 