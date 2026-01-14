# SuiteSync - Ubuntu 22.04 Setup Guide

## Prerequisites Installation

After cloning the repository, follow these steps:

### 1. Update System Packages

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install Python 3.10+ and Dependencies

```bash
# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install Git (if not already installed)
sudo apt install git -y

# Install additional build tools
sudo apt install build-essential libssl-dev libffi-dev python3-dev -y
```

### 3. Verify Python Version

```bash
python3 --version
# Should show Python 3.10.x or higher
```

## Application Setup

### 4. Navigate to Project Directory

```bash
cd ~/suitesync
# Or wherever you cloned the repository
```

### 5. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Your prompt should now show (venv)
```

### 6. Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt
```

### 7. Create Configuration File

```bash
# Create .env file
nano .env
```

Add the following configuration (modify as needed):

```env
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here-change-this

# Database
DATABASE_URL=sqlite:///instance/suitesync.db

# Git Repository
GIT_REPO_URL=https://github.com/glcp/vme-test-repo
GIT_BRANCH=main
GIT_CLONE_PATH=./repos/vme-test-repo

# GitHub Authentication (Optional - for private repos)
# Use Personal Access Token (PAT) instead of password
GITHUB_USERNAME=your-github-username
GITHUB_TOKEN=ghp_your_personal_access_token_here

# TestRail Configuration (Optional - Add your credentials)
TESTRAIL_URL=https://testrail.devx.hpedev.net
TESTRAIL_EMAIL=your-email@example.com
TESTRAIL_API_KEY=your-api-key-here
TESTRAIL_SUITE_ID=126845

# Sync Configuration
SYNC_ON_STARTUP=false
```

**Save the file**: Press `Ctrl+O`, `Enter`, then `Ctrl+X`

### 7a. GitHub Authentication (For Private Repositories)

If you're accessing a **private GitHub repository**, you need to provide authentication credentials:

#### Creating a GitHub Personal Access Token (PAT):

1. **Go to GitHub Settings**: https://github.com/settings/tokens
2. **Click "Generate new token"** → "Generate new token (classic)"
3. **Give it a name**: e.g., "SuiteSync Access"
4. **Select scopes**:
   - For private repos: Check `repo` (Full control of private repositories)
   - For public repos: Check `public_repo` (Access public repositories)
5. **Click "Generate token"**
6. **Copy the token** (starts with `ghp_`) - you won't see it again!

#### Add to .env file:

```env
GITHUB_USERNAME=your-github-username
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Note:** 
- For public repositories, you can skip this step
- Keep your token secure - never commit it to version control
- If using SSH URLs (git@github.com:...), authentication happens via SSH keys, not tokens

### 8. Create Required Directories

```bash
mkdir -p repos logs instance migrations
```

### 9. Initialize Database

```bash
# Run migrations
python migrations/add_markers_column.py
```

### 10. Test Installation

```bash
# Quick test to verify everything is set up
python -c "from app import create_app; app = create_app(); print('✓ Setup successful!')"
```

## Running the Application

### Option 1: Development Server (Recommended for Testing)

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the application
python app.py
```

The application will be available at: **http://localhost:5000** or **http://your-vm-ip:5000**

### Option 2: Using Flask CLI

```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
```

### Option 3: Production with Gunicorn

```bash
# Install gunicorn if not already installed
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**With background mode:**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app --daemon
```

## Accessing the Application

### From the VM itself:
```bash
http://localhost:5000
```

### From your host machine or network:
```bash
http://VM_IP_ADDRESS:5000
```

**Find your VM IP address:**
```bash
ip addr show | grep inet
# Or
hostname -I
```

## Firewall Configuration

If you can't access from outside the VM, configure the firewall:

```bash
# Allow port 5000
sudo ufw allow 5000/tcp

# Check firewall status
sudo ufw status
```

## Running as a System Service (Optional)

To run SuiteSync as a background service:

### 1. Create Service File

```bash
sudo nano /etc/systemd/system/suitesync.service
```

Add the following content (adjust paths):

```ini
[Unit]
Description=SuiteSync Web Application
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/suitesync
Environment="PATH=/home/YOUR_USERNAME/suitesync/venv/bin"
ExecStart=/home/YOUR_USERNAME/suitesync/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Replace `YOUR_USERNAME` with your actual username**

### 2. Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable suitesync

# Start the service
sudo systemctl start suitesync

# Check status
sudo systemctl status suitesync
```

### 3. Manage Service

```bash
# Stop service
sudo systemctl stop suitesync

# Restart service
sudo systemctl restart suitesync

# View logs
sudo journalctl -u suitesync -f
```

## First Sync

