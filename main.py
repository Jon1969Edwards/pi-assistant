#!/usr/bin/env python3
"""
Pi AI Assistant - Main Application
A local AI assistant with animated face, voice control, and LLM integration.
"""

import asyncio
import threading
import queue
import sys
from enum import Enum, auto

import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FULLSCREEN, FPS,
    BACKGROUND_COLOR, TOUCH_ENABLED, TAP_TO_LISTEN, TAP_TO_CANCEL
)
from face import FaceAnimator
from voice import VoiceRecognizer
from llm import LLMClient
from tts import TextToSpeech


class AssistantState(Enum):
    """Current state of the assistant."""
    IDLE = auto()           # Waiting for wake word
    LISTENING = auto()      # Recording user speech
    THINKING = auto()       # LLM is processing
    SPEAKING = auto()       # TTS is playing response


class PiAssistant:
    """Main application class for the Pi AI Assistant."""
    
    def __init__(self):
        # Initialize Pygame
        pygame.init()
        pygame.mixer.init()
        
        # Setup display
        flags = pygame.FULLSCREEN if FULLSCREEN else 0
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        pygame.display.set_caption("Pi AI Assistant")
        self.clock = pygame.time.Clock()
        
        # Initialize components
        self.face = FaceAnimator(self.screen)
        self.voice = VoiceRecognizer()
        self.llm = LLMClient()
        self.tts = TextToSpeech()
        
        # State management
        self.state = AssistantState.IDLE
        self.running = True
        
        # Message queues for thread communication
        self.speech_queue = queue.Queue()
        self.response_queue = queue.Queue()
        
        # Conversation history (for context)
        self.conversation = []
        
    def set_state(self, new_state: AssistantState):
        """Change the assistant's state and update face."""
        self.state = new_state
        self.face.set_emotion_for_state(new_state)
        if new_state == AssistantState.IDLE:
            self.voice.wake_word_paused = False
        
    def _handle_keydown(self, event):
        """Handle keyboard events."""
        if event.key == pygame.K_ESCAPE:
            self.running = False
        elif event.key == pygame.K_SPACE:
            self._handle_interaction()

    def _handle_touch(self):
        """Handle touch/mouse events."""
        if TAP_TO_LISTEN and self.state == AssistantState.IDLE:
            self.start_listening()
        elif TAP_TO_CANCEL and self.state == AssistantState.SPEAKING:
            self.cancel_speech()

    def _handle_interaction(self):
        """Handle user interaction (space bar or tap)."""
        if self.state == AssistantState.IDLE:
            self.start_listening()
        elif self.state == AssistantState.SPEAKING:
            self.cancel_speech()

    def handle_events(self):
        """Process pygame events (touch, keyboard, quit)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            elif event.type == pygame.MOUSEBUTTONDOWN and TOUCH_ENABLED:
                self._handle_touch()
                    
    def start_listening(self):
        """Start recording user speech."""
        if self.state != AssistantState.IDLE:
            return  # Ignore wake word if already processing
        self.voice.wake_word_paused = True
        self.set_state(AssistantState.LISTENING)
        
        # Start voice recording in background thread
        def record_and_transcribe():
            try:
                text = self.voice.listen_and_transcribe()
                if text:
                    self.speech_queue.put(text)
            except Exception as e:
                print(f"Voice recognition error: {e}")
                self.speech_queue.put(None)
                
        thread = threading.Thread(target=record_and_transcribe, daemon=True)
        thread.start()
        
    def cancel_speech(self):
        """Stop current speech output."""
        self.tts.stop()
        self.set_state(AssistantState.IDLE)
        
    def process_speech(self, text: str):
        """Send transcribed text to LLM and get response."""
        self.set_state(AssistantState.THINKING)
        
        # Add to conversation history
        self.conversation.append({"role": "user", "content": text})
        
        def get_response():
            try:
                response = self.llm.chat(self.conversation)
                self.response_queue.put(response)
            except Exception as e:
                print(f"LLM error: {e}")
                self.response_queue.put("Sorry, I had trouble thinking about that.")
                
        thread = threading.Thread(target=get_response, daemon=True)
        thread.start()
        
    def speak_response(self, text: str):
        """Speak the LLM response using TTS."""
        self.set_state(AssistantState.SPEAKING)
        
        # Add to conversation history
        self.conversation.append({"role": "assistant", "content": text})
        
        # Keep conversation history manageable (last 10 exchanges)
        if len(self.conversation) > 20:
            self.conversation = self.conversation[-20:]
        
        def speak():
            try:
                self.tts.speak(text)
            except Exception as e:
                print(f"TTS error: {e}")
            finally:
                # Signal speech complete
                self.response_queue.put("__SPEECH_DONE__")
                
        thread = threading.Thread(target=speak, daemon=True)
        thread.start()
        
    def check_wake_word(self):
        """Check for wake word in background (when idle)."""
        if self.state == AssistantState.IDLE and self.voice.check_wake_word():
            self.start_listening()
                
    def update(self):
        """Main update loop - check queues and update state."""
        # Check for transcribed speech
        try:
            text = self.speech_queue.get_nowait()
            if text:
                print(f"You said: {text}")
                self.process_speech(text)
            else:
                self.set_state(AssistantState.IDLE)
        except queue.Empty:
            pass
            
        # Check for LLM response
        try:
            response = self.response_queue.get_nowait()
            if response == "__SPEECH_DONE__":
                self.set_state(AssistantState.IDLE)
            elif self.state == AssistantState.THINKING:
                print(f"Max: {response}")
                self.speak_response(response)
        except queue.Empty:
            pass
            
        # Update face animation
        self.face.update()
        
    def render(self):
        """Render the display."""
        self.screen.fill(BACKGROUND_COLOR)
        self.face.draw()
        
        # Draw status indicator
        self.draw_status_indicator()
        
        pygame.display.flip()
        
    def draw_status_indicator(self):
        """Draw colored status bar at bottom of screen."""
        from config import STATUS_READY, STATUS_LISTENING, STATUS_THINKING, STATUS_SPEAKING
        
        colors = {
            AssistantState.IDLE: STATUS_READY,
            AssistantState.LISTENING: STATUS_LISTENING,
            AssistantState.THINKING: STATUS_THINKING,
            AssistantState.SPEAKING: STATUS_SPEAKING
        }
        
        color = colors.get(self.state, STATUS_READY)
        bar_height = 10
        pygame.draw.rect(
            self.screen, color,
            (0, SCREEN_HEIGHT - bar_height, SCREEN_WIDTH, bar_height)
        )
        
    def run(self):
        """Main application loop."""
        print("=" * 50)
        print("Pi AI Assistant Started!")
        print("=" * 50)
        print("Controls:")
        print("  - Press SPACE or tap screen to start listening")
        print("  - Tap while speaking to cancel")
        print("  - Press ESC to quit")
        print("=" * 50)
        
        # Start wake word detection in background
        self.voice.start_wake_word_detection(callback=self.start_listening)
        
        try:
            while self.running:
                self.handle_events()
                self.update()
                self.render()
                self.clock.tick(FPS)
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Clean up resources."""
        print("Shutting down...")
        self.voice.stop()
        self.tts.stop()
        pygame.quit()


def main():
    """Entry point."""
    try:
        assistant = PiAssistant()
        assistant.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
