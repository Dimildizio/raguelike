import math
import random
import pygame
from .entity import Entity
from constants import *
from systems.combat_stats import CombatStats


class NPC(Entity):
    def __init__(self, x, y, sprite_path=SPRITES["NPC"], name="Villager Amelia"):
        super().__init__(x, y, sprite_path, SPRITES["OUTLINE_YELLOW"])
        self.face_surface = pygame.image.load(SPRITES["NPC_FACE"]).convert_alpha()
        self.face_surface = pygame.transform.scale(self.face_surface, (256, 256))
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

    def add_to_history(self, player_text, npc_response):
        # Add new interaction
        interaction = {
            "player": player_text,
            f"npc": npc_response
        }
        self.interaction_history.append(interaction)
        if len(self.interaction_history) > 10:
            self.interaction_history.pop(0)