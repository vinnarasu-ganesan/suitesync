from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Test(db.Model):
    """Model representing a pytest test case."""

    __tablename__ = 'tests'

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    test_name = db.Column(db.String(500), nullable=False)
    test_file = db.Column(db.String(500), nullable=False)
    test_class = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    markers = db.Column(db.JSON, nullable=True)  # List of pytest markers (e.g., ['always', 'run', 'testrail'])
    testrail_case_id = db.Column(db.String(50), nullable=True, index=True)
    testrail_status = db.Column(db.String(50), default='unknown')  # valid, deleted, unknown
    testrail_validated_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), default='active')  # active, archived, deleted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sync_logs = db.relationship('SyncLog', backref='test', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Test {self.test_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'test_id': self.test_id,
            'test_name': self.test_name,
            'test_file': self.test_file,
            'test_class': self.test_class,
            'description': self.description,
            'markers': self.markers or [],
            'testrail_case_id': self.testrail_case_id,
            'testrail_status': self.testrail_status,
            'testrail_validated_at': self.testrail_validated_at.isoformat() if self.testrail_validated_at else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TestRailCase(db.Model):
    """Model representing a TestRail test case."""

    __tablename__ = 'testrail_cases'

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    title = db.Column(db.String(500), nullable=False)
    section_id = db.Column(db.String(50), nullable=True)
    suite_id = db.Column(db.String(50), nullable=True)
    type_id = db.Column(db.Integer, nullable=True)
    priority_id = db.Column(db.Integer, nullable=True)
    custom_fields = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<TestRailCase {self.case_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'case_id': self.case_id,
            'title': self.title,
            'section_id': self.section_id,
            'suite_id': self.suite_id,
            'type_id': self.type_id,
            'priority_id': self.priority_id,
            'custom_fields': self.custom_fields,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SyncLog(db.Model):
    """Model representing a synchronization log entry."""

    __tablename__ = 'sync_logs'

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=True)
    sync_type = db.Column(db.String(50), nullable=False)  # full, incremental, webhook
    status = db.Column(db.String(50), nullable=False)  # success, failed, in_progress
    message = db.Column(db.Text, nullable=True)
    commit_hash = db.Column(db.String(40), nullable=True)
    branch = db.Column(db.String(100), nullable=True)
    tests_found = db.Column(db.Integer, default=0)
    tests_synced = db.Column(db.Integer, default=0)
    tests_failed = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<SyncLog {self.id} - {self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'test_id': self.test_id,
            'sync_type': self.sync_type,
            'status': self.status,
            'message': self.message,
            'commit_hash': self.commit_hash,
            'branch': self.branch,
            'tests_found': self.tests_found,
            'tests_synced': self.tests_synced,
            'tests_failed': self.tests_failed,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

