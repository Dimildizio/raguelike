from abc import ABC, abstractmethod
import pygame
import random
from constants import *
from utils.sprite_loader import SpriteLoader


class Entity(ABC):
    def __init__(self, x, y, sprite_path, outline_path=None, hp=100, ap=100):
        self.x = x
        self.y = y
        self.sprite_loader = SpriteLoader(
            ORIGINAL_SPRITE_SIZE,
            PREPROCESSED_TILE_SIZE,
            DISPLAY_TILE_SIZE
        )
        self.surface, self.pil_sprite = self.sprite_loader.load_sprite(sprite_path)
        self.outline = None

        self.pil_outline = None
        if outline_path:
            self.outline, self.pil_outline = self.sprite_loader.load_sprite(outline_path)

        # Initialize rotation
        self.rotation = 0
        self.base_rotation = 0

        # Breathing animation properties
        self.current_angle = 0
        self.target_angle = random.uniform(-BREATHING_AMPLITUDE, BREATHING_AMPLITUDE)
        self.breath_speed = random.uniform(0.5, 1.5) * BREATHING_SPEED
        self.is_breathing_in = True  # Direction of breathing

        self.combat_stats = None

        self.max_health = hp
        self.health = hp
        self.max_action_points = ap
        self.action_points = ap
        self.armor = 0


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

        # Set rotation directly from current_angle
        self.rotation = self.base_rotation + self.current_angle


    def draw(self, screen, offset_x=0, offset_y=0):
        # Draw outline first (if exists) - no rotation
        if self.outline:
            outline_rect = self.outline.get_rect(center=(
                self.x + DISPLAY_TILE_SIZE // 2 + offset_x,
                self.y + DISPLAY_TILE_SIZE // 2 + offset_y
            ))
            screen.blit(self.outline, outline_rect)

        # Draw entity sprite with PIL-based rotation
        if self.pil_sprite:
            rotated_surface = self.sprite_loader.rotate_sprite(self.pil_sprite, self.rotation)
            if rotated_surface:
                sprite_rect = rotated_surface.get_rect(center=(
                    self.x + DISPLAY_TILE_SIZE // 2 + offset_x,
                    self.y + DISPLAY_TILE_SIZE // 2 + offset_y
                ))
                screen.blit(rotated_surface, sprite_rect)

    @abstractmethod
    def update(self):
        pass

    @property
    def is_alive(self):
        return self.combat_stats and self.combat_stats.current_hp > 0  # Explicitly check current HP

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)

    def take_damage(self, amount):
        if not self.is_alive:
            return 0

        actual_damage = max(1, amount - self.armor)  # Minimum 1 damage
        self.health -= actual_damage

        if self.health <= 0:
            self.health = 0
        return actual_damage


    def spend_action_points(self, amount):
        self.action_points = max(0, self.action_points - amount)

    def reset_action_points(self):
        self.action_points = self.max_action_points

    def can_do_action(self, action_price):
        return action_price <= self.action_points