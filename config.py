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
    TESTRAIL_SUITE_ID = os.environ.get('TESTRAIL_SUITE_ID', '1')

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

