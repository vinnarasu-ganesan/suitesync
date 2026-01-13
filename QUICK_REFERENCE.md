# 🚀 SuiteSync - Quick Reference

## Start the Application

### Windows
```powershell
# Option 1: Use the startup script
.\start.bat

# Option 2: Manual start
.\.venv\Scripts\activate
python app.py
```

### Linux/Mac
```bash
# Option 1: Use the startup script
./start.sh

# Option 2: Manual start
source .venv/bin/activate
python app.py
```

**Access**: http://localhost:5000

---

## 📋 First Time Setup Checklist

- [x] ✅ Project created
- [x] ✅ Dependencies installed
- [x] ✅ Virtual environment ready
- [x] ✅ Configuration files created
- [ ] ⚠️ Review/update `.env` with TestRail credentials (optional)
- [ ] 🎯 Start application with `python app.py`
- [ ] 🎯 Navigate to http://localhost:5000
- [ ] 🎯 Click "Start Full Sync" on Sync page

---

## 🔑 Key Files

| File | Purpose |
|------|---------|
| `app.py` | Main Flask application |
| `.env` | Configuration (Git repo URL already set) |
| `requirements.txt` | Python dependencies (already installed) |
| `start.bat` / `start.sh` | Easy startup scripts |
| `test_setup.py` | Verify installation |

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| `README.md` | Complete documentation |
| `QUICKSTART.md` | Quick start guide |
| `SETUP_GUIDE.md` | Detailed setup instructions |
| `PROJECT_SUMMARY.md` | What was created |
| `HOW_IT_WORKS.md` | Architecture & flow |

---

## 🌐 Web Pages

Once the application is running:

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | http://localhost:5000/ | Statistics and overview |
| Tests | http://localhost:5000/tests | Browse all tests |
| Sync | http://localhost:5000/sync | Manage synchronization |
| TestRail | http://localhost:5000/testrail | TestRail cases |

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tests` | GET | List all tests |
| `/api/tests/<id>` | GET | Get specific test |
| `/api/tests/stats` | GET | Test statistics |
| `/api/sync` | POST | Trigger sync |
| `/api/sync/status` | GET | Last sync status |
| `/api/sync/logs` | GET | Sync history |
| `/api/testrail/cases` | GET | TestRail cases |
| `/api/webhook/github` | POST | GitHub webhook |

---

## 🔧 Common Commands

```powershell
# Start application
python app.py

# Verify setup
python test_setup.py

# Install dependencies (if needed)
pip install -r requirements.txt

# Run with Gunicorn (production)
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Docker build
docker build -t suitesync .

# Docker Compose
docker-compose up -d
```

---

## 🎯 TestRail Configuration (Optional)

To enable full TestRail integration, update `.env`:

```env
TESTRAIL_URL=https://your-instance.testrail.io
TESTRAIL_EMAIL=your-email@example.com
TESTRAIL_API_KEY=your-api-key-here
TESTRAIL_SUITE_ID=1
```

Get API key: TestRail → My Settings → API Keys

---

## 🎨 TestRail ID Formats Supported

The parser recognizes these formats:

```python
# Decorator (recommended)
@pytest.mark.testrail('C123')
def test_example():
    pass

# Alternative decorator
@pytest.mark.testrail_id('C456')
def test_another():
    pass

# In docstring
def test_with_docstring():
    """
    Test description.
    TestRail Case: C789
    """
    pass
```

---

## 🔄 Sync Process

1. **Clone/Pull** - Get latest code from Git repository
2. **Parse** - Extract all test functions and classes
3. **Identify** - Find TestRail case IDs
4. **Update** - Create/update test records
5. **TestRail** - Fetch TestRail case details (if configured)
6. **Archive** - Mark removed tests as archived

---

## 📊 After First Sync

You should see:
- ✅ Test count on dashboard
- ✅ Tests listed in Tests page
- ✅ TestRail IDs linked
- ✅ Sync log with "Success" status
- ✅ Database file `suitesync.db` created

---

## 🐛 Troubleshooting

### Application won't start
```powershell
# Check if port 5000 is in use
netstat -an | findstr 5000

# Verify virtual environment
.\.venv\Scripts\python.exe --version

# Check for errors
python test_setup.py
```

### No tests found after sync
- Verify Git repository URL in `.env`
- Check network connectivity
- Ensure repository has `test_*.py` files
- Review sync logs for errors

### TestRail connection fails
- Verify URL (no trailing slash)
- Check API key validity
- Confirm project ID is correct
- Ensure API is enabled in TestRail

---

## 📦 Project Structure

```
suitesync/
├── app.py              # Main application
├── config.py           # Configuration
├── models.py           # Database models
├── .env                # Your settings
├── routes/             # URL routes
├── services/           # Business logic
├── templates/          # HTML pages
├── static/             # CSS & JavaScript
└── docs/               # Documentation
```

---

## 🎉 Quick Start (3 Steps)

1. **Start**: `python app.py`
2. **Open**: http://localhost:5000
3. **Sync**: Click "Start Full Sync"

That's it! 🚀

---

## 📞 Need Help?

- Run tests: `python test_setup.py`
- Check logs: Console output or sync logs in UI
- Read docs: `README.md`, `QUICKSTART.md`, `SETUP_GUIDE.md`

---

**Repository**: https://github.com/glcp/vme-test-repo (already configured)
**Status**: ✅ Ready to run
**All tests passed**: 7/7 ✓

