"""Script to trigger a re-sync to update tests with new parametrize parsing."""
from app import create_app
from services.sync_service import SyncService
from config import Config

app = create_app()

with app.app_context():
    print("Starting re-sync to update parametrized tests...")
    print("=" * 80)
    
    config = {
        'GIT_REPO_URL': Config.GIT_REPO_URL,
        'GIT_CLONE_PATH': Config.GIT_CLONE_PATH,
        'GIT_BRANCH': Config.GIT_BRANCH,
        'GITHUB_USERNAME': Config.GITHUB_USERNAME,
        'GITHUB_TOKEN': Config.GITHUB_TOKEN,
        'TESTRAIL_URL': Config.TESTRAIL_URL,
        'TESTRAIL_EMAIL': Config.TESTRAIL_EMAIL,
        'TESTRAIL_API_KEY': Config.TESTRAIL_API_KEY,
        'TESTRAIL_SUITE_ID': Config.TESTRAIL_SUITE_ID,
    }
    
    sync_service = SyncService(config)
    sync_log = sync_service.sync_tests(sync_type='manual')
    
    print("\n" + "=" * 80)
    print("Sync completed!")
    print(f"Status: {sync_log.status}")
    print(f"Tests found: {sync_log.tests_found}")
    print(f"Tests synced: {sync_log.tests_synced}")
    print(f"Tests failed: {sync_log.tests_failed}")
    
    if sync_log.message:
        print(f"Message: {sync_log.message}")
