
from picamera2 import Picamera2
from libcamera import controls
import numpy as np
import cv2
import logging
from config import (
    CAMERA_WIDTH, CAMERA_HEIGHT,
    PREVIEW_WIDTH, PREVIEW_HEIGHT,
    LENS_POSITION, EXPOSURE_TIME_US, ANALOGUE_GAIN
)

logger = logging.getLogger(__name__)

class CameraController:
    def __init__(self):
        self.picam2 = Picamera2()
        self._configure()
        self.picam2.start()
        logger.info("Camera started")

    def _configure(self):
        # Full-res still config with manual controls
        config = self.picam2.create_still_configuration(
            main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT), "format": "BGR888"},
            lores={"size": (PREVIEW_WIDTH, PREVIEW_HEIGHT), "format": "YUV420"},
            display="lores"
        )
        self.picam2.configure(config)

        # Manual focus at infinity, fixed exposure
        self.picam2.set_controls({
            "AfMode": controls.AfModeEnum.Manual,
            "LensPosition": LENS_POSITION,
            "AeEnable": False,
            "ExposureTime": EXPOSURE_TIME_US,
            "AnalogueGain": ANALOGUE_GAIN,
            "AwbEnable": False,
            "ColourGains": (1.0, 1.0),  # neutral for IR imaging
        })
        logger.info(f"Camera configured: {CAMERA_WIDTH}x{CAMERA_HEIGHT}, "
                    f"exposure={EXPOSURE_TIME_US}us, gain={ANALOGUE_GAIN}")

    def capture_full(self) -> np.ndarray:
        """Capture full-resolution still frame"""
        frame = self.picam2.capture_array("main")
        logger.debug(f"Full frame captured: {frame.shape}")
        return frame

    def capture_preview(self) -> np.ndarray:
        """Capture low-res preview frame"""
        frame = self.picam2.capture_array("lores")
        # Convert YUV to BGR for OpenCV
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_YUV420p2BGR)
        return frame_bgr

    def set_exposure(self, exposure_us: int, gain: float):
        self.picam2.set_controls({
            "ExposureTime": exposure_us,
            "AnalogueGain": gain,
        })

    def cleanup(self):
        self.picam2.stop()
        self.picam2.close()
        logger.info("Camera cleaned up")
