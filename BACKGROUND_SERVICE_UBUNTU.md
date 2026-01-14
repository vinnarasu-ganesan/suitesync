# Running SuiteSync in Background on Ubuntu

This guide explains multiple ways to run SuiteSync in the background on Ubuntu.

## Method 1: Using systemd (Recommended for Production)

Systemd is the standard way to run services in the background on modern Ubuntu systems.

### Step 1: Create a Systemd Service File

Create a service file at `/etc/systemd/system/suitesync.service`:

```bash
sudo nano /etc/systemd/system/suitesync.service
```

Add the following content (adjust paths as needed):

```ini
[Unit]
Description=SuiteSync - Test Synchronization Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/suitesync
Environment="PATH=/home/ubuntu/suitesync/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/ubuntu/suitesync/.venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app --timeout 120
Restart=always
RestartSec=10

# Logging
StandardOutput=append:/home/ubuntu/suitesync/logs/suitesync.log
StandardError=append:/home/ubuntu/suitesync/logs/suitesync-error.log

[Install]
WantedBy=multi-user.target
```

**Important:** Replace `/home/ubuntu/suitesync` with your actual installation path.

### Step 2: Create Log Directory

```bash
mkdir -p ~/suitesync/logs
```

### Step 3: Reload Systemd and Enable Service

```bash
# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable suitesync

# Start the service
sudo systemctl start suitesync

# Check status
sudo systemctl status suitesync
```

### Step 4: Managing the Service

```bash
# Start the service
sudo systemctl start suitesync

# Stop the service
sudo systemctl stop suitesync

# Restart the service
sudo systemctl restart suitesync

# Check status
sudo systemctl status suitesync

# View logs
sudo journalctl -u suitesync -f

# Or check log files
tail -f ~/suitesync/logs/suitesync.log
tail -f ~/suitesync/logs/suitesync-error.log
```

---

## Method 2: Using nohup (Simple, Quick Setup)

For quick testing or non-production use.

### Start with nohup:

```bash
cd ~/suitesync
source .venv/bin/activate
nohup gunicorn -w 4 -b 0.0.0.0:5000 app:app > logs/suitesync.log 2>&1 &
```

### Get the Process ID:

```bash
# The PID is printed after running nohup, or find it:
ps aux | grep gunicorn
```

### Stop the service:

```bash
# Find the main gunicorn process
ps aux | grep gunicorn

# Kill it (replace PID with actual process ID)
kill <PID>

# Or force kill if needed
kill -9 <PID>
```

---

## Method 3: Using screen (Interactive Background)

Good for development or when you need to attach to the running process.

### Install screen:

```bash
sudo apt-get install screen -y
```

### Start in a screen session:

```bash
# Create a new screen session named "suitesync"
screen -S suitesync

# Inside the screen session:
cd ~/suitesync
source .venv/bin/activate
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Detach from screen: Press Ctrl+A, then D
```

### Managing screen sessions:

```bash
# List all screen sessions
screen -ls

# Reattach to session
screen -r suitesync

# Kill a session
screen -X -S suitesync quit
```

---

## Method 4: Using tmux (Alternative to screen)

Similar to screen but with more features.

### Install tmux:

```bash
sudo apt-get install tmux -y
```

### Start in a tmux session:

```bash
# Create a new tmux session named "suitesync"
tmux new -s suitesync

# Inside the tmux session:
cd ~/suitesync
source .venv/bin/activate
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Detach from tmux: Press Ctrl+B, then D
```

### Managing tmux sessions:

```bash
# List all sessions
tmux ls

# Attach to session
tmux attach -t suitesync

# Kill a session
tmux kill-session -t suitesync
```

---

## Method 5: Using Supervisor (Alternative Service Manager)

Supervisor is another popular process manager.

### Install Supervisor:

```bash
sudo apt-get install supervisor -y
```

### Create Supervisor Config:

```bash
sudo nano /etc/supervisor/conf.d/suitesync.conf
```

Add:

```ini
[program:suitesync]
command=/home/ubuntu/suitesync/.venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
directory=/home/ubuntu/suitesync
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/ubuntu/suitesync/logs/suitesync.log
```

### Start with Supervisor:

