import logging
from datetime import datetime
from models import db, Test, TestRailCase, SyncLog
from services.git_service import GitService
from services.pytest_parser import PytestParser
from services.testrail_service import TestRailService

logger = logging.getLogger(__name__)


class SyncService:
    """Service for synchronizing tests between Git repository and TestRail."""

    def __init__(self, config):
        self.config = config
        self.git_service = GitService(
            config.get('GIT_REPO_URL'),
            config.get('GIT_CLONE_PATH'),
            config.get('GIT_BRANCH'),
            username=config.get('GITHUB_USERNAME'),
            token=config.get('GITHUB_TOKEN')
        )

        if config.get('TESTRAIL_URL') and config.get('TESTRAIL_EMAIL') and config.get('TESTRAIL_API_KEY'):
            self.testrail_service = TestRailService(
                config.get('TESTRAIL_URL'),
                config.get('TESTRAIL_EMAIL'),
                config.get('TESTRAIL_API_KEY'),
                config.get('TESTRAIL_SUITE_ID')
            )
        else:
            self.testrail_service = None
            logger.warning("TestRail credentials not configured")

    def sync_tests(self, sync_type='manual'):
        """Perform a full synchronization of tests."""
        sync_log = SyncLog(
            sync_type=sync_type,
            status='in_progress',
            started_at=datetime.utcnow()
        )
        db.session.add(sync_log)
        db.session.commit()

        try:
            # Step 1: Clone or update repository
            logger.info("Cloning/updating Git repository...")
            if not self.git_service.clone_or_update():
                sync_log.status = 'failed'
                sync_log.message = 'Failed to clone/update repository'
                sync_log.completed_at = datetime.utcnow()
                db.session.commit()
                return sync_log

            sync_log.commit_hash = self.git_service.get_current_commit_hash()
            sync_log.branch = self.git_service.get_current_branch()
            db.session.commit()

            # Step 2: Parse test files
            logger.info("Parsing test files...")
            tests = PytestParser.parse_repository(self.git_service)
            sync_log.tests_found = len(tests)
            db.session.commit()

            # Step 3: Sync tests with database
            logger.info(f"Syncing {len(tests)} tests with database...")
            tests_synced = 0
            tests_failed = 0

            for test_data in tests:
                try:
                    test = Test.query.filter_by(test_id=test_data['test_id']).first()

                    if test:
                        # Update existing test
                        test.test_name = test_data['test_name']
                        test.test_file = test_data['test_file']
                        test.test_class = test_data['test_class']
                        test.description = test_data['description']
                        test.markers = test_data.get('markers', [])
                        test.testrail_case_id = test_data['testrail_case_id']
                        test.updated_at = datetime.utcnow()
                    else:
                        # Create new test
                        test = Test(
                            test_id=test_data['test_id'],
                            test_name=test_data['test_name'],
                            test_file=test_data['test_file'],
                            test_class=test_data['test_class'],
                            description=test_data['description'],
                            markers=test_data.get('markers', []),
                            testrail_case_id=test_data['testrail_case_id']
                        )
                        db.session.add(test)

                    tests_synced += 1

                except Exception as e:
                    logger.error(f"Error syncing test {test_data['test_id']}: {e}")
                    tests_failed += 1

            db.session.commit()

            # Step 4: Sync with TestRail if configured
            if self.testrail_service:
                logger.info("Syncing with TestRail...")
                self._sync_with_testrail()

            # Step 5: Mark old tests as archived
            self._archive_missing_tests(tests)

            # Update sync log
            sync_log.status = 'success'
            sync_log.tests_synced = tests_synced
            sync_log.tests_failed = tests_failed
            sync_log.message = f'Successfully synced {tests_synced} tests'
            sync_log.completed_at = datetime.utcnow()
            db.session.commit()

            logger.info(f"Sync completed: {tests_synced} synced, {tests_failed} failed")
            return sync_log

        except Exception as e:
            logger.error(f"Sync error: {e}")
            sync_log.status = 'failed'
            sync_log.message = str(e)
            sync_log.completed_at = datetime.utcnow()
            db.session.commit()
            return sync_log

    def _sync_with_testrail(self):
        """Sync test information with TestRail."""
        try:
            # Get suite information first
            logger.info("Fetching suite information...")
            suite_info = self.testrail_service.get_suite()
            suite_name = suite_info.get('name', f'Suite {self.testrail_service.suite_id}') if suite_info else f'Suite {self.testrail_service.suite_id}'
            logger.info(f"Suite name: {suite_name}")

            # Get all sections and create a mapping of section_id -> section_name
            logger.info("Fetching sections...")
            sections = self.testrail_service.get_sections()
            sections_map = {}
            if sections:
                for section in sections:
                    section_id = str(section.get('id', ''))
                    section_name = section.get('name', f'Section {section_id}')
                    sections_map[section_id] = section_name
            logger.info(f"Found {len(sections_map)} sections")

            # Get all TestRail cases
            response = self.testrail_service.get_cases()
            if not response:
                logger.warning("No cases retrieved from TestRail")
                return

            # Handle paginated response (dict with 'cases' key) or direct list
            if isinstance(response, dict) and 'cases' in response:
                cases = response['cases']
            elif isinstance(response, list):
                cases = response
            else:
                logger.error(f"Unexpected TestRail response format: {type(response)}")
                return

            logger.info(f"Retrieved {len(cases)} cases from TestRail")

            # Track current case IDs from TestRail
            current_case_ids = set()

            # Update or create TestRail cases in database
            for case in cases:
                case_id = f"C{case['id']}"
                current_case_ids.add(case_id)
                section_id = str(case.get('section_id', ''))
                section_name = sections_map.get(section_id, f'Section {section_id}')

                # Extract all custom fields (fields starting with 'custom_')
                custom_fields = {}
                for key, value in case.items():
                    if key.startswith('custom_'):
                        custom_fields[key] = value

                testrail_case = TestRailCase.query.filter_by(case_id=case_id).first()

                if testrail_case:
                    testrail_case.title = case['title']
                    testrail_case.section_id = section_id
                    testrail_case.section_name = section_name
                    testrail_case.suite_id = str(case.get('suite_id', ''))
                    testrail_case.suite_name = suite_name
                    testrail_case.type_id = case.get('type_id')
                    testrail_case.priority_id = case.get('priority_id')
                    testrail_case.custom_fields = custom_fields
                    testrail_case.updated_at = datetime.utcnow()
                else:
                    testrail_case = TestRailCase(
                        case_id=case_id,
                        title=case['title'],
                        section_id=section_id,
                        section_name=section_name,
                        suite_id=str(case.get('suite_id', '')),
                        suite_name=suite_name,
                        type_id=case.get('type_id'),
                        priority_id=case.get('priority_id'),
                        custom_fields=custom_fields
                    )
                    db.session.add(testrail_case)

            # Delete TestRail cases that no longer exist in TestRail
            all_db_cases = TestRailCase.query.all()
            deleted_count = 0
            for db_case in all_db_cases:
                if db_case.case_id not in current_case_ids:
                    logger.info(f"Deleting case {db_case.case_id} ({db_case.title}) - no longer exists in TestRail")
                    db.session.delete(db_case)
                    deleted_count += 1

            db.session.commit()
            logger.info(f"TestRail cases synced successfully. Deleted {deleted_count} cases that no longer exist in TestRail.")

        except Exception as e:
            logger.error(f"Error syncing with TestRail: {e}")

    def _archive_missing_tests(self, current_tests):
        """Mark tests that are no longer in the repository as archived."""
        current_test_ids = {test['test_id'] for test in current_tests}
        active_tests = Test.query.filter_by(status='active').all()

        archived_count = 0
        for test in active_tests:
            if test.test_id not in current_test_ids:
                test.status = 'archived'
                test.updated_at = datetime.utcnow()
                archived_count += 1

        if archived_count > 0:
            db.session.commit()
            logger.info(f"Archived {archived_count} tests")

    def get_sync_status(self):
        """Get the status of the last sync operation."""
        last_sync = SyncLog.query.order_by(SyncLog.started_at.desc()).first()
        return last_sync.to_dict() if last_sync else None

