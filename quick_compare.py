"""
Quick comparison script - shows key metrics to verify environments match
Run on both local and server, then compare output.
"""
from app import create_app
from models import Test, TestRailCase, SyncLog

app = create_app()

with app.app_context():
    # Get key metrics
    total_tests = Test.query.count()
    tests_with_tr_id = Test.query.filter(Test.testrail_case_id.isnot(None), Test.testrail_case_id != '').count()
    tests_multi_ids = Test.query.filter(Test.testrail_case_id.like('%,%')).count()
    validated = Test.query.filter(Test.testrail_validated_at.isnot(None)).count()
    valid = Test.query.filter_by(testrail_status='valid').count()
    deleted = Test.query.filter_by(testrail_status='deleted').count()
    tr_cases = TestRailCase.query.count()

    last_sync = SyncLog.query.order_by(SyncLog.started_at.desc()).first()

    print("=" * 60)
    print("ENVIRONMENT SNAPSHOT")
    print("=" * 60)
    print(f"Total Tests:              {total_tests}")
    print(f"Tests with TestRail ID:   {tests_with_tr_id}")
    print(f"Parametrized Tests:       {tests_multi_ids}")
    print(f"TestRail Cases in DB:     {tr_cases}")
    print("-" * 60)
    print(f"Validated Tests:          {validated}")
    print(f"Valid Tests:              {valid}")
    print(f"Deleted Tests:            {deleted}")
    print("-" * 60)
    if last_sync:
        print(f"Last Sync:                {last_sync.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Sync Status:              {last_sync.status}")
        print(f"Tests Synced:             {last_sync.tests_synced}")
    else:
        print(f"Last Sync:                NEVER")
    print("=" * 60)

    # Quick health check
    issues = []
    if tests_multi_ids == 0:
        issues.append("❌ No parametrized tests (needs sync)")
    if validated != tests_with_tr_id:
        issues.append(f"⚠️  Not all tests validated ({validated}/{tests_with_tr_id})")
    if total_tests < 240:
        issues.append(f"⚠️  Low test count (expected ~250)")

    if issues:
        print("\nISSUES DETECTED:")
        for issue in issues:
            print(f"  {issue}")
        print("\n➡️  RUN: Sync → Validate TestRail IDs")
    else:
        print("\n✅ Environment looks healthy!")
    print("=" * 60)
