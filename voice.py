#!/usr/bin/env python3
"""
Voice Recognition Module
Handles wake word detection and speech-to-text transcription.
"""

import os
import threading
import queue
import numpy as np
from typing import Optional, Callable

# Suppress ONNX Runtime GPU warning on Pi (no GPU available)
os.environ["ORT_LOG_LEVEL"] = "3"

from config import (
    WAKE_WORD, WAKE_WORD_SENSITIVITY,
    SAMPLE_RATE, AUDIO_CHANNELS, WHISPER_MODEL,
    IS_RASPBERRY_PI
)


class VoiceRecognizer:
    """
    Voice recognition with wake word detection and speech transcription.
    Uses Vosk for wake word and faster-whisper for transcription.
    """
    
    def __init__(self):
        self.sample_rate = SAMPLE_RATE
        self.channels = AUDIO_CHANNELS
        
        # Audio recording state
        self.is_recording = False
        self.audio_queue = queue.Queue()
        
        # Wake word detection
        self.wake_word = WAKE_WORD.lower()
        self.wake_word_callback: Optional[Callable] = None
        self.wake_word_thread: Optional[threading.Thread] = None
        self.wake_word_running = False
        self.wake_word_paused = False  # Pause during processing
        
        # Initialize components lazily
        self._audio_interface = None
        self._whisper_model = None
        self._vosk_model = None
        self._vosk_recognizer = None
        
    def _init_audio(self):
        """Initialize audio interface."""
        if self._audio_interface is None:
            try:
                import sounddevice as sd
                self._audio_interface = sd
                print(f"Audio initialized: {sd.query_devices(kind='input')['name']}")
            except Exception as e:
                print(f"Warning: Could not initialize audio: {e}")
                print("Voice features will be disabled.")
                
    def _init_whisper(self):
        """Initialize Whisper model for transcription."""
        if self._whisper_model is None:
            try:
                from faster_whisper import WhisperModel

                print(f"Loading Whisper model '{WHISPER_MODEL}'...")
                # Suppress ONNX Runtime GPU warning during model load
                stderr_fd = os.dup(2)
                devnull = os.open(os.devnull, os.O_WRONLY)
                os.dup2(devnull, 2)
                try:
                    self._whisper_model = WhisperModel(
                        WHISPER_MODEL,
                        device="cpu",
                        compute_type="int8"
                    )
                finally:
                    os.dup2(stderr_fd, 2)
                    os.close(stderr_fd)
                    os.close(devnull)
                print("Whisper model loaded!")
            except ImportError:
                print("Warning: faster-whisper not installed. Using mock transcription.")
            except Exception as e:
                print(f"Warning: Could not load Whisper: {e}")
                print("Using mock transcription instead.")
                
    def _init_vosk(self):
        """Initialize Vosk for wake word detection."""
        if self._vosk_model is None:
            try:
                from vosk import Model, KaldiRecognizer
                import os
                
                # Try to find Vosk model
                model_path = "models/vosk-model-small-en-us-0.15"
                if not os.path.exists(model_path):
                    # Try alternative paths
                    alt_paths = [
                        os.path.expanduser("~/.cache/vosk/vosk-model-small-en-us-0.15"),
                        "/usr/share/vosk/models/small-en-us",
                    ]
                    for path in alt_paths:
                        if os.path.exists(path):
                            model_path = path
                            break
                            
                if os.path.exists(model_path):
                    print(f"Loading Vosk model from {model_path}...")
                    self._vosk_model = Model(model_path)
                    self._vosk_recognizer = KaldiRecognizer(self._vosk_model, self.sample_rate)
                    print("Vosk model loaded!")
                else:
                    print("Vosk model not found. Wake word detection disabled.")
                    print("Download from: https://alphacephei.com/vosk/models")
            except ImportError:
                print("Warning: Vosk not installed. Wake word detection disabled.")
            except Exception as e:
                print(f"Warning: Could not load Vosk: {e}")
                
    def start_wake_word_detection(self, callback: Callable):
        """Start listening for wake word in background."""
        self._init_audio()
        self._init_vosk()
        
        self.wake_word_callback = callback
        self.wake_word_running = True
        
        if self._vosk_recognizer and self._audio_interface:
            self.wake_word_thread = threading.Thread(
                target=self._wake_word_loop,
                daemon=True
            )
            self.wake_word_thread.start()
            print(f"Listening for wake word: '{self.wake_word}'")
        else:
            print("Wake word detection not available. Use SPACE or tap to activate.")
            
    def _wake_word_loop(self):
        """Background thread for wake word detection."""
        import json
        
        sd = self._audio_interface
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Audio status: {status}")
            self.audio_queue.put(bytes(indata))
            
        try:
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=8000,
                dtype='int16',
                channels=self.channels,
                callback=audio_callback
            ):
                while self.wake_word_running:
                    try:
                        data = self.audio_queue.get(timeout=0.5)
                        if self.wake_word_paused:
                            continue  # Discard audio while processing
                        if self._vosk_recognizer.AcceptWaveform(data):
                            result = json.loads(self._vosk_recognizer.Result())
                            text = result.get("text", "").lower()
                            if self.wake_word in text:
                                print(f"Wake word detected: '{text}'")
                                if self.wake_word_callback:
                                    self.wake_word_callback()
                    except queue.Empty:
                        continue
        except Exception as e:
            print(f"Wake word detection error: {e}")
            
    def check_wake_word(self) -> bool:
        """Manual check for wake word (called from main loop)."""
        # This is handled in background thread now
        return False
        
    def listen_and_transcribe(self, max_duration: float = 10.0) -> Optional[str]:
        """
        Record audio and transcribe to text.
        Records until silence is detected or max_duration is reached.
        """
        self._init_audio()
        self._init_whisper()
        
        if not self._audio_interface:
            return self._mock_transcription()
            
        sd = self._audio_interface
        
        print("Recording...")
        self.is_recording = True
        
        try:
            # Record audio
            audio_data = []
            silence_threshold = 500  # Adjust based on your mic
            silence_duration = 0
            max_silence = 1.5  # Seconds of silence before stopping
            
            def callback(indata, frames, time, status):
                if status:
                    print(f"Recording status: {status}")
                audio_data.append(indata.copy())
                
                # Check for silence
                volume = np.abs(indata).mean()
                nonlocal silence_duration
                if volume < silence_threshold:
                    silence_duration += frames / self.sample_rate
                else:
                    silence_duration = 0
                    
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='int16',
                callback=callback
            ):
                # Wait for speech and silence
                import time
                start_time = time.time()
                while self.is_recording:
                    if time.time() - start_time > max_duration:
                        print("Max duration reached")
                        break
                    if silence_duration > max_silence and len(audio_data) > 10:
                        print("Silence detected")
                        break
                    time.sleep(0.1)
                    
            self.is_recording = False
            
            if not audio_data:
                return None
                
            # Combine audio chunks
            audio = np.concatenate(audio_data, axis=0)
            
            # Convert to mono if stereo (take first channel)
            if audio.ndim > 1:
                audio = audio[:, 0]
            
            # Ensure 1D
            audio = audio.ravel()
            
            audio_float = audio.astype(np.float32) / 32768.0
            
            print(f"Transcribing {len(audio_float)} samples...")
            return self._transcribe(audio_float)
            
        except Exception as e:
            print(f"Recording error: {e}")
            self.is_recording = False
            return None
            
    def _transcribe(self, audio: np.ndarray) -> Optional[str]:
        """Transcribe audio using Whisper."""
        if self._whisper_model is None:
            return self._mock_transcription()
        
        # Skip if audio is too short
        if len(audio) < 1600:  # Less than 0.1 seconds
            print("Audio too short, skipping transcription")
            return None
            
        try:
            segments, info = self._whisper_model.transcribe(
                audio,
                language="en",
                beam_size=1,  # Faster
                best_of=1,
                vad_filter=True
            )
            
            text = " ".join(segment.text for segment in segments).strip()
            return text if text else None
            
        except Exception as e:
            print(f"Transcription error: {e}")
            return None
            
    def _mock_transcription(self) -> str:
        """Return mock transcription for testing without audio."""
        import random
        mock_phrases = [
            "Hello Max, how are you today?",
            "What's the weather like?",
            "Tell me a joke",
            "What time is it?",
            "Set a reminder for tomorrow",
        ]
        return random.choice(mock_phrases)
        
    def stop(self):
        """Stop all voice recognition."""
        self.is_recording = False
        self.wake_word_running = False
        if self.wake_word_thread:
            self.wake_word_thread.join(timeout=1.0)
