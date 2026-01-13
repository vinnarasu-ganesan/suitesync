# SuiteSync - Complete Setup Guide

## Project Overview

**SuiteSync** is a comprehensive web application that synchronizes pytest tests from the Git repository `https://github.com/glcp/vme-test-repo` with TestRail test cases. It provides:

- **Automatic Test Discovery**: Parses pytest files to extract test information
- **TestRail Integration**: Links tests with TestRail cases using case IDs
- **Web Dashboard**: Beautiful UI to view tests, sync status, and TestRail cases
- **GitHub Webhooks**: Auto-sync on merge to main branch
- **RESTful API**: Full API for programmatic access

## Architecture

```
SuiteSync Web App
│
├── Frontend (Bootstrap 5 + Vanilla JS)
│   ├── Dashboard - Statistics and overview
│   ├── Tests - Browse all tests with filters
│   ├── TestRail - View TestRail cases
│   └── Sync - Manage synchronization
│
├── Backend (Flask + SQLAlchemy)
│   ├── API Routes - RESTful endpoints
│   ├── Web Routes - Page rendering
│   └── Services
│       ├── GitService - Clone/pull repository
│       ├── PytestParser - Parse test files
│       ├── TestRailService - TestRail API client
│       └── SyncService - Orchestrate sync
│
└── Database (SQLite/PostgreSQL)
    ├── tests - Test cases from repository
    ├── testrail_cases - TestRail case cache
    └── sync_logs - Sync operation history
```

## Setup Instructions

### ✅ Prerequisites (Already Satisfied)

- ✓ Python 3.10 installed
- ✓ Virtual environment created at `.venv`
- ✓ All dependencies installed
- ✓ Git installed
- ✓ All files and directories created

### 📝 Configuration

1. **Review the `.env` file** (already created with defaults):

```env
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development

# Git Repository (Already configured)
GIT_REPO_URL=https://github.com/glcp/vme-test-repo
GIT_BRANCH=main

# TestRail Configuration (Optional - Add your credentials)
TESTRAIL_URL=https://your-instance.testrail.io
TESTRAIL_EMAIL=your-email@example.com
TESTRAIL_API_KEY=your-api-key-here
TESTRAIL_SUITE_ID=1
```

2. **TestRail Setup** (Optional but recommended):
   - Log in to your TestRail instance
   - Go to **My Settings → API Keys**
   - Generate a new API key
   - Update `.env` with your credentials

### 🚀 Running the Application

**Option 1: Quick Start**
```powershell
# Activate virtual environment (if not already active)
.\.venv\Scripts\activate

# Run the application
python app.py
```

**Option 2: Using Flask CLI**
```powershell
flask run
```

**Option 3: Using Gunicorn (Production)**
```powershell
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

The application will be available at: **http://localhost:5000**

### 📊 Using the Application

#### 1. Dashboard (Home Page)
- View test statistics (total, with/without TestRail IDs, archived)
- See last sync status
- View sync history chart
- Browse recent tests

#### 2. Tests Page
- Browse all tests with pagination
- Filter by status (active/archived)
- Filter by TestRail ID presence
- Search tests by name, file, or ID
- Click on any test to view details

#### 3. Sync Page
- **Manual Sync**: Click "Start Full Sync" button
- View current sync status
- See complete sync history with details
- Monitor tests found, synced, and failed

#### 4. TestRail Page
- View all TestRail cases cached in the database
- See case details (ID, title, suite, section, etc.)
- Browse with pagination

### 🔄 Synchronization Process

When you trigger a sync:

1. **Clone/Update Repository**: Pulls latest code from GitHub
2. **Parse Test Files**: Extracts all test functions and classes
3. **Extract TestRail IDs**: Identifies TestRail case IDs from:
   - `@pytest.mark.testrail('C123')` decorators
   - `@pytest.mark.testrail_id('C456')` decorators
   - Docstring mentions: `TestRail Case: C789`
4. **Update Database**: Creates or updates test records
5. **Sync with TestRail**: Fetches TestRail case details (if configured)
6. **Archive Old Tests**: Marks removed tests as archived

### 🔗 GitHub Webhook Setup (Auto-sync on merge)

1. Go to your GitHub repository: `https://github.com/glcp/vme-test-repo`
2. Navigate to **Settings → Webhooks → Add webhook**
3. Configure:
   - **Payload URL**: `http://your-server.com/api/webhook/github`
   - **Content type**: `application/json`
   - **Secret**: Set a secret and add to `.env` as `GITHUB_WEBHOOK_SECRET`
   - **Events**: Select "Just the push event"
   - **Active**: ✓ Checked
4. Save webhook

Now, whenever code is pushed to the main branch, SuiteSync will automatically sync!

### 📡 API Endpoints

All API endpoints return JSON and are prefixed with `/api`:

#### Tests
- `GET /api/tests` - List all tests (supports pagination, search, filters)
- `GET /api/tests/<id>` - Get specific test details
- `GET /api/tests/stats` - Get test statistics

#### TestRail
- `GET /api/testrail/cases` - List all TestRail cases

#### Sync
- `POST /api/sync` - Trigger manual sync
- `GET /api/sync/status` - Get last sync status
- `GET /api/sync/logs` - Get sync history

#### Webhook
- `POST /api/webhook/github` - GitHub webhook endpoint

**Example API Usage:**
```bash
# Get all tests
curl http://localhost:5000/api/tests

# Get test statistics
curl http://localhost:5000/api/tests/stats

# Trigger sync
curl -X POST http://localhost:5000/api/sync

# Get sync status
curl http://localhost:5000/api/sync/status
```

### 📁 Project Structure

