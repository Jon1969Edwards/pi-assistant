# Pi AI Assistant - Copilot Instructions

## Project Overview

A fully local voice-controlled AI assistant with animated face for Raspberry Pi. Inspired by Max Headroom-style retro AI aesthetics. Runs 100% on-device with no cloud dependencies.

## Architecture

```
main.py (PiAssistant)    ← Entry point, state machine, main loop
    ├── face.py          ← Pygame rendering, procedural face animation
    ├── voice.py         ← Wake word (Vosk) + transcription (faster-whisper)
    ├── llm.py           ← Ollama HTTP client for local LLM
    ├── tts.py           ← Piper TTS with pyttsx3 fallback
    └── config.py        ← All settings, platform detection
```

**State Machine Flow**: `IDLE → LISTENING → THINKING → SPEAKING → IDLE`

Each state change updates the face emotion via `face.set_emotion_for_state()`.

## Key Patterns

### Thread Communication
All heavy operations (voice recording, LLM calls, TTS) run in daemon threads. Communication uses `queue.Queue`:
- `speech_queue`: transcribed text from voice → main loop
- `response_queue`: LLM response + TTS completion signals → main loop

### Lazy Initialization
Components init dependencies on first use to speed startup:
```python
# voice.py pattern - follow this for new components
def _init_whisper(self):
    if self._whisper_model is None:
        # Load model...
```

### Graceful Degradation
Each module has fallbacks when dependencies are missing:
- `voice.py`: Mock transcription if faster-whisper unavailable
- `llm.py`: Mock responses if Ollama not running
- `tts.py`: pyttsx3 fallback if Piper not installed
- `face.py`: Procedural drawing if no sprites in `assets/faces/`

## Development Workflow

### Windows Testing
```powershell
.\setup_windows.ps1          # First-time setup
ollama serve                  # Terminal 1: Start Ollama
.\venv\Scripts\Activate.ps1   # Terminal 2: Activate venv
python main.py                # Run assistant
```

### Key Config Tweaks (config.py)
- `FULLSCREEN = False` for windowed testing
- `LLM_MODEL = "qwen2:0.5b"` for 4GB RAM Pi, `"phi3:mini"` for 8GB
- `WHISPER_MODEL = "tiny"` for Pi, `"base"` for more accuracy

## Component Integration Points

### Adding New Emotions
1. Add to `Emotion` enum in [face.py](../face.py)
2. Implement drawing in `_draw_procedural()` or add sprite to `assets/faces/<emotion>.png`
3. Map to `AssistantState` in `set_emotion_for_state()`

### Modifying LLM Behavior
- System prompt in `config.py → SYSTEM_PROMPT`
- Response length: `num_predict` in [llm.py](../llm.py#L89) (default 150 tokens for voice)
- Conversation history capped at 20 messages in `main.py`

### Wake Word
- Change `WAKE_WORD` in config.py (e.g., "hey max", "computer")
- Vosk model path: `models/vosk-model-small-en-us-0.15` or `~/.cache/vosk/`

## Platform Considerations

- `IS_RASPBERRY_PI` flag in config.py for platform-specific logic
- Pygame uses `FULLSCREEN` flag on Pi for kiosk mode
- Audio: sounddevice with 16kHz sample rate, mono channel

## Dependencies

Core optional dependencies (commented in requirements.txt):
- `faster-whisper`: Speech-to-text (heavy, ~500MB)
- `vosk`: Wake word detection (requires model download)
- `piper-tts`: High-quality TTS (install separately)

System packages needed on Pi: `portaudio19-dev`, `espeak-ng`
