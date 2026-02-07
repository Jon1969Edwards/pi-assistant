#!/usr/bin/env python3
"""
LLM Integration Module
Handles communication with Ollama for local LLM inference.
"""

import json
import requests
from typing import List, Dict, Optional, Generator

from config import OLLAMA_HOST, LLM_MODEL, SYSTEM_PROMPT


class LLMClient:
    """
    Client for Ollama local LLM server.
    Handles chat completions with conversation history.
    """
    
    def __init__(self):
        self.host = OLLAMA_HOST
        self.model = LLM_MODEL
        self.system_prompt = SYSTEM_PROMPT
        
        # Check if Ollama is available
        self.available = self._check_ollama()
        
    def _check_ollama(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                
                # Check for exact match or partial match
                model_found = any(
                    self.model in name or name.startswith(self.model.split(":")[0])
                    for name in model_names
                )
                
                if model_found:
                    print(f"✓ Ollama connected, model '{self.model}' available")
                    return True
                else:
                    print(f"⚠ Ollama running but model '{self.model}' not found")
                    print(f"  Available models: {model_names}")
                    print(f"  Run: ollama pull {self.model}")
                    return False
            return False
        except requests.exceptions.ConnectionError:
            print(f"⚠ Ollama not running at {self.host}")
            print("  Start Ollama with: ollama serve")
            return False
        except Exception as e:
            print(f"⚠ Error checking Ollama: {e}")
            return False
            
    def chat(self, messages: List[Dict[str, str]], stream: bool = False) -> str:
        """
        Send chat messages and get a response.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            stream: Whether to stream the response
            
        Returns:
            The assistant's response text
        """
        if not self.available:
            return self._mock_response(messages)
            
        # Prepare messages with system prompt
        full_messages = [
            {"role": "system", "content": self.system_prompt}
        ] + messages
        
        try:
            if stream:
                return self._chat_stream(full_messages)
            else:
                return self._chat_sync(full_messages)
        except Exception as e:
            print(f"LLM error: {e}")
            return "I'm having trouble thinking right now. Could you try again?"
            
    def _chat_sync(self, messages: List[Dict[str, str]]) -> str:
        """Synchronous chat completion."""
        response = requests.post(
            f"{self.host}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 75,   # Shorter responses = faster on Pi
                    "num_ctx": 512,      # Smaller context window for speed
                    "num_thread": 4,     # Use all Pi 4 cores
                }
            },
            timeout=300  # Long timeout for Pi CPU inference
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("message", {}).get("content", "").strip()
        else:
            raise RuntimeError(f"Ollama error: {response.status_code}")
            
    def _chat_stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """Streaming chat completion (yields chunks)."""
        response = requests.post(
            f"{self.host}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 75,
                    "num_ctx": 512,
                    "num_thread": 4,
                }
            },
            stream=True,
            timeout=60
        )
        
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    content = data.get("message", {}).get("content", "")
                    if content:
                        yield content
        else:
            raise RuntimeError(f"Ollama error: {response.status_code}")
            
    def _mock_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate a mock response when Ollama is not available."""
        import random
        
        last_message = messages[-1]["content"].lower() if messages else ""
        
        # Simple pattern matching for demo
        if "hello" in last_message or "hi" in last_message:
            return random.choice([
                "Hello there! I'm Max, your friendly AI assistant. How can I help you today?",
                "Hi! Great to see you! What would you like to talk about?",
                "Hey! I'm here and ready to help!"
            ])
        elif "weather" in last_message:
            return "I'd love to tell you about the weather, but I'm running locally and don't have internet access. Maybe check your phone?"
        elif "joke" in last_message:
            return random.choice([
                "Why do programmers prefer dark mode? Because light attracts bugs!",
                "I would tell you a UDP joke, but you might not get it.",
                "There are only 10 types of people: those who understand binary and those who don't!",
            ])
        elif "time" in last_message:
            from datetime import datetime
            now = datetime.now().strftime("%I:%M %p")
            return f"It's currently {now}. Time flies when you're having fun!"
        elif "name" in last_message:
            return "I'm Max! Your personal AI assistant living right here on this device."
        elif "how are you" in last_message:
            return random.choice([
                "I'm doing great! My circuits are humming nicely. How are you?",
                "Wonderful! Just sitting here, thinking at 30 frames per second. And you?",
                "Fantastic! Ready to help with whatever you need!"
            ])
        else:
            return random.choice([
                "That's an interesting question! I'm running in demo mode right now, so my answers are limited. Start Ollama to unlock my full potential!",
                "I'm in demo mode without Ollama. Once you start it, I'll be much smarter!",
                "Hmm, I'd need Ollama running to give you a proper answer. For now, I'm just doing my best!",
            ])
            
    def generate_simple(self, prompt: str) -> str:
        """Simple text generation without conversation history."""
        return self.chat([{"role": "user", "content": prompt}])
