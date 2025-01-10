import math
import pygame
from .entity import Entity
from constants import *

import random
from systems.combat_stats import CombatStats


class Character(Entity):
    def __init__(self, x, y, sprite_path="PLAYER", game_state=None):
        super().__init__(x, y, SPRITES[sprite_path], SPRITES["OUTLINE_GREEN"], game_state=game_state)
        self.combat_stats = CombatStats(base_hp=PLAYER_START_HP, base_armor=PLAYER_START_ARMOR,
                                        base_damage=PLAYER_BASE_DAMAGE)
        self.name = 'Ready_player_1'
        self.facing = DIRECTION_PLAYER_START
        self.face_surface = pygame.image.load(SPRITES["HERO_FACE"]).convert_alpha()
        self.face_surface = pygame.transform.scale(self.face_surface, (256, 256))
        self.active_quests = []
        self.completed_quests = []
        self.inventory = []
        self.gold = 0

    def update(self):
            self.update_breathing()
            self.rotation = self.facing + self.current_angle
    
    def set_facing(self, direction):
        self.facing = direction

    def take_damage(self, amount):
        actual_damage = self.combat_stats.take_damage(amount)
        return actual_damage

    def accept_quest(self, quest_id: str) -> bool:
        """Accept a new quest if not already active or completed"""
        if quest_id not in self.active_quests and quest_id not in self.completed_quests:
            self.active_quests.append(quest_id)
            return True
        return False

    def complete_quest(self, quest_id: str):
        """Move quest from active to completed"""
        if quest_id in self.active_quests:
            self.active_quests.remove(quest_id)
            self.completed_quests.append(quest_id)

    def has_active_quest(self, quest_id: str) -> bool:
        """Check if a specific quest is active"""
        return quest_id in self.active_quests

    def has_completed_quest(self, quest_id: str) -> bool:
        """Check if a specific quest is completed"""
        return quest_id in self.completed_quests