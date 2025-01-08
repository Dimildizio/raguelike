import math
from .entity import Entity
from constants import *
from systems.combat_stats import CombatStats
import random


class Monster(Entity):
    def __init__(self, x, y, sprite_path="MONSTER"):
        super().__init__(x, y, SPRITES[sprite_path], SPRITES["OUTLINE_RED"])
        self.combat_stats = CombatStats(
            base_hp=MONSTER_BASE_HP,
            base_armor=MONSTER_BASE_ARMOR,
            base_damage=MONSTER_BASE_DAMAGE
        )
        # More aggressive breathing for monsters
        self.breath_speed *= 1.3
        self.target_angle *= 1.2
        self.facing = DIRECTION_DOWN

    def update(self):
        self.update_breathing()
        
    def attack(self, target):
        # Basic attack with random variation
        base_damage = self.combat_stats.damage * random.uniform(0.8, 1.2)
        if random.random() < CRITICAL_HIT_CHANCE:
            base_damage *= 2
        
        actual_damage = max(0, base_damage - target.combat_stats.armor)
        target.health -= actual_damage
        return actual_damage