```
suitesync/
├── app.py                      # Flask application factory
├── config.py                   # Configuration management
├── models.py                   # Database models (SQLAlchemy)
├── requirements.txt            # Python dependencies
├── .env                        # Environment configuration
├── README.md                   # Complete documentation
├── QUICKSTART.md              # Quick start guide
├── setup.py                   # Setup script
├── test_setup.py              # Verify installation
│
├── routes/                    # Application routes
│   ├── api.py                # API endpoints
│   └── web.py                # Web page routes
│
├── services/                  # Business logic
│   ├── git_service.py        # Git operations
│   ├── pytest_parser.py      # Parse test files
│   ├── testrail_service.py   # TestRail API client
│   └── sync_service.py       # Sync orchestration
│
├── templates/                 # Jinja2 HTML templates
│   ├── base.html             # Base template
│   ├── index.html            # Dashboard
│   ├── tests.html            # Tests listing
│   ├── test_detail.html      # Test details
│   ├── sync.html             # Sync management
│   └── testrail.html         # TestRail cases
│
├── static/                    # Static assets
│   ├── css/
│   │   └── style.css         # Custom styles
│   └── js/
│       ├── main.js           # Common utilities
│       ├── dashboard.js      # Dashboard logic
│       ├── tests.js          # Tests page logic
│       ├── test_detail.js    # Test detail logic
│       ├── sync.js           # Sync page logic
│       └── testrail.js       # TestRail page logic
│
├── repos/                     # Cloned repositories (created at runtime)
├── logs/                      # Application logs
│
└── Deployment files
    ├── Dockerfile            # Docker container
    ├── docker-compose.yml    # Docker Compose setup
    └── Procfile             # Heroku deployment
```

### 🗄️ Database Models

#### Test
Represents a pytest test case from the repository.

**Fields:**
- `id` - Primary key
- `test_id` - Unique identifier (file::class::function)
- `test_name` - Function name
- `test_file` - File path
- `test_class` - Class name (if applicable)
- `description` - Docstring
- `testrail_case_id` - TestRail case ID (e.g., 'C123')
- `status` - active, archived, deleted
- `created_at`, `updated_at` - Timestamps

#### TestRailCase
Represents a TestRail test case (cached).

**Fields:**
- `id` - Primary key
- `case_id` - TestRail case ID
- `title` - Case title
- `section_id`, `suite_id` - TestRail organization
- `type_id`, `priority_id` - Case metadata
- `custom_fields` - JSON field for custom data
- `created_at`, `updated_at` - Timestamps

#### SyncLog
Tracks synchronization operations.

**Fields:**
- `id` - Primary key
- `sync_type` - manual, webhook, startup, scheduled
- `status` - success, failed, in_progress
- `message` - Status message
- `commit_hash` - Git commit
- `branch` - Git branch
- `tests_found`, `tests_synced`, `tests_failed` - Counters
- `started_at`, `completed_at` - Timestamps

### 🐳 Docker Deployment

**Build and run with Docker:**
```bash
docker build -t suitesync .
docker run -p 5000:5000 --env-file .env suitesync
```

**Use Docker Compose:**
```bash
docker-compose up -d
```

This will start:
- Web application (Flask)
- PostgreSQL database
- Redis (for background tasks)

### 🔧 Troubleshooting

#### Application won't start
- Check if port 5000 is available: `netstat -an | findstr 5000`
- Verify virtual environment is activated
- Check `.env` file exists and is properly formatted

#### Tests not found after sync
- Verify repository URL is accessible
- Check network connectivity
- Ensure repository contains pytest test files
- View sync logs for detailed error messages

#### TestRail connection fails
- Verify TestRail URL (no trailing slash)
- Check API key is valid and not expired
- Ensure project ID is correct
- Verify API access is enabled in TestRail settings
- Test connection: `curl -u email:apikey https://instance.testrail.io/index.php?/api/v2/get_projects`

#### Database errors
- Delete `suitesync.db` and restart to recreate
- Check file permissions
- Verify SQLite is available

### 📈 Features in Detail

#### Test Case ID Formats

SuiteSync recognizes TestRail case IDs in multiple formats:

```python
# Decorator format (recommended)
@pytest.mark.testrail('C123')
def test_example():
    pass

# Alternative decorator
@pytest.mark.testrail_id('C456')
def test_another():
    pass

# Docstring format
def test_with_docstring():
    """
    Test description.
    TestRail Case: C789
    """
    pass

# Class-based tests
class TestFeature:
    @pytest.mark.testrail('C100')
    def test_method(self):
        pass
```

#### Automatic Test Discovery

The parser:
- Finds all `test_*.py` files
- Extracts test functions (starting with `test_`)
- Handles both standalone functions and class methods
- Preserves file structure and class hierarchy
- Extracts docstrings as descriptions

#### Smart Sync

- Only updates changed tests
- Archives tests that no longer exist
- Tracks sync history for auditing
- Handles git conflicts gracefully
- Retries on transient failures

### 📚 Additional Resources

- **Full Documentation**: See `README.md`
- **Quick Start**: See `QUICKSTART.md`
- **Example Tests**: See `example_test.py`
- **Test Setup**: Run `python test_setup.py`

### 🎉 You're All Set!

Your SuiteSync application is fully configured and ready to use. Here's what to do next:

1. **Start the application**: `python app.py`
2. **Open your browser**: http://localhost:5000
3. **Trigger first sync**: Navigate to Sync page and click "Start Full Sync"
4. **Browse tests**: Explore the Tests page to see discovered tests
5. **Configure TestRail**: Add your credentials to enable full integration

### 📞 Support

- Check logs in console for error details
- Review sync logs in the Sync page
- Verify setup with: `python test_setup.py`
- Read full documentation in `README.md`

---

**Built with ❤️ using Flask, Bootstrap, and modern web technologies.**

