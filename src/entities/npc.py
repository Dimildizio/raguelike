import math
import random
from .entity import Entity
from constants import *


class NPC(Entity):
    def __init__(self, x, y, sprite_path=SPRITES["NPC"], name="Villager"):
        super().__init__(x, y, sprite_path, SPRITES["OUTLINE_YELLOW"])
        self.name = name
        self.health = NPC_BASE_HP
        self.armor = NPC_BASE_ARMOR
        # Slower, gentler breathing for NPCs
        self.breath_speed *= 0.7
        self.target_angle *= 0.6
        self.dialog_lines = []

    def update(self):
        self.update_breathing()
    def add_dialog(self, line):
        self.dialog_lines.append(line)
        
    def get_next_dialog(self):
        if self.dialog_lines:
            return self.dialog_lines[0]  # Could be made more sophisticated with conversation trees
        return "..."