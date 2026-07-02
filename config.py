import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """Base configuration."""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.join(basedir, "suitesync.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Git Repository
    GIT_REPO_URL = os.environ.get('GIT_REPO_URL', 'https://github.com/glcp/vme-test-repo')
    GIT_CLONE_PATH = os.environ.get('GIT_CLONE_PATH', os.path.join(basedir, 'repos', 'vme-test-repo'))
    GIT_BRANCH = os.environ.get('GIT_BRANCH', 'main')

    # GitHub Authentication (Optional - for private repos)
    GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME', '')
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')  # Personal Access Token or Password

    # TestRail
    TESTRAIL_URL = os.environ.get('TESTRAIL_URL', '')
    TESTRAIL_EMAIL = os.environ.get('TESTRAIL_EMAIL', '')
    TESTRAIL_API_KEY = os.environ.get('TESTRAIL_API_KEY', '')

    # Multi-suite support: TESTRAIL_SUITE_IDS takes a comma-separated list of suite IDs.
    # Falls back to the legacy TESTRAIL_SUITE_ID for single-suite deployments.
    _suite_ids_raw = os.environ.get('TESTRAIL_SUITE_IDS') or os.environ.get('TESTRAIL_SUITE_ID', '1')
    TESTRAIL_SUITE_IDS = [sid.strip() for sid in _suite_ids_raw.split(',') if sid.strip()]
    # Primary / default suite ID kept for backward compatibility
    TESTRAIL_SUITE_ID = TESTRAIL_SUITE_IDS[0] if TESTRAIL_SUITE_IDS else '1'

    # ── Suite-to-section mapping (RECOMMENDED for multi-suite deployments) ──────
    #
    # TESTRAIL_SUITE_SECTION_MAP explicitly ties a section/group ID to the suite
    # it belongs to, so the framework knows exactly which suite to filter when
    # syncing.  Suites listed in TESTRAIL_SUITE_IDS that are NOT mentioned here
    # are synced in full (no section filter).
    #
    # Format:  <suite_id>:<section_id1>,<section_id2>;<suite_id>:<section_id>
    # Example: collect only "PCBE+VME System test" (section 1867685) from suite
    #          206374, while suites 126845 and 257515 are fully synced:
    #
    #   TESTRAIL_SUITE_SECTION_MAP=206374:1867685
    #
    # Multiple sections for the same suite:
    #   TESTRAIL_SUITE_SECTION_MAP=206374:1867685,1867700
    #
    # Multiple suites, each with their own section filter:
    #   TESTRAIL_SUITE_SECTION_MAP=206374:1867685;257515:9876543
    #
    _suite_section_map_raw = os.environ.get('TESTRAIL_SUITE_SECTION_MAP', '')
    TESTRAIL_SUITE_SECTION_MAP: dict = {}
    if _suite_section_map_raw:
        for _entry in _suite_section_map_raw.split(';'):
            _entry = _entry.strip()
            if ':' in _entry:
                _suite_part, _sections_part = _entry.split(':', 1)
                _suite_key = _suite_part.strip()
                _sections = [s.strip() for s in _sections_part.split(',') if s.strip()]
                if _suite_key:
                    TESTRAIL_SUITE_SECTION_MAP[_suite_key] = _sections

    # ── Legacy single-suite section filter (kept for backward compatibility) ──
    #
    # TESTRAIL_SECTION_IDS is honoured ONLY when exactly ONE suite is configured
    # AND TESTRAIL_SUITE_SECTION_MAP is not set.  For multi-suite setups always
    # use TESTRAIL_SUITE_SECTION_MAP instead.
    _section_ids_raw = os.environ.get('TESTRAIL_SECTION_IDS', '')
    TESTRAIL_SECTION_IDS = [sid.strip() for sid in _section_ids_raw.split(',') if sid.strip()]

    # GitHub Webhook
    GITHUB_WEBHOOK_SECRET = os.environ.get('GITHUB_WEBHOOK_SECRET', '')

    # Redis
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    # Celery
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL

    # Application
    SYNC_ON_STARTUP = os.environ.get('SYNC_ON_STARTUP', 'false').lower() == 'true'
    AUTO_SYNC_INTERVAL = int(os.environ.get('AUTO_SYNC_INTERVAL', 3600))

    # TestRail sections (folders) whose cases are excluded from automation
    # status distribution and coverage calculations. Matching is done on a
    # normalized name (case/space/dash-insensitive) and includes all
    # descendant subsections. Comma-separated env override supported.
    _excluded_sections_raw = os.environ.get(
        'TESTRAIL_EXCLUDED_SECTIONS', 'Archived,To-Be-Deleted'
    )
    EXCLUDED_SECTION_NAMES = [
        name.strip() for name in _excluded_sections_raw.split(',') if name.strip()
    ]


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

