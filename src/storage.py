# Save captured images to disk

import cv2
import os
import json
import logging
from datetime import datetime
from config import SAVE_DIR, MAX_SAVES

logger = logging.getLogger(__name__)

class ImageStorage:
    def __init__(self):
        os.makedirs(SAVE_DIR, exist_ok=True)
        self.count = self._count_existing()
        logger.info(f"Storage initialized at {SAVE_DIR}, {self.count} existing captures")

    def _count_existing(self) -> int:
        try:
            return len([f for f in os.listdir(SAVE_DIR) if f.endswith('.jpg')])
        except:
            return 0

    def save(self, frame, label: str = "capture", metrics: dict = None) -> str | None:
        if self.count >= MAX_SAVES:
            logger.warning("Max saves reached")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"{timestamp}_{label}.jpg"
        filepath = os.path.join(SAVE_DIR, filename)

        cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        self.count += 1

        # Save metrics alongside image
        if metrics:
            meta_path = filepath.replace('.jpg', '_meta.json')
            with open(meta_path, 'w') as f:
                json.dump({**metrics, "timestamp": timestamp, "label": label}, f, indent=2)

        logger.info(f"Saved: {filename} (total: {self.count})")
        return filepath

    def latest_captures(self, n: int = 5) -> list:
        files = sorted([
            os.path.join(SAVE_DIR, f)
            for f in os.listdir(SAVE_DIR)
            if f.endswith('.jpg')
        ])
        return files[-n:]
