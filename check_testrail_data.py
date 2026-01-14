from app import create_app
from models import TestRailCase
import json

app = create_app()

with app.app_context():
    # Get a sample case
    case = TestRailCase.query.first()
    if case:
        print("Sample TestRail Case:")
        print(f"  case_id: {case.case_id}")
        print(f"  title: {case.title}")
        print(f"  suite_id: {case.suite_id}")
        print(f"  suite_name: {case.suite_name}")
        print(f"  section_id: {case.section_id}")
        print(f"  section_name: {case.section_name}")
        print(f"  type_id: {case.type_id}")
        print(f"  priority_id: {case.priority_id}")
        print(f"  custom_fields: {json.dumps(case.custom_fields, indent=2) if case.custom_fields else None}")

        # Check unique suites
        print("\n\nUnique suites:")
        suites = TestRailCase.query.with_entities(TestRailCase.suite_id).distinct().all()
        for suite in suites:
            print(f"  - {suite[0]}")

        # Check unique sections (first 10)
        print("\n\nFirst 10 unique sections:")
        sections = TestRailCase.query.with_entities(TestRailCase.section_id).distinct().limit(10).all()
        for section in sections:
            print(f"  - {section[0]}")

