#!/usr/bin/env python3
"""
Face Animation System
Displays animated emoji faces that react to assistant state.
"""

import pygame
import math
import random
from enum import Enum, auto
from typing import Tuple, Optional
from pathlib import Path

from config import SCREEN_WIDTH, SCREEN_HEIGHT, FACES_DIR


class Emotion(Enum):
    """Face emotions/expressions."""
    NEUTRAL = auto()
    HAPPY = auto()
    THINKING = auto()
    LISTENING = auto()
    SPEAKING = auto()
    SURPRISED = auto()
    CONFUSED = auto()


class FaceAnimator:
    """
    Animated face display using procedural graphics.
    Falls back to simple geometric shapes if no sprite assets are found.
    """
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.center_x = SCREEN_WIDTH // 2
        self.center_y = SCREEN_HEIGHT // 2 - 20  # Slightly above center
        
        # Face dimensions
        self.face_radius = min(SCREEN_WIDTH, SCREEN_HEIGHT) // 3
        
        # Current emotion
        self.emotion = Emotion.NEUTRAL
        
        # Animation state
        self.animation_time = 0
        self.blink_timer = 0
        self.blink_duration = 0.15
        self.next_blink = random.uniform(2, 5)
        self.is_blinking = False
        
        # Speaking animation
        self.mouth_open = 0.0
        self.speaking_speed = 15
        
        # Bounce animation
        self.bounce_offset = 0
        
        # Try to load sprite faces if available
        self.sprites = self._load_sprites()
        
        # Colors
        self.face_color = (255, 220, 100)  # Yellow face
        self.eye_color = (40, 40, 40)       # Dark eyes
        self.mouth_color = (40, 40, 40)     # Dark mouth
        self.cheek_color = (255, 150, 150)  # Pink cheeks
        
    def _load_sprites(self) -> dict:
        """Try to load face sprite images."""
        sprites = {}
        if FACES_DIR.exists():
            for emotion in Emotion:
                sprite_path = FACES_DIR / f"{emotion.name.lower()}.png"
                if sprite_path.exists():
                    try:
                        img = pygame.image.load(str(sprite_path))
                        # Scale to fit face area
                        size = self.face_radius * 2
                        sprites[emotion] = pygame.transform.scale(img, (size, size))
                    except pygame.error:
                        pass
        return sprites
        
    def set_emotion(self, emotion: Emotion):
        """Set the current face emotion."""
        self.emotion = emotion
        
    def set_emotion_for_state(self, state):
        """Set emotion based on assistant state."""
        from main import AssistantState
        
        emotion_map = {
            AssistantState.IDLE: Emotion.NEUTRAL,
            AssistantState.LISTENING: Emotion.LISTENING,
            AssistantState.THINKING: Emotion.THINKING,
            AssistantState.SPEAKING: Emotion.SPEAKING,
        }
        self.emotion = emotion_map.get(state, Emotion.NEUTRAL)
        
    def update(self):
        """Update animation state."""
        dt = 1.0 / 30  # Assume 30 FPS
        self.animation_time += dt
        
        # Blink logic
        self.blink_timer += dt
        if not self.is_blinking and self.blink_timer >= self.next_blink:
            self.is_blinking = True
            self.blink_timer = 0
        elif self.is_blinking and self.blink_timer >= self.blink_duration:
            self.is_blinking = False
            self.blink_timer = 0
            self.next_blink = random.uniform(2, 5)
            
        # Speaking mouth animation
        if self.emotion == Emotion.SPEAKING:
            self.mouth_open = 0.5 + 0.5 * math.sin(self.animation_time * self.speaking_speed)
        else:
            self.mouth_open = max(0, self.mouth_open - dt * 5)
            
        # Bounce animation
        self.bounce_offset = 3 * math.sin(self.animation_time * 2)
        
    def draw(self):
        """Draw the animated face."""
        # Check for sprite first
        if self.emotion in self.sprites:
            self._draw_sprite()
        else:
            self._draw_procedural()
            
    def _draw_sprite(self):
        """Draw face using sprite image."""
        sprite = self.sprites[self.emotion]
        x = self.center_x - sprite.get_width() // 2
        y = self.center_y - sprite.get_height() // 2 + int(self.bounce_offset)
        self.screen.blit(sprite, (x, y))
        
    def _draw_procedural(self):
        """Draw face using procedural shapes."""
        cx = self.center_x
        cy = self.center_y + int(self.bounce_offset)
        r = self.face_radius
        
        # Main face circle
        pygame.draw.circle(self.screen, self.face_color, (cx, cy), r)
        pygame.draw.circle(self.screen, (200, 170, 80), (cx, cy), r, 3)  # Outline
        
        # Draw eyes
        self._draw_eyes(cx, cy, r)
        
        # Draw mouth
        self._draw_mouth(cx, cy, r)
        
        # Draw cheeks for happy emotion
        if self.emotion in [Emotion.HAPPY, Emotion.SPEAKING]:
            self._draw_cheeks(cx, cy, r)
            
        # Draw thinking indicators
        if self.emotion == Emotion.THINKING:
            self._draw_thinking_dots(cx, cy, r)
            
    def _draw_eyes(self, cx: int, cy: int, r: int):
        """Draw the eyes."""
        eye_y = cy - r // 4
        eye_spacing = r // 2
        eye_radius = r // 6
        
        for eye_x in [cx - eye_spacing // 2, cx + eye_spacing // 2]:
            if self.is_blinking:
                # Closed eye (line)
                pygame.draw.line(
                    self.screen, self.eye_color,
                    (eye_x - eye_radius, eye_y),
                    (eye_x + eye_radius, eye_y),
                    4
                )
            else:
                # Open eye
                pygame.draw.circle(self.screen, self.eye_color, (eye_x, eye_y), eye_radius)
                
                # Highlight
                highlight_offset = eye_radius // 3
                pygame.draw.circle(
                    self.screen, (255, 255, 255),
                    (eye_x - highlight_offset, eye_y - highlight_offset),
                    eye_radius // 3
                )
                
                # Listening: eyes look up
                if self.emotion == Emotion.LISTENING:
                    pygame.draw.circle(
                        self.screen, self.eye_color,
                        (eye_x, eye_y - eye_radius // 2),
                        eye_radius // 2
                    )
                    
    def _draw_mouth(self, cx: int, cy: int, r: int):
        """Draw the mouth."""
        mouth_y = cy + r // 3
        mouth_width = r // 2
        
        if self.emotion == Emotion.SPEAKING or self.mouth_open > 0.1:
            # Open mouth (ellipse)
            mouth_height = int(r // 4 * self.mouth_open)
            if mouth_height > 2:
                pygame.draw.ellipse(
                    self.screen, self.mouth_color,
                    (cx - mouth_width // 2, mouth_y - mouth_height // 2,
                     mouth_width, mouth_height)
                )
        elif self.emotion == Emotion.HAPPY:
            # Big smile (arc)
            rect = pygame.Rect(cx - mouth_width, mouth_y - r // 4, mouth_width * 2, r // 2)
            pygame.draw.arc(self.screen, self.mouth_color, rect, 3.14, 0, 4)
        elif self.emotion == Emotion.THINKING:
            # Small 'o' mouth
            pygame.draw.circle(self.screen, self.mouth_color, (cx, mouth_y), r // 10)
        elif self.emotion == Emotion.LISTENING:
            # Slight smile
            rect = pygame.Rect(cx - mouth_width // 2, mouth_y - r // 6, mouth_width, r // 3)
            pygame.draw.arc(self.screen, self.mouth_color, rect, 3.14, 0, 3)
        else:
            # Neutral smile
            pygame.draw.arc(
                self.screen, self.mouth_color,
                (cx - mouth_width // 2, mouth_y - r // 8, mouth_width, r // 4),
                3.14, 0, 3
            )
            
    def _draw_cheeks(self, cx: int, cy: int, r: int):
        """Draw rosy cheeks."""
        cheek_y = cy + r // 8
        cheek_offset = r // 2
        cheek_radius = r // 8
        
        for cheek_x in [cx - cheek_offset, cx + cheek_offset]:
            # Semi-transparent pink circles
            s = pygame.Surface((cheek_radius * 2, cheek_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.cheek_color, 100), (cheek_radius, cheek_radius), cheek_radius)
            self.screen.blit(s, (cheek_x - cheek_radius, cheek_y - cheek_radius))
            
    def _draw_thinking_dots(self, cx: int, cy: int, r: int):
        """Draw animated thinking dots above head."""
        dot_y = cy - r - 30
        num_dots = 3
        spacing = 20
        
        for i in range(num_dots):
            # Animate each dot with offset timing
            phase = self.animation_time * 3 + i * 0.5
            alpha = int(128 + 127 * math.sin(phase))
            dot_x = cx + (i - 1) * spacing
            
            s = pygame.Surface((12, 12), pygame.SRCALPHA)
            pygame.draw.circle(s, (150, 150, 255, alpha), (6, 6), 6)
            self.screen.blit(s, (dot_x - 6, dot_y - 6 - int(5 * math.sin(phase))))
