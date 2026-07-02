import logging
from datetime import datetime
from sqlalchemy import or_
from models import db, Test, TestRailCase, TestRailSection, SyncLog
from services.git_service import GitService
from services.pytest_parser import PytestParser
from services.testrail_service import TestRailService

logger = logging.getLogger(__name__)


class SyncService:
    """Service for synchronizing tests between Git repository and TestRail."""

    def __init__(self, config):
        self.config = config
        self.git_service = GitService(
            config.get('GIT_REPO_URL'),
            config.get('GIT_CLONE_PATH'),
            config.get('GIT_BRANCH'),
            username=config.get('GITHUB_USERNAME'),
            token=config.get('GITHUB_TOKEN')
        )

        if config.get('TESTRAIL_URL') and config.get('TESTRAIL_EMAIL') and config.get('TESTRAIL_API_KEY'):
            # Prefer the multi-suite list; fall back to the legacy single-ID key
            suite_ids = config.get('TESTRAIL_SUITE_IDS') or [config.get('TESTRAIL_SUITE_ID')]
            self.testrail_service = TestRailService(
                config.get('TESTRAIL_URL'),
                config.get('TESTRAIL_EMAIL'),
                config.get('TESTRAIL_API_KEY'),
                suite_ids
            )
        else:
            self.testrail_service = None
            logger.warning("TestRail credentials not configured")

    def sync_tests(self, sync_type='manual'):
        """Perform a full synchronization of tests."""
        sync_log = SyncLog(
            sync_type=sync_type,
            status='in_progress',
            started_at=datetime.utcnow()
        )
        db.session.add(sync_log)
        db.session.commit()

        try:
            # Step 1: Clone or update repository
            logger.info("Cloning/updating Git repository...")
            if not self.git_service.clone_or_update():
                sync_log.status = 'failed'
                sync_log.message = 'Failed to clone/update repository'
                sync_log.completed_at = datetime.utcnow()
                db.session.commit()
                return sync_log

            sync_log.commit_hash = self.git_service.get_current_commit_hash()
            sync_log.branch = self.git_service.get_current_branch()
            db.session.commit()

            # Step 2: Parse test files
            logger.info("Parsing test files...")
            tests = PytestParser.parse_repository(self.git_service)
            sync_log.tests_found = len(tests)
            db.session.commit()

            # Step 3: Sync tests with database
            logger.info(f"Syncing {len(tests)} tests with database...")
            tests_synced = 0
            tests_failed = 0

            for test_data in tests:
                try:
                    test = Test.query.filter_by(test_id=test_data['test_id']).first()

                    if test:
                        # Update existing test
                        test.test_name = test_data['test_name']
                        test.test_file = test_data['test_file']
                        test.test_class = test_data['test_class']
                        test.description = test_data['description']
                        test.markers = test_data.get('markers', [])
                        test.testrail_case_id = test_data['testrail_case_id']
                        test.updated_at = datetime.utcnow()
                    else:
                        # Create new test
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

                    tests_synced += 1

                except Exception as e:
                    logger.error(f"Error syncing test {test_data['test_id']}: {e}")
                    tests_failed += 1

            db.session.commit()

            # Step 4: Sync with TestRail if configured
            if self.testrail_service:
                logger.info("Syncing with TestRail...")
                self._sync_with_testrail()

            # Step 5: Mark old tests as archived
            self._archive_missing_tests(tests)

            # Update sync log
            sync_log.status = 'success'
            sync_log.tests_synced = tests_synced
            sync_log.tests_failed = tests_failed
            sync_log.message = f'Successfully synced {tests_synced} tests'
            sync_log.completed_at = datetime.utcnow()
            db.session.commit()

            logger.info(f"Sync completed: {tests_synced} synced, {tests_failed} failed")
            return sync_log

        except Exception as e:
            logger.error(f"Sync error: {e}")
            sync_log.status = 'failed'
            sync_log.message = str(e)
            sync_log.completed_at = datetime.utcnow()
            db.session.commit()
            return sync_log

    def _sync_with_testrail(self):
        """Sync test information with TestRail for all configured suites."""
        try:
            suite_ids = self.testrail_service.suite_ids

            # ── Resolve per-suite section filters ──────────────────────────────
            # Primary source: TESTRAIL_SUITE_SECTION_MAP  e.g. {'206374': ['1867685']}
            suite_section_map = dict(self.config.get('TESTRAIL_SUITE_SECTION_MAP') or {})

            # Legacy fallback: TESTRAIL_SECTION_IDS is only honoured when there
            # is exactly ONE suite configured AND the explicit map is not set.
            # With multiple suites it is impossible to know which suite the
            # section belongs to, so the legacy variable is intentionally ignored.
            legacy_section_ids = self.config.get('TESTRAIL_SECTION_IDS') or []
            if legacy_section_ids and not suite_section_map:
                if len(suite_ids) == 1:
                    suite_section_map[suite_ids[0]] = legacy_section_ids
                    logger.info(
                        f"Using TESTRAIL_SECTION_IDS={legacy_section_ids} "
                        f"for the single configured suite {suite_ids[0]}"
                    )
                else:
                    logger.warning(
                        "TESTRAIL_SECTION_IDS is set but multiple suites are configured "
                        f"({suite_ids}). Cannot determine which suite owns the section(s) "
                        f"{legacy_section_ids}. Use TESTRAIL_SUITE_SECTION_MAP instead "
                        "(e.g. TESTRAIL_SUITE_SECTION_MAP=206374:1867685). "
                        "Falling back to full sync for all suites."
                    )

            logger.info(
                f"Syncing {len(suite_ids)} TestRail suite(s): {suite_ids} | "
                f"Section filter map: {suite_section_map if suite_section_map else 'none (full sync)'}"
            )

            for suite_id in suite_ids:
                section_ids_for_suite = suite_section_map.get(str(suite_id)) or []
                if section_ids_for_suite:
                    logger.info(
                        f"[Suite {suite_id}] Section-scoped sync: "
                        f"collecting only section(s) {section_ids_for_suite}"
                    )
                    # Collect all allowed section IDs across every configured root
                    # section so the post-sync out-of-scope cleanup knows exactly
                    # which sections are in scope for this suite.
                    combined_allowed_section_ids: set = set()
                    for section_id in section_ids_for_suite:
                        allowed = self._sync_suite(suite_id, section_id=section_id)
                        if allowed:
                            combined_allowed_section_ids.update(allowed)

                    # Remove cases that belong to sections outside the configured
                    # subtrees.  These are typically left over from a previous
                    # full-suite sync and would otherwise never be cleaned up.
                    if combined_allowed_section_ids:
                        self._cleanup_out_of_scope_cases(suite_id, combined_allowed_section_ids)
                else:
                    logger.info(f"[Suite {suite_id}] Full suite sync (no section filter)")
                    self._sync_suite(suite_id)

        except Exception as e:
            logger.error(f"Error syncing with TestRail: {e}")

    @staticmethod
    def _resolve_descendant_section_ids(sections_list, root_section_id):
        """Return a set of section IDs that are the root section itself plus all
        of its descendants (children, grandchildren, …).

        The TestRail API ``get_cases?section_id=X`` only returns cases directly
        inside section X and does NOT recurse into sub-sections.  We therefore
        resolve the full sub-tree here and filter cases in Python.

        Args:
            sections_list: List of section dicts as returned by ``get_sections``.
            root_section_id: The top-level section/group ID whose subtree we want
                             (string or int).
        Returns:
            set of string section IDs (including root_section_id itself).
        """
        root = str(root_section_id)

        # Build parent_id → [child_section_id] map
        children: dict = {}
        for s in sections_list:
            parent_raw = s.get('parent_id')
            parent_id = str(parent_raw) if parent_raw not in (None, '') else None
            child_id = str(s.get('id', ''))
            children.setdefault(parent_id, []).append(child_id)

        # BFS / DFS from root
        resolved: set = set()
        stack = [root]
        while stack:
            sid = stack.pop()
            if sid in resolved:
                continue
            resolved.add(sid)
            stack.extend(children.get(sid, []))

        return resolved

    def _sync_suite(self, suite_id, section_id=None):
        """Sync a single TestRail suite (or a specific section subtree) into the database.

        Args:
            suite_id: TestRail suite ID to sync.
            section_id: Optional parent section/group ID.  When given, ALL cases
                whose section is the root section **or any of its descendants**
                are collected.  The resolution is done on the full sections list
                already fetched, so no extra API calls are needed.

                Note: The TestRail ``get_cases?section_id=X`` API filter only
                returns cases directly in section X (it does not recurse).  We
                therefore fetch all cases for the suite and filter in Python.

        Returns:
            set: The resolved set of allowed section IDs used for this sync
                 (includes root + all descendants).  Empty set for a full-suite
                 sync (no section filter).  The caller uses this to build the
                 combined in-scope set for post-sync out-of-scope cleanup.
        """
        try:
            scope_label = (
                f"[Suite {suite_id}]" if not section_id
                else f"[Suite {suite_id} / Section {section_id}]"
            )

            # --- Suite info ---
            logger.info(f"{scope_label} Fetching suite information...")
            suite_info = self.testrail_service.get_suite(suite_id)
            suite_name = (
                suite_info.get('name', f'Suite {suite_id}') if suite_info else f'Suite {suite_id}'
            )
            logger.info(f"{scope_label} Suite name: {suite_name}")

            # --- Sections ---
            logger.info(f"{scope_label} Fetching sections...")
            sections_response = self.testrail_service.get_sections(suite_id)
            sections_list = []
            sections_map = {}
            if sections_response:
                sections_list = (
                    sections_response if isinstance(sections_response, list)
                    else sections_response.get('sections', [])
                )
                for section in sections_list:
                    sid = str(section.get('id', ''))
                    sections_map[sid] = section.get('name', f'Section {sid}')

                    parent_raw = section.get('parent_id')
                    parent_id = str(parent_raw) if parent_raw not in (None, '') else None
                    db_section = TestRailSection.query.filter_by(section_id=sid).first()
                    if db_section:
                        db_section.name = section.get('name', f'Section {sid}')
                        db_section.parent_id = parent_id
                        db_section.suite_id = str(suite_id)
                        db_section.suite_name = suite_name
                        db_section.updated_at = datetime.utcnow()
                    else:
                        db.session.add(TestRailSection(
                            section_id=sid,
                            name=section.get('name', f'Section {sid}'),
                            parent_id=parent_id,
                            suite_id=str(suite_id),
                            suite_name=suite_name
                        ))
            logger.info(f"{scope_label} Found {len(sections_map)} sections")

            # --- Resolve descendant section IDs when a parent section is given ---
            # The TestRail API get_cases?section_id=X does NOT recurse into
            # subsections, so we resolve the full subtree ourselves and filter
            # cases in Python after fetching all cases for the suite.
            allowed_section_ids: set = set()   # empty = no filter (sync all)
            section_scoped = False
            if section_id:
                allowed_section_ids = self._resolve_descendant_section_ids(
                    sections_list, section_id
                )
                section_scoped = True
                # Log the resolved sub-sections so it is easy to verify
                resolved_names = [
                    f"{sid}({sections_map.get(sid, '?')})"
                    for sid in sorted(allowed_section_ids)
                ]
                logger.info(
                    f"{scope_label} Resolved {len(allowed_section_ids)} section(s) "
                    f"in subtree of {section_id}: {resolved_names}"
                )

            # --- Cases (always fetch all for the suite; filter below) ---
            logger.info(f"{scope_label} Fetching all cases for suite {suite_id}...")
            # Do NOT pass section_id to the API – it only matches the root section
            # and ignores descendants.  We filter in Python instead.
            response = self.testrail_service.get_cases(suite_id)
            if not response:
                logger.warning(f"{scope_label} No cases retrieved from TestRail")
                return allowed_section_ids

            if isinstance(response, dict) and 'cases' in response:
                all_cases = response['cases']
            elif isinstance(response, list):
                all_cases = response
            else:
                logger.error(f"{scope_label} Unexpected response format: {type(response)}")
                return allowed_section_ids

            logger.info(f"{scope_label} Total cases in suite: {len(all_cases)}")

            # Apply subtree filter when a parent section was requested
            if section_scoped:
                cases = [
                    c for c in all_cases
                    if str(c.get('section_id', '')) in allowed_section_ids
                ]
                logger.info(
                    f"{scope_label} After subtree filter: {len(cases)} case(s) "
                    f"(discarded {len(all_cases) - len(cases)} from other sections)"
                )
            else:
                cases = all_cases

            # Track case IDs fetched for THIS suite/section (used for cleanup)
            current_case_ids = set()

            for case in cases:
                case_id = f"C{case['id']}"
                current_case_ids.add(case_id)
                section_id_val = str(case.get('section_id', ''))
                section_name = sections_map.get(section_id_val, f'Section {section_id_val}')

                custom_fields = {k: v for k, v in case.items() if k.startswith('custom_')}

                testrail_case = TestRailCase.query.filter_by(case_id=case_id).first()
                if testrail_case:
                    testrail_case.title = case['title']
                    testrail_case.section_id = section_id_val
                    testrail_case.section_name = section_name
                    testrail_case.suite_id = str(case.get('suite_id', suite_id))
                    testrail_case.suite_name = suite_name
                    testrail_case.type_id = case.get('type_id')
                    testrail_case.priority_id = case.get('priority_id')
                    testrail_case.custom_fields = custom_fields
                    testrail_case.updated_at = datetime.utcnow()
                else:
                    testrail_case = TestRailCase(
                        case_id=case_id,
                        title=case['title'],
                        section_id=section_id_val,
                        section_name=section_name,
                        suite_id=str(case.get('suite_id', suite_id)),
                        suite_name=suite_name,
                        type_id=case.get('type_id'),
                        priority_id=case.get('priority_id'),
                        custom_fields=custom_fields
                    )
                    db.session.add(testrail_case)

            # --- Per-suite cleanup ---
            # Full suite sync: remove DB cases no longer in TestRail.
            # Section-scoped sync: only clean up cases inside the resolved subtree
            # so that cases from OTHER sections in the same suite are untouched.
            #
            # NOTE: We intentionally do NOT filter by suite_id alone in the DB
            # query because older records (written before suite_id tracking was
            # introduced, or before a migration) may have suite_id=NULL.  Those
            # stale rows would be silently skipped and never cleaned up.
            # Instead we rely on section_id (which is globally unique in TestRail)
            # for section-scoped syncs, and for full-suite syncs we also include
            # NULL-suite_id rows whose section_id is known to belong to this suite.
            if not section_scoped:
                # Full suite – collect all section IDs that belong to this suite
                suite_section_ids = list(sections_map.keys())
                # Include rows whose suite_id matches OR whose suite_id is NULL
                # but whose section_id is one of this suite's sections (legacy rows).
                db_cases_for_suite = TestRailCase.query.filter(
                    or_(
                        TestRailCase.suite_id == str(suite_id),
                        db.and_(
                            TestRailCase.suite_id.is_(None),
                            TestRailCase.section_id.in_(suite_section_ids)
                        )
                    )
                ).all()
                deleted_count = 0
                for db_case in db_cases_for_suite:
                    if db_case.case_id not in current_case_ids:
                        logger.info(
                            f"{scope_label} Removing case {db_case.case_id} "
                            f"({db_case.title}) – no longer exists in TestRail"
                        )
                        db.session.delete(db_case)
                        deleted_count += 1
            else:
                # Section-scoped – only clean up within the resolved subtree.
                # Use section_id as the sole filter: TestRail section IDs are
                # globally unique so there is no risk of touching cases from
                # other suites.  This also catches legacy rows where suite_id
                # was not stored (NULL) and would therefore be missed by a
                # suite_id equality check.
                deleted_count = 0
                db_cases_in_subtree = TestRailCase.query.filter(
                    TestRailCase.section_id.in_(list(allowed_section_ids))
                ).all()
                for db_case in db_cases_in_subtree:
                    if db_case.case_id not in current_case_ids:
                        logger.info(
                            f"{scope_label} Removing case {db_case.case_id} "
                            f"({db_case.title}) – no longer in subtree"
                        )
                        db.session.delete(db_case)
                        deleted_count += 1

            db.session.commit()
            logger.info(
                f"{scope_label} Sync complete – "
                f"{len(cases)} cases upserted, {deleted_count} obsolete cases removed."
            )
            return allowed_section_ids

        except Exception as e:
            logger.error(f"[Suite {suite_id}] Error syncing suite: {e}")
            return set()

    def _cleanup_out_of_scope_cases(self, suite_id, combined_allowed_section_ids: set):
        """Remove DB cases for *suite_id* whose section is no longer in scope.

        When the sync configuration switches from a full-suite sync to a
        section-scoped sync (or when the configured section filter changes),
        cases from sections that are now outside the configured subtrees remain
        in the DB indefinitely.  This method removes them.

        It is called from ``_sync_with_testrail`` after ALL configured section
        syncs for a suite have completed, so ``combined_allowed_section_ids``
        contains the union of every resolved subtree for that suite.

        Args:
            suite_id: TestRail suite ID.
            combined_allowed_section_ids: Set of section ID strings that are
                in-scope for this suite (all configured subtrees combined).
        """
        scope_label = f"[Suite {suite_id}]"
        try:
            # After a section-scoped sync the DB may still contain cases from
            # sections outside the configured subtrees (e.g. left over from an
            # earlier full-suite sync or a previously wider section filter).
            # Delete every case whose suite_id matches this suite but whose
            # section_id is NOT in the combined in-scope set.
            all_db_cases_for_suite = TestRailCase.query.filter(
                TestRailCase.suite_id == str(suite_id)
            ).all()

            deleted_count = 0
            for db_case in all_db_cases_for_suite:
                if str(db_case.section_id) not in combined_allowed_section_ids:
                    logger.info(
                        f"{scope_label} Removing out-of-scope case {db_case.case_id} "
                        f"({db_case.title}) from section {db_case.section_id} "
                        f"– not in any configured subtree"
                    )
                    db.session.delete(db_case)
                    deleted_count += 1

            if deleted_count:
                db.session.commit()
                logger.info(
                    f"{scope_label} Out-of-scope cleanup complete – "
                    f"{deleted_count} cases removed (were outside configured section subtree(s))."
                )
            else:
                logger.info(f"{scope_label} Out-of-scope cleanup: no stale cases found.")

        except Exception as e:
            logger.error(f"{scope_label} Error during out-of-scope cleanup: {e}")
            db.session.rollback()

    def _archive_missing_tests(self, current_tests):
        """Mark tests that are no longer in the repository as archived."""
        current_test_ids = {test['test_id'] for test in current_tests}
        active_tests = Test.query.filter_by(status='active').all()

        archived_count = 0
        for test in active_tests:
            if test.test_id not in current_test_ids:
                test.status = 'archived'
                test.updated_at = datetime.utcnow()
                archived_count += 1

        if archived_count > 0:
            db.session.commit()
            logger.info(f"Archived {archived_count} tests")

    def get_sync_status(self):
        """Get the status of the last sync operation."""
        last_sync = SyncLog.query.order_by(SyncLog.started_at.desc()).first()
        return last_sync.to_dict() if last_sync else None

