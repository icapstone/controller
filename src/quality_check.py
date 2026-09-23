# Image quality validation + pupil detection

import cv2
import numpy as np
import logging
from config import LAPLACIAN_THRESHOLD, MIN_BRIGHTNESS, MAX_BRIGHTNESS

logger = logging.getLogger(__name__)

class QualityAnalyzer:

    def focus_score(self, frame: np.ndarray) -> float:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())

    def brightness_score(self, frame: np.ndarray) -> float:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return float(np.mean(gray))

    def detect_pupil(self, frame: np.ndarray) -> tuple[bool, dict]:
        """
        Detect pupil using Hough circle detection on IR preview frame.
        Returns (found, info_dict).
        Tune minRadius/maxRadius after seeing your actual IR preview.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (9, 9), 2)

        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=50,
            param1=50, # edge threshold, lower if pupil edges not detected
            param2=30, # circle threshold, lower = more lenient
            minRadius=20, # tune: how big is pupil in pixels at your WD?
            maxRadius=80 # tune: upper bound
        )

        if circles is None:
            return False, {}

        # Take strongest detected circle
        x, y, r = circles[0][0]
        h, w = frame.shape[:2]
        cx, cy = w // 2, h // 2

        # Check it's roughly centered (within 30% of frame center)
        centered = abs(x - cx) < w * 0.3 and abs(y - cy) < h * 0.3

        info = {
            "pupil_x": int(x), "pupil_y": int(y),
            "pupil_r": int(r), "centered": centered
        }
        logger.debug(f"Pupil detected: {info}")
        return centered, info

    def validate(self, frame: np.ndarray) -> tuple[bool, dict]:
        """Full quality check: focus + brightness only (on captured frame)"""
        focus = self.focus_score(frame)
        brightness = self.brightness_score(frame)
        focus_ok = focus > LAPLACIAN_THRESHOLD
        brightness_ok = MIN_BRIGHTNESS < brightness < MAX_BRIGHTNESS
        passed = focus_ok and brightness_ok
        metrics = {
            "focus_score": round(focus, 1),
            "brightness": round(brightness, 1),
            "focus_ok": focus_ok,
            "brightness_ok": brightness_ok,
            "passed": passed,
        }
        logger.info(f"Quality: {metrics}")
        return passed, metrics

    def ready_to_capture(self, preview_frame: np.ndarray) -> tuple[bool, dict]:
        """
        Called continuously on IR preview frames BEFORE triggering capture.
        Returns True only when pupil detected + image in focus.
        """
        focus = self.focus_score(preview_frame)
        focus_ok = focus > LAPLACIAN_THRESHOLD
        pupil_found, pupil_info = self.detect_pupil(preview_frame)
        ready = focus_ok and pupil_found
        info = {
            "focus_score": round(focus, 1),
            "focus_ok": focus_ok,
            "pupil_found": pupil_found,
            **pupil_info,
            "ready": ready,
        }
        logger.debug(f"Ready check: {info}")
        return ready, info
