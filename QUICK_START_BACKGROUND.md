# Quick Reference: Running SuiteSync in Background on Ubuntu

## 🚀 Quick Start (Simplest Method)

```bash
# Make scripts executable
chmod +x *.sh

# Start in background
./start_background.sh

# Check status
./status.sh

# View logs
./view_logs.sh

# Stop
./stop_background.sh
```

---

## 📋 All Available Scripts

| Script | Purpose |
|--------|---------|
| `start_background.sh` | Start SuiteSync in background |
| `stop_background.sh` | Stop SuiteSync |
| `restart_background.sh` | Restart SuiteSync |
| `status.sh` | Check if running |
| `view_logs.sh` | View logs interactively |
| `setup_systemd.sh` | Install as systemd service (production) |

---

## 🔧 Method 1: Simple Background (Development/Testing)

### Start
```bash
./start_background.sh
```

### Stop
```bash
./stop_background.sh
```

### Status
```bash
./status.sh
```

### Logs
```bash
./view_logs.sh
# Or manually:
tail -f logs/suitesync.log
```

**Pros:** Simple, no root needed  
**Cons:** Doesn't auto-restart on failure, doesn't survive reboot

---

## 🎯 Method 2: Systemd Service (Production)

### One-Time Setup
```bash
# Run the setup script (will prompt for sudo)
./setup_systemd.sh
```

### Daily Usage
```bash
# Start
sudo systemctl start suitesync

# Stop
sudo systemctl stop suitesync

# Restart
sudo systemctl restart suitesync

# Status
sudo systemctl status suitesync

# Logs (real-time)
sudo journalctl -u suitesync -f

# Logs (last 50 lines)
sudo journalctl -u suitesync -n 50

# Enable auto-start on boot
sudo systemctl enable suitesync

# Disable auto-start
sudo systemctl disable suitesync
```

**Pros:** Auto-restart, survives reboot, production-ready  
**Cons:** Requires root/sudo access

---

## 🔍 Common Commands

### Check if Running
```bash
./status.sh
# Or manually:
ps aux | grep gunicorn
netstat -tulpn | grep 5000
curl http://localhost:5000
```

### View Logs
```bash
./view_logs.sh
# Or manually:
tail -f logs/suitesync.log
tail -f logs/access.log
tail -f logs/error.log
```

### Check Resource Usage
```bash
# CPU and memory
top -p $(cat suitesync.pid)
# Or
htop -p $(cat suitesync.pid)
```

### Kill Stuck Process
```bash
# Graceful
kill $(cat suitesync.pid)

# Force kill
kill -9 $(cat suitesync.pid)

# Kill all gunicorn processes
pkill -f "gunicorn.*app:app"
```

---

## 🌐 Access from Other Machines

### Allow Through Firewall
```bash
# Ubuntu UFW
sudo ufw allow 5000/tcp
sudo ufw status

# Or iptables
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
```

### Access
```
http://<server-ip>:5000
```

---

## 🐛 Troubleshooting

### Service Won't Start
```bash
# Check logs
./view_logs.sh
# Or
tail -50 logs/suitesync.log

# Check if port is in use
sudo lsof -i :5000
sudo netstat -tulpn | grep 5000

# Check permissions
ls -la .venv/
ls -la logs/

# Test manually
source .venv/bin/activate
gunicorn -w 1 -b 0.0.0.0:5000 app:app
```

### Can't Connect from Browser
```bash
# Check if actually listening
netstat -tulpn | grep 5000
# Should show: 0.0.0.0:5000 (not 127.0.0.1:5000)

# Check firewall
sudo ufw status
sudo ufw allow 5000/tcp

# Test locally
curl http://localhost:5000
```

### Service Keeps Crashing
```bash
# Check error logs
tail -50 logs/error.log

# Check system logs (if using systemd)
sudo journalctl -u suitesync -n 100

# Increase timeout
# Edit gunicorn command to add: --timeout 300
```

### Remove/Uninstall Systemd Service
```bash
# Stop service
sudo systemctl stop suitesync

# Disable service
sudo systemctl disable suitesync

# Remove service file
sudo rm /etc/systemd/system/suitesync.service

# Reload systemd
sudo systemctl daemon-reload
```

---

## 📊 Monitoring

### Watch Logs in Real-Time
```bash
# Application logs
tail -f logs/suitesync.log

# Access logs
tail -f logs/access.log

# Error logs
tail -f logs/error.log

# Systemd logs
sudo journalctl -u suitesync -f
```

### Resource Monitoring
```bash
# Simple
ps aux | grep gunicorn

# Detailed
top -p $(cat suitesync.pid)

# With htop (install: sudo apt install htop)
htop -p $(cat suitesync.pid)

# Disk usage
du -sh logs/
```

---

## 🔄 Updates and Maintenance

### After Code Changes
```bash
# Method 1: Using scripts
./restart_background.sh

# Method 2: Using systemd
sudo systemctl restart suitesync
```

### After Package Updates
```bash
# Stop service
./stop_background.sh  # or: sudo systemctl stop suitesync

# Update packages
source .venv/bin/activate
pip install -r requirements.txt --upgrade

# Start service
./start_background.sh  # or: sudo systemctl start suitesync
```

### Log Rotation
```bash
# Manual log rotation
cd logs
mv suitesync.log suitesync.log.1
mv access.log access.log.1
mv error.log error.log.1

# Or set up automatic rotation (create /etc/logrotate.d/suitesync):
sudo nano /etc/logrotate.d/suitesync
```

Add:
```
/path/to/suitesync/logs/*.log {
    daily
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

## 📝 Summary

### For Development/Testing
```bash
./start_background.sh  # Start
./status.sh            # Check
./stop_background.sh   # Stop
```

### For Production
```bash
./setup_systemd.sh              # One-time setup
sudo systemctl start suitesync  # Start
sudo systemctl status suitesync # Check
sudo systemctl stop suitesync   # Stop
```

---

## 🆘 Getting Help

1. Check status: `./status.sh`
2. View logs: `./view_logs.sh`
3. Read detailed guide: `BACKGROUND_SERVICE_UBUNTU.md`
4. Check systemd logs: `sudo journalctl -u suitesync -n 50`

---

**Quick Access:**
- Application: http://localhost:5000
- Logs: `./view_logs.sh`
- Status: `./status.sh`

