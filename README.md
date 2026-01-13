# SuiteSync - Test Management & TestRail Synchronization
For issues and questions, please open an issue on GitHub.

## Support

MIT License - See LICENSE file for details

## License

4. Submit a pull request
3. Make your changes
2. Create a feature branch
1. Fork the repository

## Contributing

- Run migrations if schema changes
- Ensure database file/server is accessible
- Check database connection string
### Database Issues

- Ensure API is enabled in TestRail
- Check project ID
- Verify TestRail URL, email, and API key
### TestRail Connection Issues

- Verify network connectivity
- Check repository URL and credentials
- Ensure Git is installed and accessible
### Git Clone Issues

## Troubleshooting

```
docker run -p 5000:5000 --env-file .env suitesync
docker build -t suitesync .
```bash
Build and run:

```
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
EXPOSE 5000

COPY . .

RUN pip install -r requirements.txt
COPY requirements.txt .
WORKDIR /app

FROM python:3.9-slim
```dockerfile
Create a `Dockerfile`:

### Using Docker

```
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```bash

### Using Gunicorn

## Deployment

- **Static**: Frontend assets (CSS, JavaScript)
- **Templates**: Jinja2 templates for web pages
- **Models**: Database models using SQLAlchemy
- **Routes**: API and web endpoints
- **Services**: Business logic for Git, TestRail, and sync operations

### Code Structure

```
pytest
```bash

### Running Tests

The application will run on `http://localhost:5000` with debug mode enabled.

```
python app.py
```bash

### Running in Development Mode

## Development

- Fields: sync_type, status, message, commit_hash, branch, tests_found, tests_synced, tests_failed
- Tracks synchronization operations
### SyncLog

- Fields: case_id, title, section_id, suite_id, type_id, priority_id, custom_fields
- Represents a TestRail test case
### TestRailCase

- Fields: test_id, test_name, test_file, test_class, description, testrail_case_id, status
- Represents a pytest test case
### Test

## Database Models

- `POST /api/webhook/github` - GitHub webhook endpoint

### Webhook

- `GET /api/sync/logs` - Get sync history
- `GET /api/sync/status` - Get last sync status
- `POST /api/sync` - Trigger manual synchronization

### Sync

- `GET /api/testrail/cases` - Get all TestRail cases

### TestRail

- `GET /api/tests/stats` - Get test statistics
- `GET /api/tests/<id>` - Get specific test
- `GET /api/tests` - Get all tests (with pagination)

### Tests

## API Endpoints

```
    pass
    """
    TestRail Case: C789
    Test description.
    """
def test_with_docstring():
# In docstring

    pass
def test_another_example():
@pytest.mark.testrail_id('C456')
# Using pytest marker with alternative name

    pass
def test_example():
@pytest.mark.testrail('C123')
# Using pytest marker

import pytest
```python

Tests should include TestRail case IDs using one of these formats:

### TestRail Case ID Format

3. When code is merged to the main branch, sync will trigger automatically

   - **Events**: Select "Just the push event"
   - **Secret**: Your `GITHUB_WEBHOOK_SECRET`
   - **Content type**: `application/json`
   - **Payload URL**: `http://your-server.com/api/webhook/github`
2. Add a new webhook with:
1. In your GitHub repository, go to Settings → Webhooks

### Automatic Sync (GitHub Webhook)

3. Monitor the sync progress and view logs
2. Click **Start Full Sync** button
1. Navigate to the **Sync** page

### Manual Sync

## Usage

Open your browser and navigate to: `http://localhost:5000`
6. **Access the application**:

```
python app.py
```bash
Or simply run the app (it will create tables automatically):

```
flask db upgrade
flask db migrate -m "Initial migration"
flask db init
```bash
5. **Initialize database**:

```
GITHUB_WEBHOOK_SECRET=your-webhook-secret
# GitHub Webhook

TESTRAIL_SUITE_ID=1
TESTRAIL_API_KEY=your-api-key-here
TESTRAIL_EMAIL=your-email@example.com
TESTRAIL_URL=https://your-instance.testrail.io
# TestRail

GIT_BRANCH=main
GIT_CLONE_PATH=./repos/vme-test-repo
GIT_REPO_URL=https://github.com/glcp/vme-test-repo
# Git Repository

DATABASE_URL=sqlite:///suitesync.db
# Database

SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_APP=app.py
```env
Edit `.env` file with your configuration:

```
cp .env.example .env
```bash
4. **Configure environment variables**:

```
pip install -r requirements.txt
```bash
3. **Install dependencies**:

```
# source .venv/bin/activate  # On Linux/Mac
.venv\Scripts\activate  # On Windows
python -m venv .venv
```bash
2. **Create virtual environment**:

```
cd suitesync
git clone <your-repo-url>
```bash
1. **Clone the repository**:

### Setup

- PostgreSQL (optional, SQLite is used by default)
- TestRail account with API access
- Git
- Python 3.9 or higher

### Prerequisites

## Installation

```
        └── testrail.js
        ├── sync.js
        ├── test_detail.js
        ├── tests.js
        ├── dashboard.js
        ├── main.js
    └── js/
    │   └── style.css
    ├── css/
└── static/               # CSS, JS, images
│   └── testrail.html
│   ├── sync.html
│   ├── test_detail.html
│   ├── tests.html
│   ├── index.html
│   ├── base.html
├── templates/            # HTML templates
│   └── sync_service.py   # Synchronization logic
│   ├── testrail_service.py # TestRail API client
│   ├── pytest_parser.py  # Test file parsing
│   ├── git_service.py    # Git operations
├── services/
│   └── web.py            # Web page routes
│   ├── api.py            # API endpoints
├── routes/
├── requirements.txt       # Python dependencies
├── models.py              # Database models
├── config.py              # Configuration management
├── app.py                  # Flask application factory
suitesync/
```

## Architecture

- **RESTful API**: Full API for integration with other tools
- **Test Tracking**: Track test status, updates, and TestRail associations
- **GitHub Webhook Support**: Automatic sync on merge to main branch
- **Web Dashboard**: View tests, sync status, and TestRail cases
- **TestRail Integration**: Syncs test cases with TestRail using case IDs
- **Automatic Test Discovery**: Parses pytest test files from Git repository

## Features

SuiteSync is a web application that synchronizes pytest tests from a Git repository with TestRail test cases. It provides a comprehensive dashboard for viewing tests, tracking synchronization status, and managing test cases.


