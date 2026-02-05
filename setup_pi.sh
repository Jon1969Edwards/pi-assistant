#!/bin/bash
# ============================================
# Pi AI Assistant - Raspberry Pi Setup Script
# ============================================
# Run this script on your Raspberry Pi to install all dependencies

set -e

echo "=========================================="
echo "  Pi AI Assistant - Setup Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo -e "${YELLOW}Warning: This doesn't look like a Raspberry Pi${NC}"
    echo "Continuing anyway..."
fi

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo -e "${GREEN}Step 1: Updating system packages${NC}"
echo "-------------------------------------------"
sudo apt update && sudo apt upgrade -y

echo ""
echo -e "${GREEN}Step 2: Installing system dependencies${NC}"
echo "-------------------------------------------"
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-pygame \
    portaudio19-dev \
    python3-pyaudio \
    espeak-ng \
    libatlas-base-dev \
    libasound2-dev \
    alsa-utils \
    pulseaudio \
    bluetooth \
    bluez \
    bluez-tools

echo ""
echo -e "${GREEN}Step 3: Creating Python virtual environment${NC}"
echo "-------------------------------------------"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo ""
echo -e "${GREEN}Step 4: Installing Python packages${NC}"
echo "-------------------------------------------"
pip install --upgrade pip
pip install -r requirements.txt

# Install optional packages
echo ""
echo -e "${YELLOW}Installing optional packages (this may take a while)...${NC}"
pip install faster-whisper || echo "faster-whisper install failed, continuing..."
pip install vosk || echo "vosk install failed, continuing..."

echo ""
echo -e "${GREEN}Step 5: Installing Ollama${NC}"
echo "-------------------------------------------"
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "Ollama already installed"
fi

echo ""
echo -e "${GREEN}Step 6: Pulling LLM model${NC}"
echo "-------------------------------------------"
echo "Pulling qwen2:0.5b model (this may take a few minutes)..."
ollama pull qwen2:0.5b

echo ""
echo -e "${GREEN}Step 7: Downloading Vosk model${NC}"
echo "-------------------------------------------"
VOSK_MODEL_DIR="models"
VOSK_MODEL_NAME="vosk-model-small-en-us-0.15"
if [ ! -d "$VOSK_MODEL_DIR/$VOSK_MODEL_NAME" ]; then
    mkdir -p "$VOSK_MODEL_DIR"
    cd "$VOSK_MODEL_DIR"
    echo "Downloading Vosk model..."
    wget -q https://alphacephei.com/vosk/models/$VOSK_MODEL_NAME.zip
    unzip -q $VOSK_MODEL_NAME.zip
    rm $VOSK_MODEL_NAME.zip
    cd "$SCRIPT_DIR"
else
    echo "Vosk model already downloaded"
fi

echo ""
echo -e "${GREEN}Step 8: Setting up Piper TTS (optional)${NC}"
echo "-------------------------------------------"
pip install piper-tts || echo "Piper TTS install failed, will use pyttsx3 fallback"

echo ""
echo -e "${GREEN}Step 9: Configuring Bluetooth audio${NC}"
echo "-------------------------------------------"
# Add user to bluetooth group
sudo usermod -a -G bluetooth $USER

# Create simple script to connect bluetooth speaker
cat > connect_bluetooth.sh << 'EOF'
#!/bin/bash
# Connect to Bluetooth speaker
# Usage: ./connect_bluetooth.sh XX:XX:XX:XX:XX:XX

if [ -z "$1" ]; then
    echo "Usage: $0 <bluetooth-mac-address>"
    echo "Find your speaker's MAC with: bluetoothctl devices"
    exit 1
fi

bluetoothctl << END
power on
agent on
default-agent
connect $1
END
EOF
chmod +x connect_bluetooth.sh

echo ""
echo -e "${GREEN}Step 10: Creating autostart script${NC}"
echo "-------------------------------------------"
cat > start_assistant.sh << 'EOF'
#!/bin/bash
# Start the Pi AI Assistant

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Start Ollama in background if not running
if ! pgrep -x "ollama" > /dev/null; then
    ollama serve &
    sleep 3
fi

# Activate virtual environment and run
source venv/bin/activate
python main.py
EOF
chmod +x start_assistant.sh

echo ""
echo "=========================================="
echo -e "${GREEN}  Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Connect your Bluetooth speaker:"
echo "   bluetoothctl"
echo "   > scan on"
echo "   > pair XX:XX:XX:XX:XX:XX"
echo "   > connect XX:XX:XX:XX:XX:XX"
echo "   > trust XX:XX:XX:XX:XX:XX"
echo ""
echo "2. Test audio:"
echo "   speaker-test -t wav -c 2"
echo ""
echo "3. Start the assistant:"
echo "   ./start_assistant.sh"
echo ""
echo "4. For autostart on boot, add to /etc/rc.local:"
echo "   $SCRIPT_DIR/start_assistant.sh &"
echo ""
