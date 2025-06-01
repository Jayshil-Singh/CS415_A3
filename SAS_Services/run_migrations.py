"""Run database migrations

This script runs all available database migrations in the migrations directory.
"""

from migrations import update_gender_values

def run_migrations():
    print("Running migrations...")
    try:
        # Run the gender values update migration
        update_gender_values.upgrade()
        print("All migrations completed successfully.")
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == '__main__':
    run_migrations() 