"""
Simple force re-sync - Deletes tests and re-parses with new logic.
Safe to run - only affects the Test table, not TestRail cases.
"""
from app import create_app
from models import db, Test
from services.git_service import GitService
from services.pytest_parser import PytestParser
from config import Config

print("=" * 80)
print("FORCE RE-SYNC - Clean Re-parse of All Tests")
print("=" * 80)

app = create_app()

with app.app_context():
    # Step 1: Current state
    print("\n1. BEFORE:")
    before_total = Test.query.count()
    before_with_ids = Test.query.filter(Test.testrail_case_id.isnot(None), Test.testrail_case_id != '').count()
    before_multi = Test.query.filter(Test.testrail_case_id.like('%,%')).count()
    print(f"   Total: {before_total}, With IDs: {before_with_ids}, Multi IDs: {before_multi}")

    # Step 2: Delete all tests
    print("\n2. DELETING all test records...")
    deleted = Test.query.delete()
    db.session.commit()
    print(f"   ✅ Deleted {deleted} records")

    # Step 3: Re-parse
    print("\n3. RE-PARSING with new parametrize logic...")
    git_service = GitService(
        Config.GIT_REPO_URL,
        Config.GIT_CLONE_PATH,
        Config.GIT_BRANCH,
        username=Config.GITHUB_USERNAME,
        token=Config.GITHUB_TOKEN
    )

    print("   Updating repository...")
    git_service.clone_or_update()

    print("   Parsing test files...")
    tests = PytestParser.parse_repository(git_service)
    print(f"   ✅ Parsed {len(tests)} tests")

    # Step 4: Insert into database
    print("\n4. INSERTING into database...")
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

    # Step 5: Final state
    print("\n5. AFTER:")
    after_total = Test.query.count()
    after_with_ids = Test.query.filter(Test.testrail_case_id.isnot(None), Test.testrail_case_id != '').count()
    after_multi = Test.query.filter(Test.testrail_case_id.like('%,%')).count()
    print(f"   Total: {after_total}, With IDs: {after_with_ids}, Multi IDs: {after_multi}")

    # Step 6: Show improvement
    print("\n6. CHANGE:")
    print(f"   Tests with IDs: {before_with_ids} → {after_with_ids} ({after_with_ids - before_with_ids:+d})")
    print(f"   Multi IDs:      {before_multi} → {after_multi} ({after_multi - before_multi:+d})")

    if after_with_ids > 220:
        print("\n✅ SUCCESS! Tests with IDs increased to expected level (~226)")
    else:
        print(f"\n⚠️  Still low: {after_with_ids}/226 expected")

    print("\n" + "=" * 80)
    print("NEXT STEP: Run validation")
    print("  Click 'Validate TestRail IDs' button in the UI")
    print("  OR run: python -c \"from app import create_app; from routes.api import validate_testrail_ids; app=create_app(); app.app_context().push(); validate_testrail_ids()\"")
    print("=" * 80)
