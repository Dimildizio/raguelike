import math
from .entity import Entity
from constants import *
import random


class Monster(Entity):
    def __init__(self, x, y, sprite_path=SPRITES["MONSTER"]):
        super().__init__(x, y, sprite_path, SPRITES["OUTLINE_RED"])
        self.health = MONSTER_BASE_HP
        self.armor = MONSTER_BASE_ARMOR
        self.damage = MONSTER_BASE_DAMAGE
        # More aggressive breathing for monsters
        self.breath_speed *= 1.3
        self.target_angle *= 1.2

    def update(self):
        self.update_breathing()
        
    def attack(self, target):
        # Basic attack with random variation
        base_damage = self.damage * random.uniform(0.8, 1.2)
        if random.random() < CRITICAL_HIT_CHANCE:
            base_damage *= 2
        
        actual_damage = max(0, base_damage - target.armor)
        target.health -= actual_damage
        return actual_damage