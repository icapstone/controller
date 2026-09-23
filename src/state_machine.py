# Device state machine with pupil-gated triggering

from enum import Enum, auto
import time
import logging
from config import (
    IR_BRIGHTNESS, WHITE_BRIGHTNESS,
    WHITE_FLASH_DURATION, ALIGN_SETTLE_TIME,
    UPLOAD_BATCH_SIZE,
    PUPIL_POLL_INTERVAL, PUPIL_STABLE_FRAMES,
)

logger = logging.getLogger(__name__)

class State(Enum):
    IDLE = auto()
    ALIGN = auto() # IR on, polling preview for pupil
    CAPTURE = auto() # pupil found — white flash + full capture
    VALIDATE = auto() # quality check captured frame
    SAVE = auto()
    UPLOAD = auto()
    ERROR = auto()

class DeviceStateMachine:

    def __init__(self, illumination, camera, analyzer, storage, uploader=None):
        self.illumination = illumination
        self.camera = camera
        self.analyzer = analyzer
        self.storage = storage
        self.uploader = uploader
        self.state = State.IDLE
        self.last_metrics = {}
        self.capture_count = 0
        self.fail_count = 0
        self._pending_upload = []

    def _wait_for_pupil(self, timeout: float = 30.0) -> tuple[bool, dict]:
        """
        Poll IR preview frames until pupil detected and stable.
        Returns (found, last_info).
        PUPIL_STABLE_FRAMES consecutive detections required before firing.
        Times out after `timeout` seconds.
        """
        stable_count = 0
        deadline = time.time() + timeout
        last_info = {}

        logger.info(f"Waiting for pupil (timeout={timeout}s, need {PUPIL_STABLE_FRAMES} stable frames)...")

        while time.time() < deadline:
            preview = self.camera.capture_preview()
            ready, info = self.analyzer.ready_to_capture(preview)
            last_info = info

            if ready:
                stable_count += 1
                logger.debug(f"Pupil stable: {stable_count}/{PUPIL_STABLE_FRAMES}")
                if stable_count >= PUPIL_STABLE_FRAMES:
                    logger.info(f"Pupil locked — triggering capture")
                    return True, info
            else:
                stable_count = 0  # reset if lost

            time.sleep(PUPIL_POLL_INTERVAL)

        logger.warning("Pupil detection timed out")
        return False, last_info

    def run_cycle(self) -> dict:
        result = {
            "success": False, "metrics": {},
            "filepath": None, "uploaded": False,
            "pupil_info": {}
        }

        try:
            # ALIGN: IR on, wait for pupil 
            self.state = State.ALIGN
            self.illumination.set_ir(IR_BRIGHTNESS)
            time.sleep(ALIGN_SETTLE_TIME)

            pupil_found, pupil_info = self._wait_for_pupil(timeout=30.0)
            result["pupil_info"] = pupil_info

            if not pupil_found:
                logger.warning("No pupil detected — skipping capture")
                self.illumination.all_off()
                return result

            # CAPTURE: white flash
            self.state = State.CAPTURE
            self.illumination.set_white(WHITE_BRIGHTNESS)
            time.sleep(WHITE_FLASH_DURATION)
            capture = self.camera.capture_full()
            self.illumination.set_white(0)
            self.illumination.set_ir(IR_BRIGHTNESS)

            # VALIDATE
            self.state = State.VALIDATE
            passed, metrics = self.analyzer.validate(capture)
            self.last_metrics = metrics
            result["metrics"] = metrics

            # SAVE
            self.state = State.SAVE
            label = "retina" if passed else "failed"
            filepath = self.storage.save(capture, label=label, metrics=metrics)
            result["filepath"] = filepath

            if passed:
                result["success"] = True
                self.capture_count += 1
                self._pending_upload.append(filepath)
                logger.info(f"Capture #{self.capture_count}: {filepath}")
            else:
                self.fail_count += 1
                logger.warning(f"Quality fail #{self.fail_count}: {metrics}")

            # UPLOAD batch
            if self.uploader and len(self._pending_upload) >= UPLOAD_BATCH_SIZE:
                self.state = State.UPLOAD
                batch = self._pending_upload.copy()
                upload_result = self.uploader.send_batch(batch)
                if upload_result["success"] == len(batch):
                    self._pending_upload.clear()
                    result["uploaded"] = True
                else:
                    failed = [r["path"] for r in upload_result["files"] if not r["success"]]
                    self._pending_upload = failed

        except Exception as e:
            self.state = State.ERROR
            logger.error(f"Cycle error: {e}", exc_info=True)
            self.illumination.all_off()
            result["error"] = str(e)

        self.state = State.IDLE
        return result

    def flush_uploads(self):
        if self.uploader and self._pending_upload:
            self.uploader.send_batch(self._pending_upload)
            self._pending_upload.clear()

    def status(self) -> dict:
        return {
            "state": self.state.name,
            "captures": self.capture_count,
            "fails": self.fail_count,
            "pending_upload": len(self._pending_upload),
            "last_metrics": self.last_metrics,
        }
