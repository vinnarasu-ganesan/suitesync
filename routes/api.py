from flask import Blueprint, jsonify, request, current_app
from models import db, Test, TestRailCase, SyncLog
from services.sync_service import SyncService
import logging
import time

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/tests', methods=['GET'])
def get_tests():
    """Get all tests with optional filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    status = request.args.get('status', 'active')
    search = request.args.get('search', '')
    marker = request.args.get('marker', '')  # Marker filter parameter
    testrail_filter = request.args.get('testrail_filter', '')  # TestRail filter parameter

    query = Test.query

    if status:
        query = query.filter_by(status=status)

    if search:
        # Case-insensitive search
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Test.test_id.ilike(search_term),
                Test.test_name.ilike(search_term),
                Test.test_file.ilike(search_term),
                Test.testrail_case_id.ilike(search_term)
            )
        )

    # Apply TestRail filter
    if testrail_filter == 'with':
        query = query.filter(Test.testrail_case_id.isnot(None))
    elif testrail_filter == 'without':
        query = query.filter(Test.testrail_case_id.is_(None))
    elif testrail_filter == 'deleted':
        query = query.filter_by(testrail_status='deleted')

    # Filter by marker - get all results first if marker filter is applied
    if marker:
        # Get all matching tests (not paginated yet)
        all_tests = query.order_by(Test.test_file, Test.test_name).all()
        # Filter by marker in Python
        filtered_tests = [test for test in all_tests if test.markers and marker in test.markers]

        # Manual pagination
        total = len(filtered_tests)
        pages = (total + per_page - 1) // per_page  # Ceiling division
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_tests = filtered_tests[start_idx:end_idx]

        return jsonify({
            'tests': [test.to_dict() for test in paginated_tests],
            'total': total,
            'pages': pages,
            'current_page': page,
            'per_page': per_page
        })
    else:
        # No marker filter - use normal pagination
        pagination = query.order_by(Test.test_file, Test.test_name).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'tests': [test.to_dict() for test in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        })


@api_bp.route('/tests/<int:test_id>', methods=['GET'])
def get_test(test_id):
    """Get a specific test by ID."""
    test = Test.query.get_or_404(test_id)

    # Get associated TestRail case if available
    testrail_cases = []
    if test.testrail_case_id:
        # Handle multiple TestRail IDs
        case_ids = [cid.strip() for cid in test.testrail_case_id.split(',')]
        for case_id in case_ids:
            testrail_case = TestRailCase.query.filter_by(case_id=case_id).first()
            if testrail_case:
                testrail_cases.append(testrail_case)

    result = test.to_dict()
    if testrail_cases:
        # If multiple cases, return the first one but include all
        result['testrail_case'] = testrail_cases[0].to_dict()
        if len(testrail_cases) > 1:
            result['testrail_cases'] = [tc.to_dict() for tc in testrail_cases]

    return jsonify(result)


@api_bp.route('/tests/stats', methods=['GET'])
def get_test_stats():
    """Get statistics about tests."""
    total_tests = Test.query.count()
    active_tests = Test.query.filter_by(status='active').count()
    archived_tests = Test.query.filter_by(status='archived').count()
    tests_with_testrail = Test.query.filter(Test.testrail_case_id.isnot(None)).count()
    tests_without_testrail = Test.query.filter(Test.testrail_case_id.is_(None)).count()
    tests_with_deleted_testrail = Test.query.filter_by(testrail_status='deleted').count()

    return jsonify({
        'total_tests': total_tests,
        'active_tests': active_tests,
        'archived_tests': archived_tests,
        'tests_with_testrail': tests_with_testrail,
        'tests_without_testrail': tests_without_testrail,
        'tests_with_deleted_testrail': tests_with_deleted_testrail
    })


@api_bp.route('/tests/markers', methods=['GET'])
def get_all_markers():
    """Get all unique markers from all tests."""
    try:
        # Query all tests and collect unique markers
        tests = Test.query.filter(Test.markers.isnot(None)).all()

        # Collect all unique markers
        all_markers = set()
        for test in tests:
            if test.markers:
                for marker in test.markers:
                    all_markers.add(marker)

        # Sort alphabetically
        sorted_markers = sorted(list(all_markers))

        logger.info(f"Found {len(sorted_markers)} unique markers")

        return jsonify({
            'markers': sorted_markers,
            'count': len(sorted_markers)
        })
    except Exception as e:
        logger.error(f"Error fetching markers: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e),
            'markers': []
        }), 500


@api_bp.route('/testrail/cases', methods=['GET'])
def get_testrail_cases():
    """Get all TestRail cases with filtering and sorting."""
    start = time.time()
    per_page = 50  # Default value for error handling

    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        sort_by = request.args.get('sort_by', 'case_id', type=str)
        sort_order = request.args.get('sort_order', 'asc', type=str)

        # Filtering parameters
        suite_id = request.args.get('suite_id', type=str)
        section_id = request.args.get('section_id', type=str)
        type_id = request.args.get('type_id', type=int)
        priority_id = request.args.get('priority_id', type=int)
        automation_status = request.args.get('automation_status', type=str)
        search = request.args.get('search', type=str)

        # Build query with filters
        query = TestRailCase.query

        # Apply filters (except automation_status - handled after query for SQLite compatibility)
        if suite_id:
            query = query.filter(TestRailCase.suite_id == suite_id)
        if section_id:
            # Handle multiple section IDs (comma-separated)
            section_ids = [sid.strip() for sid in section_id.split(',') if sid.strip()]
            if len(section_ids) == 1:
                query = query.filter(TestRailCase.section_id == section_ids[0])
            elif len(section_ids) > 1:
                query = query.filter(TestRailCase.section_id.in_(section_ids))
        if type_id:
            query = query.filter(TestRailCase.type_id == type_id)
        if priority_id:
            query = query.filter(TestRailCase.priority_id == priority_id)
        if search:
            # Case-insensitive search for both case_id and title
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    TestRailCase.case_id.ilike(search_term),
                    TestRailCase.title.ilike(search_term)
                )
            )

        # Apply sorting
        sort_column = TestRailCase.case_id  # default
        if sort_by == 'case_id':
            sort_column = TestRailCase.case_id
        elif sort_by == 'title':
            sort_column = TestRailCase.title
        elif sort_by == 'suite_id':
            sort_column = TestRailCase.suite_id
        elif sort_by == 'section_id':
            sort_column = TestRailCase.section_id
        elif sort_by == 'type_id':
            sort_column = TestRailCase.type_id
        elif sort_by == 'priority_id':
            sort_column = TestRailCase.priority_id
        elif sort_by == 'updated_at':
            sort_column = TestRailCase.updated_at

        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # If automation_status filter is applied, we need to filter in Python (SQLite limitation)
        if automation_status:
            # Get all results (without pagination first) to filter by automation status
            all_cases = query.all()

            # Filter by automation status
            filtered_cases = []
            for case in all_cases:
                case_automation_status = None
                if case.custom_fields and 'custom_automation_status' in case.custom_fields:
                    case_automation_status = str(case.custom_fields['custom_automation_status'])

                # Match the automation status
                if case_automation_status == automation_status:
                    filtered_cases.append(case)

            # Manual pagination
            total_filtered = len(filtered_cases)
            total_pages = (total_filtered + per_page - 1) // per_page if total_filtered > 0 else 1

            # Get the page slice
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_cases = filtered_cases[start_idx:end_idx]

            # Build response data
            cases_data = []
            for case in paginated_cases:
                automation_status_val = None
                if case.custom_fields and 'custom_automation_status' in case.custom_fields:
                    automation_status_val = case.custom_fields['custom_automation_status']

                cases_data.append({
                    'id': case.id,
                    'case_id': case.case_id,
                    'title': case.title,
                    'section_id': case.section_id,
                    'section_name': case.section_name,
                    'suite_id': case.suite_id,
                    'suite_name': case.suite_name,
                    'type_id': case.type_id,
                    'priority_id': case.priority_id,
                    'automation_status': automation_status_val,
                    'created_at': case.created_at.isoformat() if case.created_at else None,
                    'updated_at': case.updated_at.isoformat() if case.updated_at else None
                })

            elapsed = (time.time() - start) * 1000
            logger.info(f"[API] /testrail/cases completed in {elapsed:.2f}ms - returned {len(cases_data)} cases (filtered by automation_status)")

            return jsonify({
                'cases': cases_data,
                'total': total_filtered,
                'pages': total_pages,
                'current_page': page,
                'per_page': per_page
            })
        else:
            # Normal pagination without automation_status filter
            pagination = query.paginate(
                page=page, per_page=per_page, error_out=False
            )

            # Optimize: Create lightweight dict without custom_fields to reduce payload size
            cases_data = []
            for case in pagination.items:
                # Extract automation_status from custom_fields if available
                automation_status_val = None
                if case.custom_fields and 'custom_automation_status' in case.custom_fields:
                    automation_status_val = case.custom_fields['custom_automation_status']

                cases_data.append({
                    'id': case.id,
                    'case_id': case.case_id,
                    'title': case.title,
                    'section_id': case.section_id,
                    'section_name': case.section_name,
                    'suite_id': case.suite_id,
                    'suite_name': case.suite_name,
                    'type_id': case.type_id,
                    'priority_id': case.priority_id,
                    'automation_status': automation_status_val,
                    # Exclude full custom_fields to reduce data transfer
                    'created_at': case.created_at.isoformat() if case.created_at else None,
                    'updated_at': case.updated_at.isoformat() if case.updated_at else None
                })

            elapsed = (time.time() - start) * 1000
            logger.info(f"[API] /testrail/cases completed in {elapsed:.2f}ms - returned {len(cases_data)} cases")

            return jsonify({
                'cases': cases_data,
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page,
                'per_page': per_page
            })

    except Exception as e:
        logger.error(f"[API] Error in /testrail/cases: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e),
            'cases': [],
            'total': 0,
            'pages': 0,
            'current_page': 1,
            'per_page': per_page
        }), 500



@api_bp.route('/testrail/stats', methods=['GET'])
def get_testrail_stats():
    """Get TestRail cases statistics, respecting all active filters."""
    from sqlalchemy import func

    # Accept the same filter params that /testrail/cases supports
    suite_id          = request.args.get('suite_id',          type=str)
    section_id        = request.args.get('section_id',        type=str)
    type_id           = request.args.get('type_id',           type=int)
    priority_id       = request.args.get('priority_id',       type=int)
    automation_status = request.args.get('automation_status', type=str)
    search            = request.args.get('search',            type=str)

    # ── SQL-filterable conditions ──────────────────────────────────────────
    query = TestRailCase.query

    if suite_id:
        query = query.filter(TestRailCase.suite_id == suite_id)

    if section_id:
        section_ids = [sid.strip() for sid in section_id.split(',') if sid.strip()]
        if len(section_ids) == 1:
            query = query.filter(TestRailCase.section_id == section_ids[0])
        elif len(section_ids) > 1:
            query = query.filter(TestRailCase.section_id.in_(section_ids))

    if type_id:
        query = query.filter(TestRailCase.type_id == type_id)

    if priority_id:
        query = query.filter(TestRailCase.priority_id == priority_id)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                TestRailCase.case_id.ilike(search_term),
                TestRailCase.title.ilike(search_term)
            )
        )

    # ── automation_status lives inside JSON – filter in Python ────────────
    all_cases = query.all()
    if automation_status:
        all_cases = [
            c for c in all_cases
            if c.custom_fields and
               str(c.custom_fields.get('custom_automation_status', '')) == automation_status
        ]

    # ── Compute aggregates from the fully-filtered list ───────────────────
    total_cases     = len(all_cases)
    unique_sections = len({c.section_id for c in all_cases if c.section_id})
    unique_suites   = len({c.suite_id   for c in all_cases if c.suite_id})

    priority_breakdown = {}
    type_breakdown     = {}
    automation_status_breakdown = {
        '0': 0,  # Deleted
        '1': 0,  # Manual
        '2': 0,  # Obsolete
        '3': 0,  # Will Not Automate
        '4': 0,  # Automated
        '5': 0,  # To Be Automated
        'null': 0
    }

    for case in all_cases:
        if case.priority_id:
            k = str(case.priority_id)
            priority_breakdown[k] = priority_breakdown.get(k, 0) + 1
        if case.type_id:
            k = str(case.type_id)
            type_breakdown[k] = type_breakdown.get(k, 0) + 1
        if case.custom_fields and 'custom_automation_status' in case.custom_fields:
            status = str(case.custom_fields['custom_automation_status'])
            if status in automation_status_breakdown:
                automation_status_breakdown[status] += 1
            else:
                automation_status_breakdown['null'] += 1
        else:
            automation_status_breakdown['null'] += 1

    automated_count       = automation_status_breakdown.get('4', 0)
    manual_count          = automation_status_breakdown.get('1', 0)
    automation_percentage = round((automated_count / total_cases) * 100, 1) if total_cases > 0 else 0

    # Explicit coverage: Automated ÷ (Automated + Manual) × 100
    explicit_total                  = automated_count + manual_count
    explicit_automation_percentage  = round((automated_count / explicit_total) * 100, 1) if explicit_total > 0 else 0

    return jsonify({
        'total_cases': total_cases,
        'unique_sections': unique_sections,
        'unique_suites': unique_suites,
        'priority_breakdown': priority_breakdown,
        'type_breakdown': type_breakdown,
        'automation_status_breakdown': automation_status_breakdown,
        'automated_count': automated_count,
        'manual_count': manual_count,
        'automation_percentage': automation_percentage,
        'explicit_total': explicit_total,
        'explicit_automation_percentage': explicit_automation_percentage
    })


@api_bp.route('/testrail/section-automation', methods=['GET'])
def get_section_automation_stats():
    """Get automation statistics for each section."""
    from sqlalchemy import func, case as sql_case
    import time

    start_time = time.time()

    try:
        logger.info("[Section Automation] Starting to fetch section automation stats")

        # Get all cases with their automation status in a single query
        all_cases = TestRailCase.query.filter(
            TestRailCase.section_id.isnot(None)
        ).all()

        logger.info(f"[Section Automation] Fetched {len(all_cases)} cases in {time.time() - start_time:.2f}s")

        # Build section stats dictionary
        section_map = {}

        for case in all_cases:
            section_id = case.section_id

            if section_id not in section_map:
                section_map[section_id] = {
                    'section_id': section_id,
                    'section_name': case.section_name or f"Section {section_id}",
                    'suite_id': case.suite_id,
                    'suite_name': case.suite_name or f"Suite {case.suite_id}",
                    'total_cases': 0,
                    'automated_count': 0,
                    'manual_count': 0,
                    'to_be_automated_count': 0,
                    'will_not_automate_count': 0,
                    'other_count': 0
                }

            section_map[section_id]['total_cases'] += 1

            # Count automation status
            if case.custom_fields and 'custom_automation_status' in case.custom_fields:
                status = str(case.custom_fields['custom_automation_status'])
                if status == '4':  # Automated
                    section_map[section_id]['automated_count'] += 1
                elif status == '1':  # Manual
                    section_map[section_id]['manual_count'] += 1
                elif status == '5':  # To Be Automated
                    section_map[section_id]['to_be_automated_count'] += 1
                elif status == '3':  # Will Not Automate
                    section_map[section_id]['will_not_automate_count'] += 1
                else:
                    section_map[section_id]['other_count'] += 1
            else:
                section_map[section_id]['other_count'] += 1

        # Calculate automation percentages
        section_stats = []
        for section_data in section_map.values():
            total_cases = section_data['total_cases']
            automated_count = section_data['automated_count']

            automation_percentage = 0
            if total_cases > 0:
                automation_percentage = round((automated_count / total_cases) * 100, 1)

            section_data['automation_percentage'] = automation_percentage
            section_stats.append(section_data)

        # Sort by automation percentage (descending)
        section_stats.sort(key=lambda x: x['automation_percentage'], reverse=True)

        elapsed = time.time() - start_time
        logger.info(f"[Section Automation] Completed in {elapsed:.2f}s - {len(section_stats)} sections")

        return jsonify({
            'status': 'success',
            'sections': section_stats,
            'total_sections': len(section_stats)
        })

    except Exception as e:
        logger.error(f"Error fetching section automation stats: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e),
            'sections': []
        }), 500


@api_bp.route('/testrail/stats/by-suite', methods=['GET'])
def get_testrail_stats_by_suite():
    """Get TestRail automation status breakdown grouped by suite."""
    try:
        # Get all distinct suites stored in the DB
        suites_query = db.session.query(
            TestRailCase.suite_id,
            TestRailCase.suite_name
        ).distinct().filter(TestRailCase.suite_id.isnot(None)).all()

        result = []
        for suite_id, suite_name in suites_query:
            cases = TestRailCase.query.filter_by(suite_id=suite_id).all()
            total_cases = len(cases)

            breakdown = {'0': 0, '1': 0, '2': 0, '3': 0, '4': 0, '5': 0, 'null': 0}

            for case in cases:
                if case.custom_fields and 'custom_automation_status' in case.custom_fields:
                    status = str(case.custom_fields['custom_automation_status'])
                    if status in breakdown:
                        breakdown[status] += 1
                    else:
                        breakdown['null'] += 1
                else:
                    breakdown['null'] += 1

            automated_count = breakdown.get('4', 0)
            manual_count    = breakdown.get('1', 0)
            automation_pct  = round((automated_count / total_cases) * 100, 1) if total_cases > 0 else 0

            # Explicit coverage: Automated ÷ (Automated + Manual) × 100
            explicit_total = automated_count + manual_count
            explicit_pct   = round((automated_count / explicit_total) * 100, 1) if explicit_total > 0 else 0

            result.append({
                'suite_id': suite_id,
                'suite_name': suite_name or f'Suite {suite_id}',
                'total_cases': total_cases,
                'automation_status_breakdown': breakdown,
                'automated_count': automated_count,
                'manual_count': manual_count,
                'automation_percentage': automation_pct,
                'explicit_total': explicit_total,
                'explicit_automation_percentage': explicit_pct
            })

        # Sort by suite_id for a stable order
        result.sort(key=lambda x: x['suite_id'])

        return jsonify({'suites': result})

    except Exception as e:
        logger.error(f"Error fetching TestRail stats by suite: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e), 'suites': []}), 500


@api_bp.route('/testrail/filters', methods=['GET'])
def get_testrail_filters():
    """Get unique values for TestRail filters.

    Accepts an optional ``suite_id`` query param; when supplied, the sections
    list is scoped to that suite only so the UI can keep them in sync.
    """
    from sqlalchemy import func

    suite_id = request.args.get('suite_id', type=str)

    # Suites are always returned in full (never filtered)
    suites = db.session.query(
        TestRailCase.suite_id,
        TestRailCase.suite_name
    ).distinct().filter(TestRailCase.suite_id.isnot(None)).all()
    suite_options = [{'value': s[0], 'label': s[1] if s[1] else f'Suite {s[0]}'} for s in suites]

    # Sections – optionally scoped to the selected suite
    sections_query = db.session.query(
        TestRailCase.section_id,
        TestRailCase.section_name,
        func.count(TestRailCase.id)
    ).filter(TestRailCase.section_id.isnot(None))

    if suite_id:
        sections_query = sections_query.filter(TestRailCase.suite_id == suite_id)

    sections = sections_query.group_by(
        TestRailCase.section_id,
        TestRailCase.section_name
    ).order_by(TestRailCase.section_name).all()
    section_options = [
        {'value': s[0], 'label': f'{s[1] if s[1] else "Section " + s[0]} ({s[2]} cases)'}
        for s in sections
    ]

    # Get unique type IDs
    types = db.session.query(
        TestRailCase.type_id,
        func.count(TestRailCase.id)
    ).filter(TestRailCase.type_id.isnot(None)).group_by(
        TestRailCase.type_id
    ).order_by(TestRailCase.type_id).all()
    type_options = [{'value': t[0], 'label': f'Type {t[0]} ({t[1]} cases)'} for t in types]

    return jsonify({
        'suites': suite_options,
        'sections': section_options,
        'types': type_options
    })


@api_bp.route('/testrail/names', methods=['GET'])
def get_testrail_names():
    """Get section and suite names from database (much faster than API)."""
    try:
        # Get unique sections from database with their names
        # This is MUCH faster than calling TestRail API
        from sqlalchemy import func, distinct

        sections_query = db.session.query(
            TestRailCase.section_id,
            func.min(TestRailCase.title).label('sample_title')
        ).filter(
            TestRailCase.section_id.isnot(None)
        ).group_by(TestRailCase.section_id).all()

        sections_map = {}
        for section_id, _ in sections_query:
            # Use section ID as name for now (fast)
            sections_map[str(section_id)] = f"Section {section_id}"

        # Get unique suites from database
        suites_query = db.session.query(
            TestRailCase.suite_id
        ).filter(
            TestRailCase.suite_id.isnot(None)
        ).distinct().all()

        suites_map = {}
        for suite_id, in suites_query:
            # Use suite ID as name for now (fast)
            suites_map[str(suite_id)] = f"Suite {suite_id}"

        logger.info(f"Loaded {len(sections_map)} sections and {len(suites_map)} suites from database")

        return jsonify({
            'sections': sections_map,
            'suites': suites_map
        })
    except Exception as e:
        logger.error(f"Error fetching TestRail names from database: {e}")
        return jsonify({
            'sections': {},
            'suites': {}
        })


@api_bp.route('/sync', methods=['POST'])
def trigger_sync():
    """Trigger a manual synchronization."""
    try:
        logger.info("Manual sync triggered via API")
        sync_service = SyncService(current_app.config)
        sync_log = sync_service.sync_tests(sync_type='manual')

        logger.info(f"Manual sync completed successfully: {sync_log.id}")
        return jsonify({
            'status': 'success',
            'message': f'Sync completed: {sync_log.tests_synced} tests synced',
            'sync_log': sync_log.to_dict()
        })
    except Exception as e:
        logger.error(f"Error triggering sync: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/sync/status', methods=['GET'])
def get_sync_status():
    """Get the status of the last sync operation."""
    last_sync = SyncLog.query.order_by(SyncLog.started_at.desc()).first()

    if last_sync:
        return jsonify(last_sync.to_dict())
    else:
        return jsonify({
            'message': 'No sync operations found'
        }), 404


@api_bp.route('/sync/logs', methods=['GET'])
def get_sync_logs():
    """Get sync operation history."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    pagination = SyncLog.query.order_by(SyncLog.started_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'logs': [log.to_dict() for log in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    })


