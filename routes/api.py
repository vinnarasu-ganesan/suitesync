from flask import Blueprint, jsonify, request, current_app
from models import db, Test, TestRailCase, SyncLog
from services.sync_service import SyncService
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/tests', methods=['GET'])
def get_tests():
    """Get all tests with optional filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    status = request.args.get('status', 'active')
    search = request.args.get('search', '')

    query = Test.query

    if status:
        query = query.filter_by(status=status)

    if search:
        query = query.filter(
            db.or_(
                Test.test_id.contains(search),
                Test.test_name.contains(search),
                Test.test_file.contains(search)
            )
        )

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

    return jsonify({
        'total_tests': total_tests,
        'active_tests': active_tests,
        'archived_tests': archived_tests,
        'tests_with_testrail': tests_with_testrail,
        'tests_without_testrail': tests_without_testrail
    })


@api_bp.route('/testrail/cases', methods=['GET'])
def get_testrail_cases():
    """Get all TestRail cases with filtering and sorting."""
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
        query = query.filter(
            db.or_(
                TestRailCase.case_id.contains(search),
                TestRailCase.title.contains(search)
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

    return jsonify({
        'cases': [case.to_dict() for case in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    })


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

    # Get unique suite IDs
    suites = db.session.query(
        TestRailCase.suite_id
    ).distinct().filter(TestRailCase.suite_id.isnot(None)).all()
    suite_options = [{'value': s[0], 'label': f'Suite {s[0]}'} for s in suites]

    # Get unique section IDs with counts
    sections = db.session.query(
        TestRailCase.section_id,
        func.count(TestRailCase.id)
    ).filter(TestRailCase.section_id.isnot(None)).group_by(
        TestRailCase.section_id
    ).order_by(TestRailCase.section_id).all()
    section_options = [{'value': s[0], 'label': f'Section {s[0]} ({s[1]} cases)'} for s in sections]

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
    """Get section and suite names from TestRail API."""
    from services.testrail_service import TestRailService

    try:
        # Initialize TestRail service
        tr_service = TestRailService(
            current_app.config.get('TESTRAIL_URL'),
            current_app.config.get('TESTRAIL_EMAIL'),
            current_app.config.get('TESTRAIL_API_KEY'),
            current_app.config.get('TESTRAIL_SUITE_ID')
        )

        # Get sections
        sections_response = tr_service.get_sections()
        sections_map = {}
        if sections_response:
            for section in sections_response:
                sections_map[str(section.get('id'))] = section.get('name', f"Section {section.get('id')}")

        # Get suite info
        suite = tr_service.get_suite()
        suites_map = {}
        if suite:
            suites_map[str(suite.get('id'))] = suite.get('name', f"Suite {suite.get('id')}")

        return jsonify({
            'sections': sections_map,
            'suites': suites_map
        })
    except Exception as e:
        logger.error(f"Error fetching TestRail names: {e}")
        return jsonify({
            'sections': {},
            'suites': {}
        })


@api_bp.route('/sync', methods=['POST'])
def trigger_sync():
    """Trigger a manual synchronization."""
    try:
        sync_service = SyncService(current_app.config)
        sync_log = sync_service.sync_tests(sync_type='manual')

        return jsonify({
            'status': 'success',
            'sync_log': sync_log.to_dict()
        })
    except Exception as e:
        logger.error(f"Error triggering sync: {e}")
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

