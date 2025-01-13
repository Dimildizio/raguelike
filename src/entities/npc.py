import math
import random
import pygame
from .entity import Entity
from constants import *
from systems.combat_stats import CombatStats


class NPC(Entity):
    def __init__(self, x, y, sprite_path="NPC_1", face_path ='NPC_FACE_1', name="Villager Amelia", mood='playful',
                 game_state=None, description=''):
        super().__init__(x, y, SPRITES[sprite_path], SPRITES["OUTLINE_YELLOW"], game_state=game_state)
        self.last_response = "Hello traveler! How can I help you today?"
        self.monster_type = 'npc'
        self.name = name
        self.description = description
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

        self.money = 100  # Default starting money
        self.negotiated_rewards = {}  # Format: {quest_id: {"gold": amount, "items": [...]}}

    def negotiate_reward(self, quest_id: str, negotiated_amount: int):
        """Record negotiated reward amount for a quest"""
        if negotiated_amount <= self.money:  # Can't promise more than they have
            self.negotiated_rewards[quest_id] = {"gold": negotiated_amount}
            return f"Negotiated reward amount: {self.negotiated_rewards[quest_id]}"
        return False

    def negotiate_reward_prompt(self):
        negotiated_rewards_info = ""
        if hasattr(self, 'negotiated_rewards') and self.negotiated_rewards:
            negotiated_rewards_info = "\nNegotiated quest rewards:"
            for quest_id, reward in self.negotiated_rewards.items():
                negotiated_rewards_info += f"\n- {quest_id}: {reward['gold']} gold"
        return negotiated_rewards_info

    def pay_reward(self, quest_id: str, original_reward: dict) -> dict:
        """
        Attempt to pay the negotiated or original reward
        Returns the actual reward given, even if partial
        """
        if quest_id not in self.negotiated_rewards:
            # No negotiation happened, use original reward
            reward_amount = original_reward.get("amount", 0)
        else:
            # Use negotiated amount
            reward_amount = self.negotiated_rewards[quest_id]["gold"]

        # Pay what we can, even if it's less than promised
        actual_reward = min(reward_amount, self.money)
        if actual_reward > 0:
            self.money -= actual_reward

            # Clear negotiation record
            if quest_id in self.negotiated_rewards:
                del self.negotiated_rewards[quest_id]

            return {"type": "gold", "amount": actual_reward}
        return {"type": "gold", "amount": 0}

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