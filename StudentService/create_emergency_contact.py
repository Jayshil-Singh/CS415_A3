import sqlite3
import os

def setup_emergency_contact():
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
    
    # Add test data
    test_data = [
        ('S00000002', 'Abudaba', None, 'Ravakodo', 'Father', '679-2181930'),
        ('S00000003', 'Abulina', None, 'Ravakodoi', 'Mother', '679-5556666')
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
    
    print("Emergency Contact table created and populated with test data.")

if __name__ == '__main__':
    setup_emergency_contact() 