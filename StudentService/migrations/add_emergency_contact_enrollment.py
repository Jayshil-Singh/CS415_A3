"""
Add Emergency_Contact table to enrollment.db
"""

from yoyo import step

__depends__ = {'add_addressing_table'}

steps = [
    step("""
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
    """,
    """
        DROP TABLE IF EXISTS Emergency_Contact
    """)
] 