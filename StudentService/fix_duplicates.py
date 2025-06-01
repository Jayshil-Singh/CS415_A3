import sqlite3
import os

# Use the exact database path
db_path = r"C:\Users\yashp\Documents\CS415\CS415_A3\StudentService\instance\studentservice.db"

print(f"Using database at: {db_path}")

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check current data
    print("\nBefore cleanup:")
    cursor.execute("SELECT * FROM Emergency_Contact ORDER BY StudentID")
    print(cursor.fetchall())

    # Remove duplicates
    cursor.execute("""
    DELETE FROM Emergency_Contact 
    WHERE ID NOT IN (
        SELECT MIN(ID)
        FROM Emergency_Contact
        GROUP BY StudentID
    )
    """)
    
    # Verify the cleanup
    print("\nAfter cleanup:")
    cursor.execute("SELECT * FROM Emergency_Contact ORDER BY StudentID")
    print(cursor.fetchall())

    # Commit changes
    conn.commit()
    print("\nDuplicate entries have been removed successfully!")

except sqlite3.Error as e:
    print(f"An error occurred: {e}")
finally:
    conn.close()