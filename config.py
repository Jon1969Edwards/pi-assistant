# Pi AI Assistant Configuration
# Adjust these settings based on your hardware

import os
from pathlib import Path

# === PATHS ===
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
FACES_DIR = ASSETS_DIR / "faces"

# === DISPLAY SETTINGS ===
SCREEN_WIDTH = 800   # Adjust for your 5" screen
SCREEN_HEIGHT = 480  # Common 5" resolution
FULLSCREEN = False   # Set True on Pi for kiosk mode
FPS = 30

# === COLORS ===
BACKGROUND_COLOR = (20, 20, 30)      # Dark background
STATUS_READY = (100, 150, 255)       # Blue - ready for wake word
STATUS_LISTENING = (255, 100, 100)   # Red - recording voice
STATUS_THINKING = (255, 200, 100)    # Orange - LLM processing
STATUS_SPEAKING = (100, 255, 150)    # Green - speaking response

# === LLM SETTINGS ===
# Set to "openai" for cloud API (fast) or "ollama" for local (slow but offline)
LLM_BACKEND = os.environ.get("LLM_BACKEND", "openai")

# OpenAI settings
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o-mini"  # Fast and cheap

# Ollama settings (local fallback)
OLLAMA_HOST = "http://localhost:11434"
LLM_MODEL = "qwen2:0.5b"

# System prompt for the AI personality
SYSTEM_PROMPT = """You are Max, a friendly and helpful AI assistant living on a Raspberry Pi.
You have an expressive animated face and enjoy helping with tasks.
Keep responses concise (1-3 sentences) since you'll be speaking them aloud.
Be warm, slightly playful, and helpful."""

# === WAKE WORD SETTINGS ===
WAKE_WORD = "hey max"  # Can also use "computer", "assistant", etc.
WAKE_WORD_SENSITIVITY = 0.5  # 0.0 to 1.0

# === AUDIO SETTINGS ===
SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1

# === SPEECH RECOGNITION ===
# Whisper model sizes: tiny, base, small, medium, large
# For Pi 4: use "tiny" or "base"
WHISPER_MODEL = "tiny"

# === TEXT-TO-SPEECH ===
# Piper voice (will be downloaded on first run)
TTS_VOICE = "en_US-lessac-medium"
TTS_SPEED = 1.0

# === TOUCH SETTINGS ===
TOUCH_ENABLED = True
TAP_TO_LISTEN = True  # Tap screen to start listening (bypasses wake word)
TAP_TO_CANCEL = True  # Tap while speaking to cancel

# === PLATFORM DETECTION ===
IS_RASPBERRY_PI = os.path.exists('/proc/device-tree/model')
if IS_RASPBERRY_PI:
    with open('/proc/device-tree/model', 'r') as f:
        PI_MODEL = f.read()
else:
    PI_MODEL = "Windows/Development"
