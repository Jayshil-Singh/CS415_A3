import sqlite3
import os

def cleanup_emergency_contacts():
    # Get the path to the database
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'enrollment.db')
    
    print(f"Database path: {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create a temporary table with the latest entries
    cursor.execute("""
        CREATE TEMPORARY TABLE temp_emergency_contact AS
        SELECT * FROM Emergency_Contact
        WHERE ID IN (
            SELECT MAX(ID)
            FROM Emergency_Contact
            GROUP BY StudentID
        )
    """)
    
    # Drop the original table
    cursor.execute("DROP TABLE IF EXISTS Emergency_Contact")
    
    # Recreate the original table
    cursor.execute("""
        CREATE TABLE Emergency_Contact (
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
    
    # Copy data from temporary table
    cursor.execute("""
        INSERT INTO Emergency_Contact (StudentID, FirstName, MiddleName, LastName, Relationship, ContactPhone)
        SELECT StudentID, FirstName, MiddleName, LastName, Relationship, ContactPhone
        FROM temp_emergency_contact
    """)
    
    # Drop temporary table
    cursor.execute("DROP TABLE IF EXISTS temp_emergency_contact")
    
    # Commit changes and close connection
    conn.commit()
    
    # Print current data
    print("\nCurrent Emergency Contact data:")
    cursor.execute("SELECT * FROM Emergency_Contact ORDER BY StudentID")
    for row in cursor.fetchall():
        print(row)
    
    conn.close()
    
    print("\nEmergency Contact table cleaned up - duplicates removed.")

if __name__ == '__main__':
    cleanup_emergency_contacts() 