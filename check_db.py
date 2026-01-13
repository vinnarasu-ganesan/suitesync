"""Quick script to check database contents."""
from app import create_app
from models import db, TestRailCase, Test

app = create_app()

with app.app_context():
    # Count TestRail cases
    testrail_count = TestRailCase.query.count()
    print(f"TestRail cases in database: {testrail_count}")

    # Count Tests
    test_count = Test.query.count()
    print(f"Tests in database: {test_count}")

    # Show first few TestRail cases
    if testrail_count > 0:
        print("\nFirst 5 TestRail cases:")
        cases = TestRailCase.query.limit(5).all()
        for case in cases:
            print(f"  - {case.case_id}: {case.title[:50]}...")
    else:
        print("\n⚠️  No TestRail cases found in database!")
        print("   You need to run a sync operation to populate the database.")
        print("   Go to the Sync page in the UI and click 'Sync Now'")

