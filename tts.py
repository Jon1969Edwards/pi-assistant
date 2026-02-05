#!/usr/bin/env python3
"""
Text-to-Speech Module
Handles speech synthesis using Piper TTS (local) or fallback to pyttsx3.
"""

import subprocess
import threading
import queue
import os
import tempfile
from pathlib import Path
from typing import Optional

from config import TTS_VOICE, TTS_SPEED, IS_RASPBERRY_PI


class TextToSpeech:
    """
    Text-to-speech synthesis using Piper (preferred) or pyttsx3 (fallback).
    Piper provides high-quality, fast local TTS perfect for Raspberry Pi.
    """
    
    def __init__(self):
        self.voice = TTS_VOICE
        self.speed = TTS_SPEED
        
        # Speech state
        self.is_speaking = False
        self.current_process: Optional[subprocess.Popen] = None
        self.speech_queue = queue.Queue()
        
        # Initialize TTS engine
        self._piper_available = self._check_piper()
        self._pyttsx_engine = None
        
        if not self._piper_available:
            self._init_pyttsx()
            
    def _check_piper(self) -> bool:
        """Check if Piper TTS is available."""
        try:
            result = subprocess.run(
                ["piper", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print("✓ Piper TTS available")
                return True
        except FileNotFoundError:
            print("⚠ Piper not found, will use fallback TTS")
        except Exception as e:
            print(f"⚠ Piper check failed: {e}")
        return False
        
    def _init_pyttsx(self):
        """Initialize pyttsx3 as fallback TTS."""
        try:
            import pyttsx3
            self._pyttsx_engine = pyttsx3.init()
            self._pyttsx_engine.setProperty('rate', int(150 * self.speed))
            
            # Try to set a decent voice
            voices = self._pyttsx_engine.getProperty('voices')
            for voice in voices:
                if 'english' in voice.name.lower():
                    self._pyttsx_engine.setProperty('voice', voice.id)
                    break
                    
            print("✓ pyttsx3 TTS initialized")
        except ImportError:
            print("⚠ pyttsx3 not installed. TTS will be disabled.")
            print("  Install with: pip install pyttsx3")
        except Exception as e:
            print(f"⚠ pyttsx3 init failed: {e}")
            
    def speak(self, text: str, blocking: bool = True):
        """
        Speak the given text.
        
        Args:
            text: Text to speak
            blocking: If True, wait for speech to complete
        """
        if not text:
            return
            
        self.is_speaking = True
        
        try:
            if self._piper_available:
                self._speak_piper(text, blocking)
            elif self._pyttsx_engine:
                self._speak_pyttsx(text, blocking)
            else:
                # No TTS available, just print
                print(f"[TTS disabled] Would say: {text}")
        finally:
            self.is_speaking = False
            
    def _speak_piper(self, text: str, blocking: bool):
        """Speak using Piper TTS."""
        try:
            # Create temp file for audio
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                wav_path = f.name
                
            # Run Piper to generate audio
            piper_cmd = [
                "piper",
                "--model", self.voice,
                "--output_file", wav_path
            ]
            
            self.current_process = subprocess.Popen(
                piper_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Send text to Piper
            self.current_process.communicate(input=text.encode('utf-8'), timeout=30)
            
            if os.path.exists(wav_path) and os.path.getsize(wav_path) > 0:
                # Play the audio
                self._play_audio(wav_path, blocking)
                
            # Cleanup
            try:
                os.unlink(wav_path)
            except OSError:
                pass
                
        except subprocess.TimeoutExpired:
            if self.current_process:
                self.current_process.kill()
            print("TTS timeout")
        except Exception as e:
            print(f"Piper TTS error: {e}")
            # Fallback to pyttsx if available
            if self._pyttsx_engine:
                self._speak_pyttsx(text, blocking)
                
    def _speak_pyttsx(self, text: str, blocking: bool):
        """Speak using pyttsx3."""
        if not self._pyttsx_engine:
            return
            
        try:
            if blocking:
                self._pyttsx_engine.say(text)
                self._pyttsx_engine.runAndWait()
            else:
                thread = threading.Thread(
                    target=self._pyttsx_speak_thread,
                    args=(text,),
                    daemon=True
                )
                thread.start()
        except Exception as e:
            print(f"pyttsx3 error: {e}")
            
    def _pyttsx_speak_thread(self, text: str):
        """Thread for non-blocking pyttsx speech."""
        try:
            self._pyttsx_engine.say(text)
            self._pyttsx_engine.runAndWait()
        except Exception as e:
            print(f"pyttsx3 thread error: {e}")
        finally:
            self.is_speaking = False
            
    def _play_audio(self, wav_path: str, blocking: bool):
        """Play a WAV file."""
        try:
            if IS_RASPBERRY_PI:
                # Use aplay on Linux/Pi
                cmd = ["aplay", "-q", wav_path]
            else:
                # Use pygame on Windows
                self._play_with_pygame(wav_path, blocking)
                return
                
            if blocking:
                self.current_process = subprocess.Popen(cmd)
                self.current_process.wait()
            else:
                self.current_process = subprocess.Popen(cmd)
                
        except Exception as e:
            print(f"Audio playback error: {e}")
            
    def _play_with_pygame(self, wav_path: str, blocking: bool):
        """Play audio using pygame (for Windows)."""
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(wav_path)
            pygame.mixer.music.play()
            
            if blocking:
                while pygame.mixer.music.get_busy():
                    if not self.is_speaking:  # Cancelled
                        pygame.mixer.music.stop()
                        break
                    pygame.time.wait(100)
        except Exception as e:
            print(f"Pygame audio error: {e}")
            
    def stop(self):
        """Stop any ongoing speech."""
        self.is_speaking = False
        
        # Kill current process if running
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=1)
            except Exception:
                try:
                    self.current_process.kill()
                except Exception:
                    pass
            self.current_process = None
            
        # Stop pyttsx if running
        if self._pyttsx_engine:
            try:
                self._pyttsx_engine.stop()
            except Exception:
                pass
                
        # Stop pygame mixer
        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass
            
    def set_voice(self, voice: str):
        """Change the TTS voice."""
        self.voice = voice
        
    def set_speed(self, speed: float):
        """Change the speech speed (0.5 to 2.0)."""
        self.speed = max(0.5, min(2.0, speed))
        if self._pyttsx_engine:
            self._pyttsx_engine.setProperty('rate', int(150 * self.speed))