@api_bp.route('/webhook/github', methods=['POST'])
def github_webhook():
    """Handle GitHub webhook events."""
    try:
        # Verify webhook signature (optional but recommended)
        # signature = request.headers.get('X-Hub-Signature-256')
        # if not verify_signature(request.data, signature, current_app.config['GITHUB_WEBHOOK_SECRET']):
        #     return jsonify({'error': 'Invalid signature'}), 403

        event = request.headers.get('X-GitHub-Event')
        payload = request.json

        if event == 'push':
            # Check if push is to main branch
            ref = payload.get('ref', '')
            if ref == f"refs/heads/{current_app.config['GIT_BRANCH']}":
                logger.info(f"Received push event to {ref}, triggering sync...")

                # Trigger sync in background (you might want to use Celery for this)
                sync_service = SyncService(current_app.config)
                sync_log = sync_service.sync_tests(sync_type='webhook')

                return jsonify({
                    'status': 'success',
                    'message': 'Sync triggered',
                    'sync_log': sync_log.to_dict()
                })

        return jsonify({'status': 'ignored', 'event': event})

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/tests/validate-testrail', methods=['POST'])
def validate_testrail_ids():
    """Validate TestRail IDs for all tests with TestRail case IDs."""
    from services.testrail_service import TestRailService
    from datetime import datetime

    try:
        # Initialize TestRail service (uses all configured suites)
        suite_ids = current_app.config.get('TESTRAIL_SUITE_IDS') or [current_app.config.get('TESTRAIL_SUITE_ID')]
        tr_service = TestRailService(
            current_app.config.get('TESTRAIL_URL'),
            current_app.config.get('TESTRAIL_EMAIL'),
            current_app.config.get('TESTRAIL_API_KEY'),
            suite_ids
        )

        # Get all TestRail case IDs from database
        testrail_cases = TestRailCase.query.all()
        valid_case_ids = set()
        for case in testrail_cases:
            # Store both with and without 'C' prefix
            case_id_str = str(case.case_id).upper()
            valid_case_ids.add(case_id_str)
            valid_case_ids.add(case_id_str.replace('C', ''))

        # Get all tests with TestRail IDs
        tests = Test.query.filter(Test.testrail_case_id.isnot(None)).all()

        validated_count = 0
        deleted_count = 0
        valid_count = 0
        partial_count = 0

        for test in tests:
            if not test.testrail_case_id:
                continue

            # Parse multiple TestRail IDs (comma-separated)
            testrail_ids = [tid.strip() for tid in test.testrail_case_id.split(',')]
            valid_ids = []
            invalid_ids = []

            for tid in testrail_ids:
                tid_upper = tid.upper()
                # Check if the ID exists in our valid set
                if tid_upper in valid_case_ids or tid_upper.replace('C', '') in valid_case_ids:
                    valid_ids.append(tid)
                else:
                    invalid_ids.append(tid)

            # Update test status based on validation results
            if len(valid_ids) == len(testrail_ids):
                # All IDs are valid
                test.testrail_status = 'valid'
                valid_count += 1
            elif len(valid_ids) > 0:
                # Some IDs are valid, some are not (partial match)
                # This is acceptable for parametrized tests
                test.testrail_status = 'valid'
                valid_count += 1
                logger.info(f"Test {test.test_name} has partial validation: {len(valid_ids)}/{len(testrail_ids)} IDs found")
            else:
                # No valid IDs found - all are deleted/missing
                test.testrail_status = 'deleted'
                deleted_count += 1

            test.testrail_validated_at = datetime.utcnow()
            validated_count += 1

        # Commit changes
        db.session.commit()

        logger.info(f"Validated {validated_count} tests: {valid_count} valid, {deleted_count} with deleted TestRail IDs")

        return jsonify({
            'status': 'success',
            'validated': validated_count,
            'valid': valid_count,
            'deleted': deleted_count
        })

    except Exception as e:
        logger.error(f"Error validating TestRail IDs: {e}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500



