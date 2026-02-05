# Windows Setup Script for Pi AI Assistant
# Run this in PowerShell to test the assistant on Windows before deploying to Pi

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Pi AI Assistant - Windows Setup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check Python
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found. Please install Python 3.10+ from python.org" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    python -m venv venv
}

# Activate venv
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "$ScriptDir\venv\Scripts\Activate.ps1"

# Install packages
Write-Host ""
Write-Host "Installing Python packages..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt

# Install optional packages
Write-Host ""
Write-Host "Installing optional packages..." -ForegroundColor Yellow
pip install faster-whisper 2>$null
pip install vosk 2>$null

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Checking Ollama" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Check for Ollama
$ollamaInstalled = $false
try {
    $ollamaVersion = ollama --version 2>&1
    $ollamaInstalled = $true
    Write-Host "Found Ollama: $ollamaVersion" -ForegroundColor Green
} catch {
    Write-Host "Ollama not installed." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To install Ollama:" -ForegroundColor White
    Write-Host "  1. Download from: https://ollama.com/download" -ForegroundColor Gray
    Write-Host "  2. Run the installer" -ForegroundColor Gray
    Write-Host "  3. After installation, run: ollama pull qwen2:0.5b" -ForegroundColor Gray
    Write-Host ""
}

if ($ollamaInstalled) {
    Write-Host ""
    Write-Host "Pulling LLM model (qwen2:0.5b)..." -ForegroundColor Yellow
    ollama pull qwen2:0.5b
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To run the assistant:" -ForegroundColor White
Write-Host ""
Write-Host "  1. Make sure Ollama is running:" -ForegroundColor Gray
Write-Host "     ollama serve" -ForegroundColor Yellow
Write-Host ""
Write-Host "  2. In a new terminal, activate venv and run:" -ForegroundColor Gray
Write-Host "     .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host "     python main.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "Controls:" -ForegroundColor White
Write-Host "  - Press SPACE to start talking" -ForegroundColor Gray
Write-Host "  - Press SPACE while speaking to cancel" -ForegroundColor Gray
Write-Host "  - Press ESC to quit" -ForegroundColor Gray
Write-Host ""
