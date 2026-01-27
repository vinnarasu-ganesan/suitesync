"""
Compare specific tests between environments to find the parsing difference.
Run this on BOTH local and server to compare results.
"""
from app import create_app
from models import Test

app = create_app()

# Test cases that should have TestRail IDs
# Use os-independent paths
import os
test_cases_to_check = [
    ('test_add_disk_with_disk_type_thick_thin', os.path.join('morpheus_automation', 'tests', 'api', 'test_vme_exploratory_e2e.py')),
    ('test_clone_instance', os.path.join('morpheus_automation', 'tests', 'api', 'test_vme_beta_api.py')),
    ('test_cluster_storage_utilization', os.path.join('morpheus_automation', 'tests', 'api', 'api_bug_automation', 'test_vme_api_bugs.py')),
    ('test_create_instance_on_simplivity_datastore', os.path.join('morpheus_automation', 'tests', 'api', 'simplivity_automation', 'test_instance_scenarios.py')),
    ('test_migrate_volume_between_gfs2_datastores', os.path.join('morpheus_automation', 'tests', 'api', 'test_gfs2_certification.py')),
]

print("=" * 80)
print("PARAMETRIZED TEST COMPARISON")
print("=" * 80)

with app.app_context():
    for test_name, test_file in test_cases_to_check:
        test = Test.query.filter_by(test_name=test_name, test_file=test_file).first()

        print(f"\n{test_name}")
        print(f"  File: {test_file}")

        if test:
            print(f"  TestRail ID: {test.testrail_case_id if test.testrail_case_id else 'NONE'}")
            print(f"  Markers: {test.markers}")
            print(f"  Status: {'✅ HAS ID' if test.testrail_case_id else '❌ MISSING ID'}")
        else:
            print(f"  Status: ❌ TEST NOT FOUND IN DATABASE")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    total = Test.query.count()
    with_ids = Test.query.filter(Test.testrail_case_id.isnot(None), Test.testrail_case_id != '').count()
    multi_ids = Test.query.filter(Test.testrail_case_id.like('%,%')).count()

    print(f"Total tests: {total}")
    print(f"Tests with TestRail ID: {with_ids}")
    print(f"Tests with multiple IDs: {multi_ids}")
    print("=" * 80)