```bash
# Update supervisor
sudo supervisorctl reread
sudo supervisorctl update

# Start the service
sudo supervisorctl start suitesync

# Check status
sudo supervisorctl status suitesync

# Stop/restart
sudo supervisorctl stop suitesync
sudo supervisorctl restart suitesync
```

---

## Comparison of Methods

| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| **systemd** | Production | Auto-start on boot, system integration, robust | Requires root access |
| **nohup** | Quick testing | Simple, no dependencies | No auto-restart, manual management |
| **screen** | Development | Interactive, can reattach | Manual, doesn't survive reboot |
| **tmux** | Development | Like screen but better | Manual, doesn't survive reboot |
| **supervisor** | Production | Good monitoring, cross-platform | Extra dependency |

---

## Recommended Production Setup (systemd + Gunicorn)

For a production environment, use **systemd** with the following configuration:

### 1. Create the systemd service (as shown in Method 1)

### 2. Configure Gunicorn properly

Create `gunicorn_config.py` in your project root:

```python
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2

# Logging
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"

# Process naming
proc_name = "suitesync"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None
```

### 3. Update systemd service to use config:

```ini
[Service]
ExecStart=/home/ubuntu/suitesync/.venv/bin/gunicorn -c gunicorn_config.py app:app
```

### 4. Set up log rotation

Create `/etc/logrotate.d/suitesync`:

```bash
sudo nano /etc/logrotate.d/suitesync
```

Add:

```
/home/ubuntu/suitesync/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ubuntu ubuntu
    sharedscripts
    postrotate
        systemctl reload suitesync > /dev/null 2>&1 || true
    endscript
}
```

---

## Monitoring and Health Checks

### Check if service is running:

```bash
# For systemd
sudo systemctl status suitesync

# For any method
curl http://localhost:5000/
ps aux | grep gunicorn
netstat -tulpn | grep 5000
```

### View real-time logs:

```bash
# systemd
sudo journalctl -u suitesync -f

# Log files
tail -f ~/suitesync/logs/suitesync.log
tail -f ~/suitesync/logs/error.log
```

### Check resource usage:

```bash
# CPU and Memory usage
top -p $(pgrep -f gunicorn | head -1)

# Or use htop (install with: sudo apt-get install htop)
htop -p $(pgrep -f gunicorn | head -1)
```

---

## Troubleshooting

### Service won't start:

```bash
# Check logs
sudo journalctl -u suitesync -n 50 --no-pager

# Check if port is already in use
sudo lsof -i :5000

# Verify permissions
ls -la /home/ubuntu/suitesync/
ls -la /home/ubuntu/suitesync/.venv/

# Test gunicorn manually
cd ~/suitesync
source .venv/bin/activate
gunicorn -w 1 -b 0.0.0.0:5000 app:app
```

### Can't access from other machines:

```bash
# Check firewall
sudo ufw status
sudo ufw allow 5000/tcp

# Verify binding
netstat -tulpn | grep 5000
# Should show 0.0.0.0:5000, not 127.0.0.1:5000
```

### Service keeps crashing:

```bash
# Check error logs
tail -n 100 ~/suitesync/logs/suitesync-error.log

# Increase timeout in systemd service
# Add to [Service] section:
Environment="GUNICORN_TIMEOUT=300"

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart suitesync
```

---

## Quick Start Script

Create `start_background.sh`:

```bash
#!/bin/bash

# Quick script to start SuiteSync in background

cd ~/suitesync
source .venv/bin/activate

# Create logs directory if not exists
mkdir -p logs

# Start with nohup
nohup gunicorn -w 4 -b 0.0.0.0:5000 app:app > logs/suitesync.log 2>&1 &

PID=$!
echo "SuiteSync started with PID: $PID"
echo $PID > suitesync.pid
echo "To stop: kill $PID"
echo "To view logs: tail -f logs/suitesync.log"
```

Make executable and run:

```bash
chmod +x start_background.sh
./start_background.sh
```

---

## Summary

**For Production:** Use **systemd** (Method 1)
- Auto-starts on boot
- Automatic restart on failure
- Integrated logging
- System-wide service management

**For Development:** Use **screen** or **tmux** (Methods 3-4)
- Can reattach and see output
- Easy to stop/restart
- No root access needed

**For Quick Testing:** Use **nohup** (Method 2)
- Simplest one-liner
- No dependencies
- Good for temporary use

Choose the method that best fits your needs!

