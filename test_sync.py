"""Test the sync endpoint directly."""
from app import create_app
import json

app = create_app()

with app.app_context():
    from services.sync_service import SyncService

    print("Testing sync service initialization...")
    try:
        sync_service = SyncService(app.config)
        print("[OK] SyncService initialized successfully")

        # Check configuration
        print("\nConfiguration:")
        print(f"  GIT_REPO_URL: {app.config.get('GIT_REPO_URL', 'NOT SET')}")
        print(f"  GIT_CLONE_PATH: {app.config.get('GIT_CLONE_PATH', 'NOT SET')}")
        print(f"  GIT_BRANCH: {app.config.get('GIT_BRANCH', 'NOT SET')}")
        print(f"  TESTRAIL_URL: {app.config.get('TESTRAIL_URL', 'NOT SET')}")
        print(f"  TESTRAIL_SUITE_ID: {app.config.get('TESTRAIL_SUITE_ID', 'NOT SET')}")

        print("\nTrying to run sync_tests...")
        sync_log = sync_service.sync_tests(sync_type='test')
        print(f"[OK] Sync completed: {sync_log.status}")
        print(f"   Tests found: {sync_log.tests_found}")
        print(f"   Tests synced: {sync_log.tests_synced}")
        print(f"   Tests failed: {sync_log.tests_failed}")

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

