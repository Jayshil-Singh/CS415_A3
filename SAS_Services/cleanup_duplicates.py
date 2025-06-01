import os
import sqlite3
from datetime import datetime

def cleanup_duplicates():
    conn = None
    try:
        # Get the path to the StudentService database
        db_path = os.path.join("C:", os.sep, "Users", "yashp", "Documents", "CS415", "CS415_A3", 
                              "StudentService", "instance", "studentservice.db")
        
        if not os.path.exists(db_path):
            print(f"Error: Database not found at {db_path}")
            return

        print(f"Connecting to database at {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Clean up Addressing_Student table
        print("\nCleaning up Addressing_Student table...")
        
        # First check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='Addressing_Student'
        """)
        if not cursor.fetchone():
            print("Error: Addressing_Student table not found in the database")
            return
        
        # Show current records before cleanup
        print("\nCurrent records before cleanup:")
        cursor.execute("SELECT * FROM Addressing_Student ORDER BY StudentID")
        records = cursor.fetchall()
        print("ID | StudentID | Province | Country | ZipCode")
        print("-" * 50)
        for record in records:
            print(f"{record[0]} | {record[1]} | {record[2]} | {record[3]} | {record[4] if record[4] else ''}")
        
        # Get count of records before cleanup
        cursor.execute("SELECT COUNT(*) FROM Addressing_Student")
        before_count = cursor.fetchone()[0]
        print(f"\nRecords before cleanup: {before_count}")

        # Create temporary table with unique records
        cursor.execute("""
            CREATE TEMPORARY TABLE temp_Addressing_Student AS
            SELECT DISTINCT StudentID, Province, Country, ZipCode,
                   MIN(ID) as ID
            FROM Addressing_Student
            GROUP BY StudentID
        """)

        # Delete all records from original table
        cursor.execute("DELETE FROM Addressing_Student")

        # Insert unique records back
        cursor.execute("""
            INSERT INTO Addressing_Student (ID, StudentID, Province, Country, ZipCode)
            SELECT ID, StudentID, Province, Country, ZipCode
            FROM temp_Addressing_Student
            ORDER BY StudentID
        """)

        # Drop temporary table
        cursor.execute("DROP TABLE temp_Addressing_Student")

        # Get count of records after cleanup
        cursor.execute("SELECT COUNT(*) FROM Addressing_Student")
        after_count = cursor.fetchone()[0]
        print(f"Records after cleanup: {after_count}")
        print(f"Removed {before_count - after_count} duplicate records")

        # Show the cleaned up records
        print("\nRecords after cleanup:")
        cursor.execute("SELECT * FROM Addressing_Student ORDER BY StudentID")
        records = cursor.fetchall()
        print("ID | StudentID | Province | Country | ZipCode")
        print("-" * 50)
        for record in records:
            print(f"{record[0]} | {record[1]} | {record[2]} | {record[3]} | {record[4] if record[4] else ''}")

        # Commit changes and close connection
        conn.commit()
        print("\nCleanup completed successfully!")

    except Exception as e:
        print(f"Error during cleanup: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    cleanup_duplicates() 