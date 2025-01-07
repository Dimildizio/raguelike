import math
import random
from .entity import Entity
from constants import *
from systems.combat_stats import CombatStats


class NPC(Entity):
    def __init__(self, x, y, sprite_path=SPRITES["NPC"], name="Villager"):
        super().__init__(x, y, sprite_path, SPRITES["OUTLINE_YELLOW"])
        self.name = name
        self.combat_stats = CombatStats(
            base_hp=PLAYER_START_HP,
            base_armor=PLAYER_START_ARMOR,
            base_damage=PLAYER_BASE_DAMAGE
        )
        # Slower, gentler breathing for NPCs
        self.breath_speed *= 0.7
        self.target_angle *= 0.6

        self.reputation = 50  # Start with neutral reputation
        self.active_quests = []
        self.interaction_history = []

    def update(self):
        self.update_breathing()

    def add_to_history(self, interaction):
        self.interaction_history.append(interaction)
        if len(self.interaction_history) > 10:  # Keep last 10 interactions
            self.interaction_history.pop(0)