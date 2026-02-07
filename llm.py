#!/usr/bin/env python3
"""
LLM Integration Module
Supports OpenAI API (cloud) and Ollama (local) backends.
"""

import requests
from typing import List, Dict

from config import (
    LLM_BACKEND, OLLAMA_HOST, LLM_MODEL, SYSTEM_PROMPT,
    OPENAI_API_KEY, OPENAI_MODEL
)


class LLMClient:
    """
    LLM client supporting OpenAI (cloud) and Ollama (local) backends.
    """

    def __init__(self):
        self.system_prompt = SYSTEM_PROMPT
        self.backend = LLM_BACKEND
        self.available = False

        if self.backend == "openai":
            self.available = self._check_openai()
        else:
            self.host = OLLAMA_HOST
            self.model = LLM_MODEL
            self.available = self._check_ollama()

    def _check_openai(self) -> bool:
        """Check if OpenAI API key is configured."""
        if not OPENAI_API_KEY:
            print("⚠ OpenAI API key not set")
            print("  Set it with: export OPENAI_API_KEY='your-key-here'")
            return False
        print(f"✓ OpenAI configured, using model '{OPENAI_MODEL}'")
        return True

    def _check_ollama(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
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
                    return False
            return False
        except requests.exceptions.ConnectionError:
            print(f"⚠ Ollama not running at {self.host}")
            return False
        except Exception as e:
            print(f"⚠ Error checking Ollama: {e}")
            return False

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send chat messages and get a response."""
        if not self.available:
            return self._mock_response(messages)

        full_messages = [
            {"role": "system", "content": self.system_prompt}
        ] + messages

        try:
            if self.backend == "openai":
                return self._openai_chat(full_messages)
            else:
                return self._ollama_chat(full_messages)
        except Exception as e:
            print(f"LLM error: {e}")
            return "I'm having trouble thinking right now. Could you try again?"

    def _openai_chat(self, messages: List[Dict[str, str]]) -> str:
        """Chat via OpenAI API."""
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENAI_MODEL,
                "messages": messages,
                "max_tokens": 150,
                "temperature": 0.7,
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        else:
            raise RuntimeError(f"OpenAI error {response.status_code}: {response.text}")

    def _ollama_chat(self, messages: List[Dict[str, str]]) -> str:
        """Chat via local Ollama."""
        response = requests.post(
            f"{self.host}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "keep_alive": "30m",
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 75,
                    "num_ctx": 512,
                    "num_thread": 4,
                }
            },
            timeout=300
        )

        if response.status_code == 200:
            result = response.json()
            return result.get("message", {}).get("content", "").strip()
        else:
            raise RuntimeError(f"Ollama error: {response.status_code}")

    def _mock_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate a mock response when no LLM is available."""
        import random

        last_message = messages[-1]["content"].lower() if messages else ""

        if "hello" in last_message or "hi" in last_message:
            return random.choice([
                "Hello there! I'm Max, your friendly AI assistant. How can I help you today?",
                "Hi! Great to see you! What would you like to talk about?",
                "Hey! I'm here and ready to help!"
            ])
        elif "weather" in last_message:
            return "I'd love to tell you about the weather, but I'm running in demo mode. Set up an API key to unlock my full potential!"
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
                "That's an interesting question! I'm running in demo mode right now. Set up an API key to unlock my full potential!",
                "I'm in demo mode. Once you configure an LLM backend, I'll be much smarter!",
                "Hmm, I'd need a working LLM to give you a proper answer. For now, I'm just doing my best!",
            ])

    def generate_simple(self, prompt: str) -> str:
        """Simple text generation without conversation history."""
        return self.chat([{"role": "user", "content": prompt}])
