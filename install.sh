#!/bin/bash
# install.sh — Run once on the Pi to set everything up
set -e
echo "=== Setup ==="

echo ">>> apt packages..."
sudo apt update
sudo apt install -y python3-picamera2 python3-opencv python3-numpy python3-pip

echo ">>> pip packages..."
pip3 install -r requirements.txt --break-system-packages

echo ">>> Creating directories..."
mkdir -p /home/icap123/captures

echo ">>> Installing systemd service..."
sudo cp retina_device.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable retina_device

echo ""
echo "=== *DONE! Run: python3 main.py --once ==="
