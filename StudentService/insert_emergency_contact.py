import sqlite3
import os

# Get the absolute path to the database
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'instance', 'studentservice.db'))
print(f"Database path: {db_path}")

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# First, remove duplicates by keeping only the first entry for each StudentID
cursor.execute("""
DELETE FROM Emergency_Contact 
WHERE ID NOT IN (
    SELECT MIN(ID)
    FROM Emergency_Contact
    GROUP BY StudentID
)
""")

# Verify the cleanup
cursor.execute("SELECT * FROM Emergency_Contact ORDER BY StudentID")
print("After cleanup - Current data:", cursor.fetchall())

# Now insert new data only if it doesn't exist
cursor.execute("""
INSERT OR IGNORE INTO Emergency_Contact 
(StudentID, FirstName, MiddleName, LastName, Relationship, ContactPhone)
VALUES 
('S00000003', 'Abulina', NULL, 'Ravakodoi', 'Mother', '679-5556666')
""")

# Commit changes
conn.commit()

# Final verification
cursor.execute("SELECT * FROM Emergency_Contact ORDER BY StudentID")
print("Final data in table:", cursor.fetchall())
conn.close()
print("Done!") 