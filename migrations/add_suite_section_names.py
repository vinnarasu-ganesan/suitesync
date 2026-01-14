"""
Migration script to add suite_name and section_name columns to testrail_cases table
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    app = create_app()

    with app.app_context():
        logger.info("Starting migration: Adding suite_name and section_name columns")

        try:
            # Add columns using raw SQL
            with db.engine.connect() as conn:
                # Check if columns already exist
                result = conn.execute(db.text("PRAGMA table_info(testrail_cases)"))
                columns = [row[1] for row in result]

                if 'suite_name' not in columns:
                    logger.info("Adding suite_name column...")
                    conn.execute(db.text("ALTER TABLE testrail_cases ADD COLUMN suite_name VARCHAR(500)"))
                    conn.commit()
                    logger.info("✓ suite_name column added")
                else:
                    logger.info("suite_name column already exists")

                if 'section_name' not in columns:
                    logger.info("Adding section_name column...")
                    conn.execute(db.text("ALTER TABLE testrail_cases ADD COLUMN section_name VARCHAR(500)"))
                    conn.commit()
                    logger.info("✓ section_name column added")
                else:
                    logger.info("section_name column already exists")

            logger.info("Migration completed successfully!")

        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)
            raise

if __name__ == '__main__':
    migrate()

