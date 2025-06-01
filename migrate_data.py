import sqlite3
import os
from datetime import datetime

def connect_to_db(db_path):
    """Connect to a SQLite database and return the connection."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at: {db_path}")
    return sqlite3.connect(db_path)

def get_table_info(cursor, table_name):
    """Get column information for a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1]: row for row in cursor.fetchall()}

def migrate_data():
    # Database paths
    enrollment_db = os.path.join('SAS_Services', 'instance', 'enrollment.db')
    student_service_db = os.path.join('StudentService', 'instance', 'studentservice.db')
    
    print(f"Source DB path: {os.path.abspath(enrollment_db)}")
    print(f"Destination DB path: {os.path.abspath(student_service_db)}")
    
    # Connect to both databases
    src_conn = connect_to_db(enrollment_db)
    dest_conn = connect_to_db(student_service_db)
    
    src_cur = src_conn.cursor()
    dest_cur = dest_conn.cursor()
    
    try:
        # Start transaction
        dest_conn.execute('BEGIN TRANSACTION')
        
        # Get list of tables in source database
        src_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        source_tables = src_cur.fetchall()
        
        print(f"Tables found in source database: {[table[0] for table in source_tables]}")
        
        # First migrate Program data
        print("\nMigrating Program data...")
        try:
            # Clear existing programs to avoid conflicts
            dest_cur.execute("DELETE FROM Program")
            
            # Get all programs from source
            src_cur.execute("SELECT * FROM Program")
            programs = src_cur.fetchall()
            
            # Create a mapping of program IDs (we'll store the numeric part)
            program_id_map = {}
            
            for program in programs:
                old_program_id = program[0]  # PROG### format
                program_name = program[1]
                
                # Extract numeric part and convert to integer
                numeric_id = int(old_program_id.replace('PROG', ''))
                program_id_map[old_program_id] = numeric_id
                
                # Insert with numeric ID
                dest_cur.execute("""
                    INSERT INTO Program (ProgramID, ProgramName)
                    VALUES (?, ?)
                """, (numeric_id, program_name))
            
            print(f"Migrated {len(programs)} programs with ID mapping")
            print("Program ID mapping:", program_id_map)
            
        except Exception as e:
            print(f"Error migrating Program table: {e}")
            raise
        
        # Migrate Student data
        print("\nMigrating Student data...")
        try:
            # Get column info for both tables
            src_columns = get_table_info(src_cur, 'Student')
            dest_columns = get_table_info(dest_cur, 'Student')
            
            # Get common columns
            common_columns = list(set(src_columns.keys()) & set(dest_columns.keys()))
            columns_str = ', '.join(common_columns)
            
            print(f"Common columns found: {common_columns}")
            
            # Select data from source
            src_cur.execute(f"SELECT {columns_str} FROM Student")
            students = src_cur.fetchall()
            
            # Prepare placeholders for the INSERT statement
            placeholders = ', '.join(['?' for _ in common_columns])
            
            # Insert data into destination
            for student in students:
                dest_cur.execute(f"""
                    INSERT OR REPLACE INTO Student ({columns_str})
                    VALUES ({placeholders})
                """, student)
            
            print(f"Migrated {len(students)} student records")
            
        except Exception as e:
            print(f"Error migrating Student table: {e}")
            raise

        # Special handling for Student_Program to Program_Student migration
        print("\nMigrating Student_Program to Program_Student...")
        try:
            # Clear existing associations
            dest_cur.execute("DELETE FROM Program_Student")
            
            # Get the data from Student_Program
            src_cur.execute("""
                SELECT sp.ProgramID, sp.StudentID 
                FROM Student_Program sp 
                ORDER BY sp.StudentID
            """)
            program_students = src_cur.fetchall()
            
            # Insert into Program_Student with mapped program IDs
            for program_id, student_id in program_students:
                new_program_id = program_id_map.get(program_id)
                if new_program_id is not None:
                    dest_cur.execute("""
                        INSERT INTO Program_Student (ProgramID, StudentID)
                        VALUES (?, ?)
                    """, (new_program_id, student_id))
                else:
                    print(f"Warning: No mapping found for program ID {program_id}")
            
            print(f"Migrated {len(program_students)} program-student associations")
            
        except Exception as e:
            print(f"Error migrating Student_Program to Program_Student: {e}")
            raise
        
        # Migrate other related tables
        related_tables = [
            'Campus',
            'ProgramType',
            'SubProgram',
            'StudentLevel',
            'Addressing_Student',
            'Emergency_Contact',
            'BirthCertificate',
            'ValidID',
            'AcademicTranscript'
        ]
        
        for table in related_tables:
            print(f"\nMigrating {table} data...")
            try:
                # Get column info
                src_columns = get_table_info(src_cur, table)
                dest_columns = get_table_info(dest_cur, table)
                
                if not src_columns:
                    print(f"Table {table} not found in source database")
                    continue
                    
                if not dest_columns:
                    print(f"Table {table} not found in destination database")
                    continue
                
                # Get common columns
                common_columns = list(set(src_columns.keys()) & set(dest_columns.keys()))
                if not common_columns:
                    print(f"No common columns found for table {table}")
                    continue
                    
                columns_str = ', '.join(common_columns)
                placeholders = ', '.join(['?' for _ in common_columns])
                
                # Select data from source
                src_cur.execute(f"SELECT {columns_str} FROM {table}")
                rows = src_cur.fetchall()
                
                # Insert data into destination
                for row in rows:
                    dest_cur.execute(f"""
                        INSERT OR REPLACE INTO {table} ({columns_str})
                        VALUES ({placeholders})
                    """, row)
                
                print(f"Migrated {len(rows)} records from {table}")
                
            except Exception as e:
                print(f"Error migrating {table}: {e}")
                continue
        
        # Commit all changes
        dest_conn.commit()
        print("\nMigration completed successfully!")
        
    except Exception as e:
        dest_conn.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        src_conn.close()
        dest_conn.close()

if __name__ == "__main__":
    migrate_data() 