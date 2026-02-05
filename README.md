# Pi AI Assistant 🤖

A fully local, voice-controlled AI assistant with an animated face - inspired by [Max Headbox](https://github.com/syxanash/maxheadbox).

![Status](https://img.shields.io/badge/status-beta-yellow)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%204%2F5-red)
![Python](https://img.shields.io/badge/python-3.10+-blue)

## ✨ Features

- **100% Local** - All processing on-device, no cloud services
- **Animated Face** - Expressive emoji-style face that reacts to conversations
- **Voice Control** - Wake word detection + speech-to-text
- **Natural Speech** - High-quality text-to-speech responses
- **Touch Control** - Tap to speak, tap to cancel
- **Conversation Memory** - Maintains context across exchanges

## 🔧 Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Raspberry Pi | Pi 4 (4GB) | Pi 4/5 (8GB) |
| Display | 5" HDMI/GPIO | 5"+ touchscreen |
| Microphone | USB mic | Any USB mic |
| Speaker | Bluetooth/3.5mm | Bluetooth speaker |
| Storage | 16GB SD | 32GB+ SD |

## 📦 Software Stack

| Component | Used For |
|-----------|----------|
| [Ollama](https://ollama.com) | Local LLM runtime |
| [qwen2:0.5b](https://ollama.com/library/qwen2) | Language model (Pi 4 friendly) |
| [faster-whisper](https://github.com/guillaumekln/faster-whisper) | Speech-to-text |
| [Vosk](https://alphacephei.com/vosk/) | Wake word detection |
| [Piper TTS](https://github.com/rhasspy/piper) | Text-to-speech |
| [Pygame](https://pygame.org) | Display & animation |

## 🚀 Quick Start

### Windows (for testing)

```powershell
# Run the setup script
.\setup_windows.ps1

# Start Ollama (in one terminal)
ollama serve

# Run the assistant (in another terminal)
.\venv\Scripts\Activate.ps1
python main.py
```

### Raspberry Pi

```bash
# Make setup script executable and run
chmod +x setup_pi.sh
./setup_pi.sh

# Start the assistant
./start_assistant.sh
```

## 📁 Project Structure

```
pi-assistant/
├── main.py              # Main application entry
├── config.py            # Configuration settings
├── face.py              # Animated face system
├── voice.py             # Wake word & speech recognition
├── llm.py               # Ollama LLM integration
├── tts.py               # Text-to-speech
├── requirements.txt     # Python dependencies
├── setup_windows.ps1    # Windows setup script
├── setup_pi.sh          # Raspberry Pi setup script
└── assets/
    └── faces/           # (Optional) Custom face sprites
```

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Display
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
FULLSCREEN = True  # Set True for Pi kiosk mode

# LLM Model (use smaller for Pi 4)
LLM_MODEL = "qwen2:0.5b"   # 4GB RAM
# LLM_MODEL = "phi3:mini"  # 8GB RAM

# Wake word
WAKE_WORD = "hey max"

# Whisper model
WHISPER_MODEL = "tiny"  # tiny, base, small
```

## 🎮 Controls

| Input | Action |
|-------|--------|
| `SPACE` / Tap | Start listening |
| `SPACE` / Tap (while speaking) | Cancel response |
| `ESC` | Quit application |

## 🔊 Status Indicators

| Color | Meaning |
|-------|---------|
| 🔵 Blue | Ready - waiting for wake word |
| 🔴 Red | Listening - recording your voice |
| 🟠 Orange | Thinking - LLM processing |
| 🟢 Green | Speaking - playing response |

## 🔧 Bluetooth Speaker Setup

On Raspberry Pi:

```bash
# Enter bluetooth control
bluetoothctl

# Inside bluetoothctl:
power on
agent on
default-agent
scan on
# Wait for your speaker to appear, note the MAC address

pair XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
exit

# Test audio
speaker-test -t wav -c 2
```

## 📝 Customization

### Custom Face Sprites

Add PNG images to `assets/faces/` named:
- `neutral.png`
- `happy.png`
- `thinking.png`
- `listening.png`
- `speaking.png`

Images will be automatically scaled to fit.

### Custom Wake Words

Modify `WAKE_WORD` in `config.py`. The Vosk-based detection works with any phrase, though shorter, distinct phrases work best.

### Different LLM Models

```bash
# List available models
ollama list

# Pull a different model
ollama pull tinyllama
ollama pull phi3:mini  # Needs 8GB RAM
```

Then update `LLM_MODEL` in `config.py`.

## 🐛 Troubleshooting

### "Ollama not running"
```bash
ollama serve  # Start Ollama server
```

### No audio output
```bash
# Check audio devices
aplay -l

# Test speakers
speaker-test -t wav -c 2

# Set default output
pactl set-default-sink <sink_name>
```

### Wake word not detecting
- Check microphone: `arecord -l`
- Test recording: `arecord -d 5 test.wav && aplay test.wav`
- Ensure Vosk model is downloaded to `models/` folder

### Display issues on Pi
```bash
# For HDMI displays, ensure in /boot/config.txt:
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_cvt=800 480 60 6 0 0 0
```

## 📜 License

MIT License - feel free to modify and share!

## 🙏 Credits

- Inspired by [Max Headbox](https://github.com/syxanash/maxheadbox) by Simone Marzulli
- Built with [Ollama](https://ollama.com), [Pygame](https://pygame.org), and love
