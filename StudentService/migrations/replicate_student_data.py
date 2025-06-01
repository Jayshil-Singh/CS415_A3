import sqlite3
import os

def get_db_paths():
    """
    Returns the absolute paths for the enrollment.db and studentservice.db databases.
    """
    enrollment_path = r'C:\Users\yashp\Documents\CS415\CS415_A3\SAS_Services\instance\enrollment.db'
    studentservice_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'studentservice.db')
    return enrollment_path, studentservice_path

def table_exists(cursor, table_name):
    """
    Checks if a table exists in the given database.
    """
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    return cursor.fetchone() is not None

def replicate_table(source_cursor, target_cursor, table_name, source_db_name, target_db_name):
    """
    Replicates a single table's data and schema from source to target database.
    """
    print(f"\n--- Replicating table: {table_name} ---")
    
    # Get the schema of the table from the source database
    source_cursor.execute(f"PRAGMA table_info({table_name})")
    columns = source_cursor.fetchall()
    
    if not columns:
        print(f"Warning: '{table_name}' table not found in '{source_db_name}'")
        return

    # Check if table exists in target
    table_already_exists = table_exists(target_cursor, table_name)

    if not table_already_exists:
        # Create table with same schema
        column_defs = []
        for col in columns:
            name = col[1]
            type_name = col[2]
            not_null = "NOT NULL" if col[3] else ""
            pk = "PRIMARY KEY" if col[5] else ""
            column_defs.append(f"{name} {type_name} {pk} {not_null}".strip())

        create_table_sql = f"CREATE TABLE {table_name} ({', '.join(column_defs)})"
        target_cursor.execute(create_table_sql)
        print(f"Created table '{table_name}'")
    else:
        # Clear existing data
        target_cursor.execute(f"DELETE FROM {table_name}")
        print(f"Cleared existing data from '{table_name}'")

    # Copy data
    source_cursor.execute(f"SELECT * FROM {table_name}")
    rows = source_cursor.fetchall()
    
    if rows:
        column_names = [col[1] for col in columns]
        placeholders = ','.join(['?' for _ in column_names])
        insert_sql = f"INSERT INTO {table_name} ({','.join(column_names)}) VALUES ({placeholders})"
        target_cursor.executemany(insert_sql, rows)
        print(f"Copied {len(rows)} records to '{table_name}'")
    else:
        print(f"No data found in '{table_name}'")

def get_foreign_key_constraints(source_cursor, table_name):
    """
    Gets foreign key constraints for a table.
    """
    source_cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    return source_cursor.fetchall()

def add_foreign_keys(target_cursor, table_name, fk_constraints):
    """
    Adds foreign key constraints to a table.
    """
    for fk in fk_constraints:
        from_col = fk[3]
        to_table = fk[2]
        to_col = fk[4]
        
        alter_sql = f"""
        ALTER TABLE {table_name} 
        ADD CONSTRAINT fk_{table_name}_{from_col}_{to_table}
        FOREIGN KEY ({from_col}) REFERENCES {to_table}({to_col})
        """
        try:
            target_cursor.execute(alter_sql)
        except sqlite3.OperationalError as e:
            if "no such table" not in str(e).lower():
                print(f"Warning: Could not add foreign key constraint: {e}")

def main_replication_script():
    """
    Main function to orchestrate the replication of specified tables.
    """
    enrollment_db, studentservice_db = get_db_paths()
    
    if not os.path.exists(enrollment_db):
        print(f"Error: Source database '{enrollment_db}' not found")
        return
    if not os.path.exists(studentservice_db):
        print(f"Error: Target database '{studentservice_db}' not found")
        return

    source_conn = None
    target_conn = None

    try:
        source_conn = sqlite3.connect(enrollment_db)
        target_conn = sqlite3.connect(studentservice_db)
        
        source_cursor = source_conn.cursor()
        target_cursor = target_conn.cursor()

        # Enable foreign key support
        source_cursor.execute("PRAGMA foreign_keys = ON")
        target_cursor.execute("PRAGMA foreign_keys = ON")

        # Tables to replicate in order (respecting foreign key constraints)
        tables_to_replicate = [
            "Campus",
            "ProgramType",
            "Program",
            "SubProgram",
            "Student",
            "Student_Level",
            "Student_Program",
            "Student_SubProgram",
            "BirthCertificate",
            "ValidID",
            "AcademicTranscript"
        ]

        # First pass: Create tables and copy data
        for table_name in tables_to_replicate:
            replicate_table(source_cursor, target_cursor, table_name, enrollment_db, studentservice_db)

        # Second pass: Add foreign key constraints
        print("\n--- Adding foreign key constraints ---")
        for table_name in tables_to_replicate:
            fk_constraints = get_foreign_key_constraints(source_cursor, table_name)
            if fk_constraints:
                add_foreign_keys(target_cursor, table_name, fk_constraints)

        target_conn.commit()
        print("\nAll tables replicated successfully!")

    except sqlite3.Error as e:
        print(f"\nSQLite error: {e}")
        if target_conn:
            target_conn.rollback()
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        if target_conn:
            target_conn.rollback()
    finally:
        if source_conn:
            source_conn.close()
        if target_conn:
            target_conn.close()

if __name__ == "__main__":
    main_replication_script()
 