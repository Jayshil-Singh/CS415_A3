"""
Add Addressing_Student table for storing student address information.
"""

from yoyo import step

__depends__ = {'add_document_tables'}

steps = [
    step("""
        CREATE TABLE Addressing_Student (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            StudentID VARCHAR(20) NOT NULL,
            Province VARCHAR(100) NOT NULL,
            Country VARCHAR(100) NOT NULL,
            ZipCode VARCHAR(20),
            FOREIGN KEY (StudentID) REFERENCES Student(StudentID) ON DELETE CASCADE
        )
    """,
    """
        DROP TABLE Addressing_Student
    """)
] 