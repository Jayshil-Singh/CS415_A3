"""
Add Addressing_Student table for storing student address information.
"""

from yoyo import step

steps = [
    step("""
        CREATE TABLE IF NOT EXISTS Addressing_Student (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            StudentID VARCHAR(20) NOT NULL,
            Province VARCHAR(100) NOT NULL,
            Country VARCHAR(100) NOT NULL,
            ZipCode VARCHAR(20),
            FOREIGN KEY (StudentID) REFERENCES Student(StudentID) ON DELETE CASCADE
        )
    """,
    """
        DROP TABLE IF EXISTS Addressing_Student
    """)
] 