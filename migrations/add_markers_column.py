"""Add markers column to tests table."""
import sys
import os

# Add parent directory to path so we can import app and models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db

app = create_app()

with app.app_context():
    print("Adding 'markers' column to 'tests' table...")

    try:
        # Check if column already exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('tests')]

        if 'markers' in columns:
            print("Column 'markers' already exists. Skipping migration.")
        else:
            # Add the column
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE tests ADD COLUMN markers JSON"))
                conn.commit()
            print("Successfully added 'markers' column to 'tests' table.")
    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()

print("\nMigration complete!")
print("Now run a sync to populate markers for existing tests:")
print("  python app.py")
print("  Then click 'Start Full Sync' from the Sync page")

