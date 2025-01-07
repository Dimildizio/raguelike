import pygame
import time
import math
from utils.sprite_loader import SpriteLoader
from constants import *


class CombatAnimation:
    def __init__(self):
        self.sprite_loader = SpriteLoader(
            ORIGINAL_SPRITE_SIZE,
            PREPROCESSED_TILE_SIZE,
            DISPLAY_TILE_SIZE
        )
        self.slash_surface, _ = self.sprite_loader.load_sprite(SPRITES["SLASH"])
        self.is_playing = False
        self.start_time = 0
        self.attacker = None
        self.target = None
        self.original_pos = (0, 0)
        self.original_target_rotation = 0
        self.shake_offset = (0, 0)  # Store shake offset separately

    def start_attack(self, attacker, target):
        self.is_playing = True
        self.start_time = time.time()
        self.attacker = attacker
        self.target = target
        self.original_pos = (attacker.x, attacker.y)
        self.original_target_rotation = target.rotation
        self.shake_offset = (0, 0)

        # Calculate angle to face attacker
        dx = attacker.x - target.x
        dy = attacker.y - target.y
        angle = math.degrees(math.atan2(-dy, dx)) + 90
        self.target.base_rotation = angle

    def update(self):
        if not self.is_playing:
            return

        current_time = time.time()
        elapsed = current_time - self.start_time

        if elapsed > ATTACK_ANIMATION_DURATION:
            # Animation finished
            self.is_playing = False
            self.attacker.x, self.attacker.y = self.original_pos
            self.target.rotation = self.original_target_rotation
            self.shake_offset = (0, 0)
            return

        # Calculate animation progress (0 to 1)
        progress = elapsed / ATTACK_ANIMATION_DURATION

        # Move attacker
        if progress < 0.5:
            forward_progress = progress * 2
            self.move_attacker_forward(forward_progress)
        else:
            backward_progress = (progress - 0.5) * 2
            self.move_attacker_back(backward_progress)

        # Calculate shake offset (but don't modify target position)
        self.shake_offset = (
            math.sin(elapsed * SHAKE_FREQUENCY) * SHAKE_AMPLITUDE,
            math.cos(elapsed * SHAKE_FREQUENCY) * SHAKE_AMPLITUDE
        )

    def move_attacker_forward(self, progress):
        dx = self.target.x - self.original_pos[0]
        dy = self.target.y - self.original_pos[1]
        self.attacker.x = self.original_pos[0] + dx * ATTACK_DISTANCE * progress
        self.attacker.y = self.original_pos[1] + dy * ATTACK_DISTANCE * progress

    def move_attacker_back(self, progress):
        dx = self.target.x - self.original_pos[0]
        dy = self.target.y - self.original_pos[1]
        self.attacker.x = (self.original_pos[0] + dx * ATTACK_DISTANCE * (1 - progress))
        self.attacker.y = (self.original_pos[1] + dy * ATTACK_DISTANCE * (1 - progress))

    def get_target_draw_position(self, camera_x=0, camera_y=0):
        """Get the target's drawing position including shake offset"""
        if not self.is_playing or not self.target:
            return None

        return (
            self.target.x + self.shake_offset[0] - camera_x,
            self.target.y + self.shake_offset[1] - camera_y
        )

    def draw(self, screen, camera_x=0, camera_y=0):
        if not self.is_playing:
            return

        elapsed = time.time() - self.start_time

        # Draw slash effect in the middle of the animation
        if 0.2 <= elapsed <= 0.5:
            target_x = self.target.x + DISPLAY_TILE_SIZE // 2 - camera_x
            target_y = self.target.y + DISPLAY_TILE_SIZE // 2 - camera_y

            # Add shake offset to slash position
            target_x += self.shake_offset[0]
            target_y += self.shake_offset[1]

            slash_rect = self.slash_surface.get_rect(center=(target_x, target_y))
            screen.blit(self.slash_surface, slash_rect)