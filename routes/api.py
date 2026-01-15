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
                Test.test_file.ilike(search_term)
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
    testrail_case = None
    if test.testrail_case_id:
        testrail_case = TestRailCase.query.filter_by(
            case_id=test.testrail_case_id
        ).first()

    result = test.to_dict()
    if testrail_case:
        result['testrail_case'] = testrail_case.to_dict()

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
        search = request.args.get('search', type=str)

        # Build query with filters
        query = TestRailCase.query

        # Apply filters
        if suite_id:
            query = query.filter(TestRailCase.suite_id == suite_id)
        if section_id:
            query = query.filter(TestRailCase.section_id == section_id)
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

        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        # Optimize: Create lightweight dict without custom_fields to reduce payload size
        cases_data = []
        for case in pagination.items:
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
                # Exclude custom_fields to reduce data transfer
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
    """Get TestRail cases statistics."""
    from sqlalchemy import func

    total_cases = TestRailCase.query.count()

    # Get unique sections count
    unique_sections = db.session.query(func.count(func.distinct(TestRailCase.section_id))).scalar()

    # Get unique suites count
    unique_suites = db.session.query(func.count(func.distinct(TestRailCase.suite_id))).scalar()

    # Get cases by priority
    priorities = db.session.query(
        TestRailCase.priority_id,
        func.count(TestRailCase.id)
    ).group_by(TestRailCase.priority_id).all()

    priority_breakdown = {str(p[0]): p[1] for p in priorities if p[0]}

    # Get cases by type
    types = db.session.query(
        TestRailCase.type_id,
        func.count(TestRailCase.id)
    ).group_by(TestRailCase.type_id).all()

    type_breakdown = {str(t[0]): t[1] for t in types if t[0]}

    return jsonify({
        'total_cases': total_cases,
        'unique_sections': unique_sections,
        'unique_suites': unique_suites,
        'priority_breakdown': priority_breakdown,
        'type_breakdown': type_breakdown
    })


@api_bp.route('/testrail/filters', methods=['GET'])
def get_testrail_filters():
    """Get unique values for TestRail filters."""
    from sqlalchemy import func

    # Get unique suite IDs with their names
    suites = db.session.query(
        TestRailCase.suite_id,
        TestRailCase.suite_name
    ).distinct().filter(TestRailCase.suite_id.isnot(None)).all()
    suite_options = [{'value': s[0], 'label': s[1] if s[1] else f'Suite {s[0]}'} for s in suites]

    # Get unique section IDs with their names and counts
    sections = db.session.query(
        TestRailCase.section_id,
        TestRailCase.section_name,
        func.count(TestRailCase.id)
    ).filter(TestRailCase.section_id.isnot(None)).group_by(
        TestRailCase.section_id,
        TestRailCase.section_name
    ).order_by(TestRailCase.section_name).all()
    section_options = [{'value': s[0], 'label': f'{s[1] if s[1] else "Section " + s[0]} ({s[2]} cases)'} for s in sections]

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
        # Initialize TestRail service
        tr_service = TestRailService(
            current_app.config.get('TESTRAIL_URL'),
            current_app.config.get('TESTRAIL_EMAIL'),
            current_app.config.get('TESTRAIL_API_KEY'),
            current_app.config.get('TESTRAIL_SUITE_ID')
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

        for test in tests:
            if not test.testrail_case_id:
                continue

            # Parse multiple TestRail IDs (comma-separated)
            testrail_ids = [tid.strip() for tid in test.testrail_case_id.split(',')]
            all_valid = True

            for tid in testrail_ids:
                tid_upper = tid.upper()
                # Check if the ID exists in our valid set
                if tid_upper not in valid_case_ids and tid_upper.replace('C', '') not in valid_case_ids:
                    all_valid = False
                    break

            # Update test status
            if all_valid:
                test.testrail_status = 'valid'
                valid_count += 1
            else:
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



