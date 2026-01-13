import os
import logging
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from config import config
from models import db
from routes.api import api_bp
from routes.web import web_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

migrate = Migrate()


def create_app(config_name=None):
    """Application factory pattern."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # Register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(web_bp)

    # Create database tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables created")

    # Run initial sync if configured
    if app.config['SYNC_ON_STARTUP']:
        with app.app_context():
            try:
                from services.sync_service import SyncService
                sync_service = SyncService(app.config)
                sync_service.sync_tests(sync_type='startup')
                logger.info("Initial sync completed")
            except Exception as e:
                logger.error(f"Error during initial sync: {e}")

    logger.info(f"Application started in {config_name} mode")
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

