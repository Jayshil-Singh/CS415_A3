"""Add document tables migration"""
from yoyo import step

__depends__ = {'20240601_01_initial'}

steps = [
    step("""
        DROP TABLE IF EXISTS BirthCertificate;
        CREATE TABLE BirthCertificate (
            DocumentID INTEGER PRIMARY KEY AUTOINCREMENT,
            StudentID VARCHAR(20) NOT NULL,
            FileName VARCHAR(255) NOT NULL,
            FilePath VARCHAR(512) NOT NULL,
            UploadDate DATETIME DEFAULT CURRENT_TIMESTAMP,
            VerificationStatus VARCHAR(20) DEFAULT 'Pending',
            FOREIGN KEY (StudentID) REFERENCES Student(StudentID) ON DELETE CASCADE
        );
    """,
    """
        DROP TABLE IF EXISTS BirthCertificate;
    """),
    
    step("""
        DROP TABLE IF EXISTS ValidID;
        CREATE TABLE ValidID (
            DocumentID INTEGER PRIMARY KEY AUTOINCREMENT,
            StudentID VARCHAR(20) NOT NULL,
            FileName VARCHAR(255) NOT NULL,
            FilePath VARCHAR(512) NOT NULL,
            UploadDate DATETIME DEFAULT CURRENT_TIMESTAMP,
            VerificationStatus VARCHAR(20) DEFAULT 'Pending',
            IDType VARCHAR(50) NOT NULL,
            FOREIGN KEY (StudentID) REFERENCES Student(StudentID) ON DELETE CASCADE
        );
    """,
    """
        DROP TABLE IF EXISTS ValidID;
    """),
    
    step("""
        DROP TABLE IF EXISTS AcademicTranscript;
        CREATE TABLE AcademicTranscript (
            DocumentID INTEGER PRIMARY KEY AUTOINCREMENT,
            StudentID VARCHAR(20) NOT NULL,
            FileName VARCHAR(255) NOT NULL,
            FilePath VARCHAR(512) NOT NULL,
            UploadDate DATETIME DEFAULT CURRENT_TIMESTAMP,
            VerificationStatus VARCHAR(20) DEFAULT 'Pending',
            TranscriptType VARCHAR(20) NOT NULL,
            FOREIGN KEY (StudentID) REFERENCES Student(StudentID) ON DELETE CASCADE
        );
    """,
    """
        DROP TABLE IF EXISTS AcademicTranscript;
    """)
] 