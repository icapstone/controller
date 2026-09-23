# config.py: central configuration for retinal imaging device

# GPIO Pins
IR_GPIO = 17
WHITE_GPIO = 27

# Illumination levels (0.0 - 1.0)
IR_BRIGHTNESS = 0.8 # IR on during alignment
WHITE_BRIGHTNESS = 1.0 # Full white for capture flash

# Timing
WHITE_FLASH_DURATION = 0.15 # seconds, white flash for color capture
ALIGN_SETTLE_TIME = 0.3 # seconds, wait after IR on before capturing
CYCLE_INTERVAL = 5.0 # seconds between capture cycles

# Camera settings
CAMERA_WIDTH = 4608
CAMERA_HEIGHT = 2592
PREVIEW_WIDTH = 1280
PREVIEW_HEIGHT = 720
LENS_POSITION = 0 # 0 = infinity focus
EXPOSURE_TIME_US = 5000 # 5ms, freeze eye motion
ANALOGUE_GAIN = 4.0

# Image quality thresholds
LAPLACIAN_THRESHOLD = 80 # focus sharpness, lower = more lenient
MIN_BRIGHTNESS = 30
MAX_BRIGHTNESS = 230

# Storage
SAVE_DIR = "/home/icap123/captures"
SAVE_IR = True # also save the IR alignment frame
MAX_SAVES = 500 # stop saving after this many images

# Streaming (for live preview over network)
STREAM_PORT = 5000
STREAM_WIDTH = 1280
STREAM_HEIGHT = 720
STREAM_FPS = 30

# Upload / backend
# BACKEND_ENDPOINT = ""
# API_KEY = "" # set via environment: export RETINA_API_KEY=xxx
UPLOAD_BATCH_SIZE = 3 # upload after every N successful captures
UPLOAD_ENABLED = True # set False to disable uploads (local-only mode)

# Pupil detection / triggering
PUPIL_POLL_INTERVAL = 0.1 # seconds between preview grabs while aligning
PUPIL_STABLE_FRAMES = 3 # consecutive detections before firing capture
