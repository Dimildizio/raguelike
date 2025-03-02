from abc import ABC
import random
import pygame as pg
from constants import *
from utils.sprite_loader import SpriteLoader
from systems.combat_stats import CombatStats
from systems.skills_system import Skill
import copy
import json
import uuid


class Entity(ABC):
    def __init__(self, x, y, sprite_path='', outline_path=None, hp=100, ap=100, game_state=None, voice='a',
                 loading=False):
        self.sprite_loader = SpriteLoader(
            ORIGINAL_SPRITE_SIZE,
            PREPROCESSED_TILE_SIZE,
            DISPLAY_TILE_SIZE
        )
        self.combat_stats = CombatStats(base_hp=hp, base_armor=0, base_damage=10, max_damage=15, ap=ap)

        self.uuid = str(uuid.uuid4())
        self.x = x
        self.y = y
        self.game_state = game_state
        self.sprite_path = sprite_path

        self.name = 'An object'
        self.voice = voice
        self.is_passable = False

        self.outline_path = outline_path
        self.outline = None
        self.surface = None
        self.pil_sprite = None
        self.pil_outline = None

        # Initialize rotation
        self.rotation = 0
        self.base_rotation = 0
        # Breathing animation properties
        self.current_angle = 0
        self.target_angle = random.uniform(-BREATHING_AMPLITUDE, BREATHING_AMPLITUDE)
        self.breath_speed = random.uniform(0.5, 1.5) * BREATHING_SPEED
        self.is_breathing_in = True  # Direction of breathing

        self.entity_id = f"{self.__class__.__name__.lower()}_{id(self)}"
        if not loading:
            self.surface, self.pil_sprite = self.sprite_loader.load_sprite(sprite_path)
            if outline_path:
                self.outline, self.pil_outline = self.sprite_loader.load_sprite(outline_path)

        if game_state and hasattr(game_state.game.dialog_ui.dialogue_processor, 'rag_manager'):
            self.rag_manager = game_state.game.dialog_ui.dialogue_processor.rag_manager
            if hasattr(self, 'can_talk') and self.can_talk and not loading:
                self.rag_manager._create_entity_index(self.entity_id, self.__class__.__name__.lower())

    @property
    def deal_dmg(self):
        return self.combat_stats.get_dmg_val

    def get_description(self):
        return f'You see {self.description.lower() if hasattr(self, "description") else self.name}'

    def save_entity(self):
        """Creates a dictionary of current attribute values"""
        save_dict = {'entity_class': self.__class__.__name__}
        for key, value in self.__dict__.items():
            # Skip certain attributes we don't want to save
            if key in {'rag_manager', 'sprite_loader', 'game_state', 'surface', 'outline', 'pil_sprite',
                       'pil_outline', 'face_surface'}:
                continue
            if key == 'combat_stats':
                save_dict['combat_stats'] = self.combat_stats.save_stats()
                continue
            if key == 'skills':
                save_dict['skills'] = [skill.save_skill() for skill in self.skills]
                continue
            if key == 'discovered_clues':
                save_dict['discovered_clues'] = list(self.discovered_clues)
                continue
            try:
                copied_value = copy.deepcopy(value)
                json.dumps(copied_value)  # Sanity check
                save_dict[key] = copied_value

            except Exception as e:
                print(f"Couldn't serialize {key}:", e)
                continue
        return save_dict

    def load_entity(self, save_dict, game_state):
        for key, value in save_dict.items():
            if key == 'combat_stats':
                self.combat_stats.load_stats(save_dict[key])
                continue
            if key == 'discovered_clues':
                self.discovered_clues = set(value)
                continue
            if key == 'skills':
                self.skills = [Skill(game_state.player).load_skill(skill_value) for skill_value in save_dict[key]]
                continue
            try:
                setattr(self, key, value)
            except Exception as e:
                print(f"Couldn't load {key}:", e)
        self.postload_entity(game_state)

    def postload_entity(self, game_state):
        try:
            self.game_state = game_state
            self.rag_manager = game_state.game.dialog_ui.dialogue_processor.rag_manager
            self.surface, self.pil_sprite = self.sprite_loader.load_sprite(self.sprite_path)
            if self.outline_path:
                self.outline, self.pil_outline = self.sprite_loader.load_sprite(self.outline_path)
            if hasattr(self, 'face_path'):
                self.face_surface = pg.image.load(self.face_path).convert_alpha()
                self.face_surface = pg.transform.scale(self.face_surface, (256, 256))
        except Exception as e:
            print(f"Couldn't load {self.name}:", e)

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

    def heal_self(self, target=None):
        pass

    @property
    def is_alive(self):
        return self.combat_stats and self.combat_stats.current_hp > 0  # Explicitly check current HP

    def take_damage(self, amount, armor=True):
        if not self.is_alive:
            return 0
        dmg = self.combat_stats.take_damage(amount, armor)
        return dmg

    def spend_action_points(self, amount):
        self.combat_stats.spend_ap(amount)

    def reset_action_points(self):
        self.combat_stats.reset_ap()

    def can_do_action(self, action_price):
        return action_price <= self.combat_stats.ap

    def use(self, *args):
        pass

    def get_floating_nums(self, txt, color=RED):
        self.game_state.floating_text_manager.add_text(txt, self.x + DISPLAY_TILE_SIZE // 2, self.y, color)


class Remains(Entity):
    def __init__(self, x, y, sprite_path='', name="remains", description="", game_state=None, loading=False):
        super().__init__(x, y, sprite_path, None, game_state=game_state, loading=loading)  # No outline for remains
        if not loading:
            self.name = name
            self.description = description
            self.is_passable = True  # Can walk over remains
            self.rotation = 0  # Remains don't rotate with breathing

    def update(self):
        pass

    def draw(self, screen, offset_x=0, offset_y=0):
        screen.blit(self.surface, (offset_x, offset_y))


class Tree(Entity):
    def __init__(self, x, y, sprite_path='', game_state=None, name='tree', loading=False):
        super().__init__(x, y, sprite_path, None, game_state=game_state, loading=loading)
        self.is_passable = False
        self.name = name

    def update(self):
        pass


class House(Entity):
    def __init__(self, x, y, name="Village House", voice='a', loading=False, sprite_path=None, game_state=None,
                 description="A cozy village house promises warmth and a bed for a night"):
        super().__init__(x, y, sprite_path, voice=voice, loading=loading)
        self.name = name
        self.description = description
        self.is_passable = False
        self.monster_type = 'house'
        self.last_response = None
        self.fee = SLEEP_FEE
        self.face_path = SPRITES["HOUSE_FACE"]
        if not loading:
            self.face_surface = pg.image.load(self.face_path).convert_alpha()
            self.face_surface = pg.transform.scale(self.face_surface, (256, 256))

    def draw(self, screen, offset_x=0, offset_y=0):
        # Override the parent draw method to draw the house part
        if self.surface:
            screen.blit(self.surface, (self.x + offset_x, self.y + offset_y))

