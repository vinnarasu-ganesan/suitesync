"""
Script to populate suite_name and section_name for existing TestRail cases
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, TestRailCase
from services.testrail_service import TestRailService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def populate_names():
    app = create_app()

    with app.app_context():
        logger.info("Starting to populate suite and section names...")

        # Get TestRail configuration
        testrail_url = app.config.get('TESTRAIL_URL')
        testrail_email = app.config.get('TESTRAIL_EMAIL')
        testrail_api_key = app.config.get('TESTRAIL_API_KEY')
        testrail_suite_id = app.config.get('TESTRAIL_SUITE_ID')

        # Create TestRail service
        service = TestRailService(testrail_url, testrail_email, testrail_api_key, testrail_suite_id)

        # Get suite information
        logger.info("Fetching suite information...")
        suite_info = service.get_suite()
        suite_name = suite_info.get('name', f'Suite {testrail_suite_id}') if suite_info else f'Suite {testrail_suite_id}'
        logger.info(f"Suite name: {suite_name}")

        # Get all sections and create a mapping
        logger.info("Fetching sections...")
        sections = service.get_sections()
        sections_map = {}
        if sections:
            for section in sections:
                section_id = str(section.get('id', ''))
                section_name = section.get('name', f'Section {section_id}')
                sections_map[section_id] = section_name
        logger.info(f"Found {len(sections_map)} sections")

        # Update all existing cases in database
        logger.info("Updating TestRail cases in database...")
        cases = TestRailCase.query.all()
        updated_count = 0

        for case in cases:
            # Update suite name
            case.suite_name = suite_name

            # Update section name
            section_id = case.section_id
            if section_id in sections_map:
                case.section_name = sections_map[section_id]
            else:
                case.section_name = f'Section {section_id}'

            updated_count += 1

            if updated_count % 100 == 0:
                logger.info(f"Updated {updated_count} cases...")

        # Commit all changes
        db.session.commit()
        logger.info(f"✓ Successfully updated {updated_count} TestRail cases with suite and section names")

if __name__ == '__main__':
    populate_names()

