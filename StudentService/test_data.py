import sqlite3
import os

def init_test_db():
    # Get the path to the database
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'studentservice.db')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
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
    
    # Add some test data
    test_data = [
        ('S10000001', 'John', None, 'Doe', 'Father', '679-1234567'),
        ('S10000002', 'Mary', 'Jane', 'Smith', 'Mother', '679-7654321')
    ]
    
    # Insert test data
    cursor.executemany("""
        INSERT OR REPLACE INTO Emergency_Contact 
        (StudentID, FirstName, MiddleName, LastName, Relationship, ContactPhone)
        VALUES (?, ?, ?, ?, ?, ?)
    """, test_data)
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Test database initialized with emergency contact data.")

if __name__ == '__main__':
    init_test_db() 