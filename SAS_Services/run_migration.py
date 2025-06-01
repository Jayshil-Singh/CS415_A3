import sqlite3
import os

def create_addressing_table(db_path):
    """Create Addressing_Student table in the specified database."""
    try:
        # Ensure the instance directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create the Addressing_Student table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Addressing_Student (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                StudentID VARCHAR(20) NOT NULL,
                Province VARCHAR(100) NOT NULL,
                Country VARCHAR(100) NOT NULL,
                ZipCode VARCHAR(20),
                FOREIGN KEY (StudentID) REFERENCES Student(StudentID) ON DELETE CASCADE
            )
        """)
        
        # Commit the changes
        conn.commit()
        print(f"Successfully created Addressing_Student table in {db_path}")
        
    except Exception as e:
        print(f"Error creating table in {db_path}: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Get the absolute path of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define database paths
    enrollment_db = os.path.join(current_dir, 'instance', 'enrollment.db')
    
    # Create table in SAS_Services database
    create_addressing_table(enrollment_db) 