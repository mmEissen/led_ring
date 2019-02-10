import os


_things_to_mock = os.environ.get("RING_MOCK", "").lower().split(",")

MOCK_RING = "ring" in _things_to_mock

PORT = int(os.environ.get("RING_PORT", 50000))
NUM_LEDS = int(os.environ.get("RING_NUM_LEDS", 60))

VOLUME_MIN_THRESHOLD = float(os.environ.get("RING_VOLUME_MIN", 0.001))
VOLUME_FALLOFF = float(os.environ.get("RING_VOLUME_FALLOFF", 32))
VOLUME_DEBUG = bool(os.environ.get("RING_VOLUME_DEBUG", 0))

FADE_FALLOFF = float(os.environ.get("RING_FADE_FALLOFF", 64))
COLOR_RATATION_PERIOD = float(os.environ.get("RING_COLOR_ROTATION_PERIOD", 180))

FIRST_OCTAVE = int(os.environ.get("RING_FIRST_OCTAVE", 4))
NUMBER_OCTAVES = int(os.environ.get("RING_NUMBER_OCTAVES", 8))

WINDOW_SIZE_SEC = float(os.environ.get("RING_WINDOW_SIZE_SEC", 0.1))