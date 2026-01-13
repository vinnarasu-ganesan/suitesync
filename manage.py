"""
Flask-Migrate migration commands.

Usage:
    flask db init      - Initialize migrations directory
    flask db migrate   - Generate migration script
    flask db upgrade   - Apply migrations
    flask db downgrade - Revert migrations
"""

from flask_migrate import Migrate
from app import create_app
from models import db

app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    app.run()

