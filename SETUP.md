# Retinal Imaging Device — Embedded Linux Setup Guide

## 1. Deploy Files to Pi

```bash
# From your Windows laptop (Git Bash)
scp -r retina_device/ icap123@192.168.2.2:~/
ssh icap123@192.168.2.2
cd ~/retina_device
bash install.sh
```

---

## 2. Boot-on-Startup (systemd)

```bash
# Install and enable the service
sudo cp retina_device.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable retina_device # starts on every boot
sudo systemctl start retina_device # start right now

# Check it's running
sudo systemctl status retina_device

# Live logs
journalctl -u retina_device -f

# Stop/restart
sudo systemctl stop retina_device
sudo systemctl restart retina_device

# Disable boot autostart (for development)
sudo systemctl disable retina_device
```

---

## 3. Set API Key Securely (never hardcode it)

```bash
# Add to Pi's environment — persists across reboots
echo 'export RETINA_API_KEY="your-key-here"' >> ~/.bashrc
echo 'export RETINA_API_KEY="your-key-here"' | sudo tee -a /etc/environment
source ~/.bashrc
```

For the systemd service, add the key to the service file:
```ini
[Service]
Environment="RETINA_API_KEY=your-key-here"
```
Then: `sudo systemctl daemon-reload && sudo systemctl restart retina_device`

---

## 4. Encryption — What's Implemented

| Layer | Standard | Implementation |
|-------|----------|----------------|
| At-rest | AES-128-GCM | Images encrypted before saving to disk |
| In-transit | TLS 1.2+ | Enforced via SSLContext minimum_version |
| Integrity | SHA-256 | Hash sent with every upload, verified by backend |
| Audit log | PHIPA req. | Every upload logged to audit.log with timestamp |

**AES key lives at:** `/home/icap123/.retina_key` (chmod 400 — owner read only)

To view audit log:
```bash
cat ~/retina_device/audit.log
```

---

## 5. Useful Embedded Linux Commands

```bash
# Check CPU/memory usage
htop
free -h
df -h # disk space

# Check GPIO state
gpio readall # requires wiringpi
cat /sys/kernel/debug/gpio # kernel GPIO state

# Check camera detected
libcamera-hello --list-cameras

# Check service logs since last boot
journalctl -u retina_device --since "today"

# Check what's running on a port
sudo ss -tlnp | grep 5000

# Monitor network
ip addr show eth0
ping 192.168.2.1

# Watch captures folder live
watch -n 2 'ls -lh ~/captures/ | tail -20'

# Count captures
ls ~/captures/*.jpg | wc -l

# Check system temperature (Pi 5 runs warm)
vcgencmd measure_temp

# Check throttling (important for symposium)
vcgencmd get_throttled
# 0x0 = all good, anything else = throttled/undervoltage
```

---

## 6. Symposium Day Checklist

1. **Power on Pi** → wait 30s for boot
2. **Check service running:** `sudo systemctl status retina_device`
3. **Start stream for demo:** `python3 main.py --stream`
4. **VLC on laptop:** Media → Open Network Stream → `tcp/mjpeg://192.168.2.2:5000`
5. **Set laptop ethernet static IP:** 192.168.2.1 / 255.255.255.0
6. **Test capture:** `python3 main.py --once`
7. **Check captures saved:** `ls ~/captures/`

---

## 7. If Something Breaks

```bash
# Check logs first
journalctl -u retina_device -n 50

# Camera not detected
sudo systemctl restart rpicam

# GPIO permission denied
sudo usermod -aG gpio icap123
# then reboot

# Python module not found
pip3 install <module> --break-system-packages

# Service won't start
sudo systemctl status retina_device
# read the error, then:
sudo journalctl -xe

# Restart everything
sudo reboot
```

---

## 8. File Locations

| Path | Contents |
|------|----------|
| `~/retina_device/` | All source code |
| `~/captures/` | Saved retinal images (AES-encrypted) |
| `~/retina_device/device.log` | Application log |
| `~/retina_device/audit.log` | PHIPA audit trail |
| `~/.retina_key` | AES-128 encryption key (chmod 400) |
| `/etc/systemd/system/retina_device.service` | Boot service |
