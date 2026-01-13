"""
Migration script to add TestRail validation fields to Test model.

Run this script to add the testrail_status and testrail_validated_at columns
to the tests table.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text

def migrate():
    """Add testrail_status and testrail_validated_at columns."""
    app = create_app()

    with app.app_context():
        try:
            # Check if columns already exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('tests')]

            if 'testrail_status' not in columns:
                print("Adding testrail_status column...")
                with db.engine.connect() as conn:
                    conn.execute(text(
                        "ALTER TABLE tests ADD COLUMN testrail_status VARCHAR(50) DEFAULT 'unknown'"
                    ))
                    conn.commit()
                print("✓ Added testrail_status column")
            else:
                print("testrail_status column already exists")

            if 'testrail_validated_at' not in columns:
                print("Adding testrail_validated_at column...")
                with db.engine.connect() as conn:
                    conn.execute(text(
                        "ALTER TABLE tests ADD COLUMN testrail_validated_at DATETIME"
                    ))
                    conn.commit()
                print("✓ Added testrail_validated_at column")
            else:
                print("testrail_validated_at column already exists")

            print("\nMigration completed successfully!")

        except Exception as e:
            print(f"Error during migration: {e}")
            raise

if __name__ == '__main__':
    migrate()

