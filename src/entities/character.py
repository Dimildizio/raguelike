import math
from .entity import Entity
from constants import *

import random


class Character(Entity):
    def __init__(self, x, y, sprite_path=SPRITES["PLAYER"]):
        super().__init__(x, y, sprite_path, SPRITES["OUTLINE_GREEN"])
        self.health = PLAYER_START_HP
        self.armor = PLAYER_START_ARMOR
        self.facing = DIRECTION_DOWN

    def update(self):
        self.update_breathing()
        self.rotation = self.facing + self.current_angle  # Add facing direction to breathing angle

    def attack(self, target):
        damage = PLAYER_BASE_DAMAGE
        target.health -= max(0, damage - target.armor)
    
    def set_facing(self, direction):
        self.facing = direction