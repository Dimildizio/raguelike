import pygame
from .entity import Entity
from constants import *
from systems.combat_stats import CombatStats


class Character(Entity):
    def __init__(self, x, y, sprite_path="PLAYER", game_state=None, voice='c'):
        super().__init__(x, y, SPRITES[sprite_path], SPRITES["OUTLINE_GREEN"], game_state=game_state, voice=voice)
        self.combat_stats = CombatStats(base_hp=PLAYER_START_HP, base_armor=PLAYER_START_ARMOR,
                                        base_damage=PLAYER_BASE_DAMAGE)
        self.name = 'Ready_player_1'
        self.facing = DIRECTION_PLAYER_START
        self.face_surface = pygame.image.load(SPRITES["HERO_FACE"]).convert_alpha()
        self.face_surface = pygame.transform.scale(self.face_surface, (256, 256))
        self.active_quests = []
        self.completed_quests = []
        self.inventory = []
        self.gold = 25

    def update(self):
        self.update_breathing()
        self.rotation = self.facing + self.current_angle

    def set_facing(self, direction):
        self.facing = direction

    def take_damage(self, amount, armor=True):
        actual_damage = self.combat_stats.take_damage(amount, armor)
        self.get_floating_nums(f"-{int(actual_damage)}", color=RED)
        self.game_state.add_message(f"You get hit for {int(actual_damage)} dmg", RED)
        self.check_dead()
        return actual_damage

    def spend_ap(self, val):
        self.action_points -= val
        self.action_points = max(self.action_points, 0)

    def check_dead(self):
        if not self.is_alive:
            self.game_state.change_state(GameState.DEAD)

    def accept_quest(self, quest_id: str) -> bool:
        """Accept a new quest if not already active or completed"""
        if quest_id not in self.active_quests and quest_id not in self.completed_quests:
            self.active_quests.append(quest_id)
            self.game_state.add_message(f"Quest {quest_id} accepted", YELLOW)
            return True
        return False

    def complete_quest(self, quest_id: str):
        """Move quest from active to completed"""
        if quest_id in self.active_quests:
            self.active_quests.remove(quest_id)
            self.completed_quests.append(quest_id)
            self.game_state.add_message(f"{quest_id} completed!", color=GREEN)

    def has_active_quest(self, quest_id: str) -> bool:
        """Check if a specific quest is active"""
        return quest_id in self.active_quests

    def has_completed_quest(self, quest_id: str) -> bool:
        """Check if a specific quest is completed"""
        return quest_id in self.completed_quests

    def add_gold(self, amount):
        """Add money to character's purse"""
        self.gold += amount
        self.game_state.add_message(f"Received {amount} gold", YELLOW)
        return self.gold

    def spend_gold(self, amount):
        """Try to spend money, return True if successful"""
        if self.gold >= amount:
            self.gold -= amount
            self.game_state.add_message(f"Lost {amount} gold", YELLOW)
            return True
        return False

    def heal_self(self, amount=0, ap_cost=10):
        if self.action_points >= ap_cost:
            self.action_points -= ap_cost
            amount = amount or self.combat_stats.max_hp
            self.combat_stats.get_healed(amount)
            self.get_floating_nums(f"+{int(amount)}", color=GREEN)
            self.game_state.add_message(f"You get healed by {amount}", GREEN)


    def get_dialogue_context(self):
        context = {"player_health": self.combat_stats.get_status()}
        return context
