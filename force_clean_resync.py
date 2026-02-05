"""
Force clean re-parse of all tests by clearing and re-syncing.
This ensures all tests get re-parsed with the new logic.
"""
from app import create_app
from services.sync_service import SyncService
from services.git_service import GitService
from services.pytest_parser import PytestParser
from config import Config
from models import db, Test
from datetime import datetime

app = create_app()

print("=" * 80)
print("FORCE CLEAN RE-SYNC")
print("=" * 80)

with app.app_context():
    print("\n1. CURRENT STATE")
    print("-" * 80)
    total_before = Test.query.count()
    with_ids_before = Test.query.filter(Test.testrail_case_id.isnot(None), Test.testrail_case_id != '').count()
    print(f"   Total tests: {total_before}")
    print(f"   Tests with TestRail ID: {with_ids_before}")

    print("\n2. DELETING ALL TEST RECORDS")
    print("-" * 80)
    print("   This will force a complete re-parse...")
    deleted_count = Test.query.delete()
    db.session.commit()
    print(f"   ✅ Deleted {deleted_count} test records")

    print("\n3. RE-PARSING ALL TESTS WITH NEW LOGIC")
    print("-" * 80)

    # Initialize services
    git_service = GitService(
        Config.GIT_REPO_URL,
        Config.GIT_CLONE_PATH,
        Config.GIT_BRANCH,
        username=Config.GITHUB_USERNAME,
        token=Config.GITHUB_TOKEN
    )

    # Make sure repo is up to date
    print("   Updating repository...")
    if not git_service.clone_or_update():
        print("   ❌ Failed to update repository")
        exit(1)

    # Parse all tests
    print("   Parsing test files...")
    tests = PytestParser.parse_repository(git_service)
    print(f"   ✅ Parsed {len(tests)} tests")

    # Insert into database
    print("   Inserting into database...")
    for test_data in tests:
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

    db.session.commit()
    print(f"   ✅ Inserted {len(tests)} tests")

    print("\n4. FINAL STATE")
    print("-" * 80)
    total_after = Test.query.count()
    with_ids_after = Test.query.filter(Test.testrail_case_id.isnot(None), Test.testrail_case_id != '').count()
    without_ids_after = Test.query.filter((Test.testrail_case_id == None) | (Test.testrail_case_id == '')).count()
    multi_ids_after = Test.query.filter(Test.testrail_case_id.like('%,%')).count()

    print(f"   Total tests: {total_after}")
    print(f"   Tests WITH TestRail ID: {with_ids_after}")
    print(f"   Tests WITHOUT TestRail ID: {without_ids_after}")
    print(f"   Tests with multiple IDs: {multi_ids_after}")

    print("\n5. COMPARISON")
    print("-" * 80)
    print(f"   Before: {with_ids_before} tests with IDs")
    print(f"   After:  {with_ids_after} tests with IDs")
    print(f"   Change: {with_ids_after - with_ids_before:+d}")

    if with_ids_after > with_ids_before:
        print(f"\n   ✅ SUCCESS! Found {with_ids_after - with_ids_before} more TestRail IDs")
    elif with_ids_after == with_ids_before:
        print(f"\n   ⚠️  No change - investigate test files or parsing logic")
    else:
        print(f"\n   ❌ Lost {with_ids_before - with_ids_after} TestRail IDs!")

    print("\n" + "=" * 80)
    print("NEXT STEP: Run validation")
    print("   python -c \"from app import create_app; from routes.api import validate_testrail_ids; app = create_app(); app.app_context().push(); validate_testrail_ids()\"")
    print("=" * 80)
