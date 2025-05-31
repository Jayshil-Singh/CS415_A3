import sqlite3
import os

# Source and target database paths
source_db = os.path.join('SAS_Services', 'instance', 'enrollment.db')
target_db = os.path.join('StudentService', 'instance', 'studentservice.db')

def copy_student_table():
    # Connect to source database
    source_conn = sqlite3.connect(source_db)
    source_cursor = source_conn.cursor()
    
    # Connect to target database
    target_conn = sqlite3.connect(target_db)
    target_cursor = target_conn.cursor()
    
    try:
        # Get the table schema from source database
        source_cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='Student'")
        create_table_sql = source_cursor.fetchone()[0]
        
        # Drop existing Student table in target if it exists
        target_cursor.execute("DROP TABLE IF EXISTS Student")
        
        # Create the table in target database
        target_cursor.execute(create_table_sql)
        
        # Copy data from source to target
        source_cursor.execute("SELECT * FROM Student")
        rows = source_cursor.fetchall()
        
        # Get column names
        source_cursor.execute("PRAGMA table_info(Student)")
        columns = source_cursor.fetchall()
        num_columns = len(columns)
        
        # Create the INSERT statement with the correct number of placeholders
        placeholders = ','.join(['?' for _ in range(num_columns)])
        insert_sql = f"INSERT INTO Student VALUES ({placeholders})"
        
        # Insert the data
        target_cursor.executemany(insert_sql, rows)
        
        # Commit the changes
        target_conn.commit()
        
        print("Student table successfully copied!")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        target_conn.rollback()
    
    finally:
        # Close connections
        source_conn.close()
        target_conn.close()

if __name__ == "__main__":
    copy_student_table() 