After starting the application:

1. **Open browser**: Navigate to `http://VM_IP:5000`
2. **Go to Sync page**: Click "Sync" in navigation
3. **Click "Start Full Sync"**: This will:
   - Clone the Git repository
   - Parse all test files
   - Extract markers and TestRail IDs
   - Populate the database
4. **Wait 1-2 minutes** for sync to complete
5. **Browse Tests page**: View all discovered tests with markers

## Troubleshooting

### Permission Issues

```bash
# Fix permissions
chmod +x app.py
chmod -R 755 repos logs instance
```

### Port Already in Use

```bash
# Check what's using port 5000
sudo lsof -i :5000

# Kill the process if needed
sudo kill -9 PID
```

### Virtual Environment Issues

```bash
# Deactivate and recreate
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Database Errors

```bash
# Reset database
rm instance/suitesync.db
python migrations/add_markers_column.py
```

### Git Clone Errors

```bash
# If git clone fails, ensure git is installed
sudo apt install git -y

# Test git connectivity
git clone https://github.com/glcp/vme-test-repo /tmp/test-repo
```

### Can't Access from Host Machine

```bash
# Check if app is listening on 0.0.0.0
netstat -tulpn | grep 5000

# Ensure firewall allows connection
sudo ufw allow 5000/tcp

# Check if VM network is properly configured
ping VM_IP_ADDRESS
```

## Environment Variables Reference

Create a `.env` file with these variables:

```env
# Flask Settings
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=change-this-to-random-string

# Database
DATABASE_URL=sqlite:///instance/suitesync.db

# Git Repository Settings
GIT_REPO_URL=https://github.com/glcp/vme-test-repo
GIT_BRANCH=main
GIT_CLONE_PATH=./repos/vme-test-repo

# GitHub Authentication (Optional - for private repos)
# Create a Personal Access Token at: https://github.com/settings/tokens
# Required scopes: repo (for private repos) or public_repo (for public repos)
GITHUB_USERNAME=your-github-username
GITHUB_TOKEN=ghp_your_personal_access_token_here

# TestRail Settings (Optional)
TESTRAIL_URL=https://testrail.devx.hpedev.net
TESTRAIL_EMAIL=your-email@example.com
TESTRAIL_API_KEY=your-api-key
TESTRAIL_SUITE_ID=126845

# Sync Settings
SYNC_ON_STARTUP=false

# GitHub Webhook (Optional)
GITHUB_WEBHOOK_SECRET=your-webhook-secret
```

## Quick Reference Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Start application (development)
python app.py

# Start application (production)
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# View logs (if running as service)
sudo journalctl -u suitesync -f

# Check application status
sudo systemctl status suitesync

# Restart application
sudo systemctl restart suitesync

# Update code and restart
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart suitesync
```

## Testing the Setup

### 1. Test Python Import
```bash
python -c "from app import create_app; print('OK')"
```

### 2. Test Database Connection
```bash
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); print('Database OK')"
```

### 3. Test API Endpoint
```bash
# After starting the app
curl http://localhost:5000/api/tests/stats
```

## Performance Tips

### For Better Performance:

1. **Use more Gunicorn workers:**
   ```bash
   # Recommended: 2-4 × CPU cores
   gunicorn -w 8 -b 0.0.0.0:5000 app:app
   ```

2. **Use PostgreSQL instead of SQLite (Production):**
   ```bash
   # Install PostgreSQL
   sudo apt install postgresql postgresql-contrib -y
   
   # Update .env
   DATABASE_URL=postgresql://user:password@localhost/suitesync
   ```

3. **Add Nginx reverse proxy:**
   ```bash
   sudo apt install nginx -y
   # Configure nginx to proxy to port 5000
   ```

## Security Best Practices

1. **Change SECRET_KEY** in `.env` to a random string
2. **Use environment variables** for sensitive data
3. **Enable firewall:**
   ```bash
   sudo ufw enable
   sudo ufw allow 22/tcp   # SSH
   sudo ufw allow 5000/tcp # SuiteSync
   ```
4. **Keep system updated:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

## Summary

You've successfully set up SuiteSync on Ubuntu 22.04! Here's what you have:

✅ Python virtual environment with all dependencies  
✅ Database initialized with migrations  
✅ Application configured and ready to run  
✅ Firewall configured (if needed)  
✅ System service configured (optional)  

**Next steps:**
1. Start the application: `python app.py`
2. Open browser: `http://VM_IP:5000`
3. Run first sync: Click "Sync" → "Start Full Sync"
4. Explore your tests with markers!

---

**Need help?** Check the logs or run: `python -c "from app import create_app; create_app()"`

