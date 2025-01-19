from abc import ABC
import random
import pygame as pg
from constants import *
from utils.sprite_loader import SpriteLoader
from systems.combat_stats import CombatStats


class Entity(ABC):
    def __init__(self, x, y, sprite_path, outline_path=None, hp=100, ap=100, game_state=None):
        self.x = x
        self.y = y
        self.game_state = game_state
        self.sprite_loader = SpriteLoader(
            ORIGINAL_SPRITE_SIZE,
            PREPROCESSED_TILE_SIZE,
            DISPLAY_TILE_SIZE
        )
        self.name = 'No name'
        self.surface, self.pil_sprite = self.sprite_loader.load_sprite(sprite_path)
        self.outline = None
        self.is_passable = False

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

        self.max_action_points = ap
        self.action_points = ap
        self.combat_stats = CombatStats(base_hp=hp, base_armor=0, base_damage=10)


    def __repr__(self):
        return self.name

    def update_breathing(self):
        # Move current angle towards target angle
        if self.is_breathing_in:
            self.current_angle += self.breath_speed
            if self.current_angle >= self.target_angle:
                self.is_breathing_in = False
                self.breath_speed = random.uniform(0.5, 1.5) * BREATHING_SPEED
        else:
            self.current_angle -= self.breath_speed
            if self.current_angle <= -self.target_angle:
                self.is_breathing_in = True
                self.target_angle = random.uniform(-BREATHING_AMPLITUDE, BREATHING_AMPLITUDE)
                self.breath_speed = random.uniform(0.5, 1.5) * BREATHING_SPEED

        # Calculate total rotation (base + breathing)
        self.rotation = (self.base_rotation + self.current_angle) % 360

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

    def update(self):
        """Base update method that includes breathing animation"""
        self.update_breathing()

    def heal_self(self):
        pass

    @property
    def is_alive(self):
        return self.combat_stats and self.combat_stats.current_hp > 0  # Explicitly check current HP

    def take_damage(self, amount):
        if not self.is_alive:
            return 0
        dmg = self.combat_stats.take_damage(amount)
        return dmg

    def spend_action_points(self, amount):
        self.action_points = max(0, self.action_points - amount)

    def reset_action_points(self):
        self.action_points = self.max_action_points

    def can_do_action(self, action_price):
        return action_price <= self.action_points

class Remains(Entity):
    def __init__(self, x, y, sprite_path, name="remains", description="", game_state=None):
        super().__init__(x, y, sprite_path, None, game_state=game_state)  # No outline for remains
        self.name = name
        self.description = description
        self.is_passable = True  # Can walk over remains
        self.rotation = 0  # Remains don't rotate with breathing

    def update(self):
        pass

class Tree(Entity):
    def __init__(self, x, y, sprite_path, game_state=None, name='tree'):
        super().__init__(x, y, sprite_path, None, game_state=game_state)
        self.is_passable = False
        self.name= name

    def update(self):
        pass


class House(Entity):
    def __init__(self, x, y, name="Village House",
                 description="A cozy village house promises warmth and a bed for a night"):
        super().__init__(x, y, None)  # No sprite needed since tiles has visualization
        self.name = name
        self.description = description
        self.is_passable = False
        self.monster_type = 'house'
        self.last_response = None
        self.fee = SLEEP_FEE
        face_path = SPRITES["NPC_FACE_3"]
        self.face_surface = pg.image.load(face_path).convert_alpha()
        self.face_surface = pg.transform.scale(self.face_surface, (256, 256))


    def draw(self, screen, offset_x=0, offset_y=0):
        # No draw implementation needed since house tiles has visualization
        pass
