# SuiteSync Quick Start Guide

## Prerequisites
- Python 3.9+
- Git
- TestRail account (optional for full functionality)

## Quick Setup

### 1. Install Dependencies
```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Application
Edit the `.env` file with your settings:
- **Git Repository**: Already configured for `https://github.com/glcp/vme-test-repo`
- **TestRail**: Add your TestRail URL, email, and API key
- **Database**: SQLite is configured by default (no setup needed)

### 3. Run the Application
```powershell
python app.py
```

The application will be available at: http://localhost:5000

## First Sync

1. Open the application in your browser
2. Navigate to the **Sync** page
3. Click **Start Full Sync** button
4. Wait for the sync to complete (may take a few minutes)

## Expected Results

After the first sync:
- Tests from the Git repository will be parsed
- Tests with TestRail IDs will be identified
- Dashboard will show test statistics
- You can browse all tests in the **Tests** page

## TestRail Integration

To enable full TestRail integration:

1. Get your TestRail API credentials:
   - Log in to TestRail
   - Go to My Settings → API Keys
   - Generate a new API key

2. Update `.env` file:
```env
TESTRAIL_URL=https://your-instance.testrail.io
TESTRAIL_EMAIL=your-email@example.com
TESTRAIL_API_KEY=your-api-key-here
TESTRAIL_SUITE_ID=1
```

3. Restart the application and trigger a new sync

## GitHub Webhook Setup (Optional)

To enable automatic sync on merge to main:

1. In your GitHub repository, go to: **Settings → Webhooks → Add webhook**

2. Configure:
   - **Payload URL**: `http://your-server.com/api/webhook/github`
   - **Content type**: `application/json`
   - **Secret**: Set a secret and add it to `.env` as `GITHUB_WEBHOOK_SECRET`
   - **Events**: Select "Just the push event"

3. Save the webhook

Now, whenever code is merged to the main branch, SuiteSync will automatically sync.

## Troubleshooting

### Application won't start
- Check if port 5000 is available
- Verify all dependencies are installed
- Check `.env` file for syntax errors

### Tests not found
- Verify Git repository URL is correct
- Check network connectivity
- Ensure repository contains pytest test files (test_*.py)

### TestRail connection fails
- Verify TestRail URL (no trailing slash)
- Check API key is valid
- Ensure project ID is correct
- Verify API access is enabled in TestRail

## Support

For detailed documentation, see `README.md`
For issues, check the application logs or console output

