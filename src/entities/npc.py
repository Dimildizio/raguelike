import math
import random
import pygame
from .entity import Entity
from constants import *
from systems.combat_stats import CombatStats


class NPC(Entity):
    def __init__(self, x, y, sprite_path="NPC_1", face_path ='NPC_FACE_1', name="Villager Amelia", mood='playful'):
        super().__init__(x, y, SPRITES[sprite_path], SPRITES["OUTLINE_YELLOW"])
        self.last_response = "Hello traveler! How can I help you today?"
        self.name = name
        self.mood = mood  # Possible values: 'playful', 'silly', 'friendly', 'neutral', 'greedy', 'vicious', 'unfriendly
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

        face_path = SPRITES[face_path] or SPRITES["NPC_FACE_1"]
        self.face_surface = pygame.image.load(face_path).convert_alpha()
        self.face_surface = pygame.transform.scale(self.face_surface, (256, 256))

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
        print(f'line added {interaction}.\nmood: {self.mood}')