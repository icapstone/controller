
from gpiozero import PWMLED
from config import IR_GPIO, WHITE_GPIO
import logging

logger = logging.getLogger(__name__)

class IlluminationController:
    def __init__(self):
        try:
            self.ir = PWMLED(IR_GPIO)
            self.white = PWMLED(WHITE_GPIO)
            logger.info(f"Illumination initialized — IR GPIO{IR_GPIO}, White GPIO{WHITE_GPIO}")
        except Exception as e:
            logger.error(f"Failed to initialize illumination: {e}")
            raise

    def set_ir(self, level: float):
        """Set IR LED brightness (0.0 - 1.0)"""
        level = max(0.0, min(1.0, level))
        self.ir.value = level
        logger.debug(f"IR set to {level:.2f}")

    def set_white(self, level: float):
        """Set white LED brightness (0.0 - 1.0)"""
        level = max(0.0, min(1.0, level))
        self.white.value = level
        logger.debug(f"White set to {level:.2f}")

    def all_off(self):
        self.ir.off()
        self.white.off()
        logger.debug("All LEDs off")

    def cleanup(self):
        self.all_off()
        self.ir.close()
        self.white.close()
        logger.info("Illumination cleaned up")
