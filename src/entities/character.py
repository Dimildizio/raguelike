import math
from .entity import Entity
from constants import *

import random
from systems.combat_stats import CombatStats


class Character(Entity):
    def __init__(self, x, y, sprite_path=SPRITES["PLAYER"]):
        super().__init__(x, y, sprite_path, SPRITES["OUTLINE_GREEN"])
        self.combat_stats = CombatStats(
            base_hp=PLAYER_START_HP,
            base_armor=PLAYER_START_ARMOR,
            base_damage=PLAYER_BASE_DAMAGE
        )
        self.facing = DIRECTION_PLAYER_START

    def update(self):
        self.update_breathing()
        self.rotation = self.facing + self.current_angle  # Add facing direction to breathing angle

    def attack(self, target):
        damage = self.combat_stats.base_damage * random.uniform(0.8, 1.2)
        target.health -= max(0, damage - target.combat_stats.base_armor)
        print('goblin', target.health)
    
    def set_facing(self, direction):
        self.facing = direction