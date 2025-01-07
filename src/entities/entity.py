from abc import ABC, abstractmethod
import pygame
import random
from constants import *
from utils.sprite_loader import SpriteLoader


class Entity(ABC):
    def __init__(self, x, y, sprite_path, outline_path=None):
        self.x = x
        self.y = y
        self.sprite_loader = SpriteLoader(
            ORIGINAL_SPRITE_SIZE,
            PREPROCESSED_TILE_SIZE,
            DISPLAY_TILE_SIZE
        )
        self.sprite = self.sprite_loader.load_sprite(sprite_path)
        self.outline = None
        if outline_path:
            self.outline = self.sprite_loader.load_sprite(outline_path)

        # Breathing animation properties
        self.rotation = 0
        self.current_angle = 0
        self.target_angle = random.uniform(-BREATHING_AMPLITUDE, BREATHING_AMPLITUDE)
        self.breath_speed = random.uniform(0.5, 1.5) * BREATHING_SPEED
        self.is_breathing_in = True  # Direction of breathing

    def update_breathing(self):
        # Move current angle towards target angle
        if self.is_breathing_in:
            self.current_angle += self.breath_speed
            if self.current_angle >= self.target_angle:
                # Reached target, start breathing out
                self.is_breathing_in = False
                # Choose new random speed for variety
                self.breath_speed = random.uniform(0.5, 1.5) * BREATHING_SPEED
        else:
            self.current_angle -= self.breath_speed
            if self.current_angle <= -self.target_angle:
                # Reached opposite point, start breathing in
                self.is_breathing_in = True
                # Choose new random target and speed
                self.target_angle = random.uniform(-BREATHING_AMPLITUDE, BREATHING_AMPLITUDE)
                self.breath_speed = random.uniform(0.5, 1.5) * BREATHING_SPEED

        # Update rotation (add base_rotation for characters that face different directions)
        self.rotation = self.current_angle

    def draw(self, screen, offset_x=0, offset_y=0):
        # Draw outline first (if exists) - no rotation
        if self.outline:
            outline_rect = self.outline.get_rect(center=(
                self.x + DISPLAY_TILE_SIZE // 2 + offset_x,
                self.y + DISPLAY_TILE_SIZE // 2 + offset_y
            ))
            screen.blit(self.outline, outline_rect)

        # Draw entity sprite with rotation
        rotated_sprite = pygame.transform.rotate(self.sprite, self.rotation)
        sprite_rect = rotated_sprite.get_rect(center=(
            self.x + DISPLAY_TILE_SIZE // 2 + offset_x,
            self.y + DISPLAY_TILE_SIZE // 2 + offset_y
        ))
        screen.blit(rotated_sprite, sprite_rect)
    @abstractmethod
    def update(self):
        pass

    def is_alive(self):
        return self.health > 0
    
    def take_damage(self, amount):
        self.health -= amount
        if self.health < 0:
            self.health = 0
        return self.health <= 0

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)