#!/usr/bin/env python3
"""
python3 main.py -> continuous capture loop
python3 main.py --once -> single capture and exit
python3 main.py --stream -> MJPEG preview stream only (VLC)
python3 main.py --status -> print status and exit
"""

import argparse
import logging
import signal
import sys
import time

from illumination import IlluminationController
from camera_control import CameraController
from quality_check import QualityAnalyzer
from storage import ImageStorage
from state_machine import DeviceStateMachine
from uploader import Uploader
from config import CYCLE_INTERVAL, BACKEND_ENDPOINT, API_KEY, UPLOAD_ENABLED

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/home/icap123/retina_device/device.log"),
    ]
)
logger = logging.getLogger("main")

_running = True

def _signal_handler(sig, frame):
    global _running
    logger.info("Shutdown signal received")
    _running = False

signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


# ── Modes ──
def run_continuous(device):
    logger.info(f"Starting continuous capture (interval={CYCLE_INTERVAL}s)")
    while _running:
        result = device.run_cycle()
        status = device.status()
        logger.info(f"captures={status['captures']} fails={status['fails']} pending_upload={status['pending_upload']}")
        if _running:
            time.sleep(CYCLE_INTERVAL)
    device.flush_uploads()


def run_once(device):
    result = device.run_cycle()
    print(f"\n{'SUCCESS' if result['success'] else 'FAILED'}")
    print(f"Metrics:  {result['metrics']}")
    print(f"Saved:    {result.get('filepath')}")
    print(f"Uploaded: {result.get('uploaded')}")
    device.flush_uploads()


def run_stream():
    import subprocess
    logger.info("Starting MJPEG stream — VLC: tcp/mjpeg://192.168.2.2:5000")
    cmd = [
        "rpicam-vid", "-t", "0",
        "--width", "1280", "--height", "720", "--framerate", "30",
        "--autofocus-mode", "manual", "--lens-position", "0",
        "--codec", "mjpeg", "--inline", "--listen",
        "-o", "tcp://0.0.0.0:5000"
    ]
    proc = subprocess.Popen(cmd)
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()


def main():
    parser = argparse.ArgumentParser(description="Retinal Imaging Device")
    parser.add_argument("--once",   action="store_true")
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()

    if args.stream:
        run_stream()
        return

    logger.info("Initializing device...")

    illumination = IlluminationController()
    camera = CameraController()
    analyzer = QualityAnalyzer()
    storage = ImageStorage()
    uploader = Uploader(BACKEND_ENDPOINT) if UPLOAD_ENABLED else None

    device = DeviceStateMachine(illumination, camera, analyzer, storage, uploader)
    logger.info("Device ready")

    try:
        if args.status:
            print(device.status())
        elif args.once:
            run_once(device)
        else:
            run_continuous(device)
    finally:
        logger.info("Shutting down...")
        illumination.all_off()
        illumination.cleanup()
        camera.cleanup()
        logger.info("Shutdown complete")

if __name__ == "__main__":
    main()
