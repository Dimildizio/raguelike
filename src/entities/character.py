import random
import pygame
from .entity import Entity
from .monster import Monster
from .item import Item
from constants import *
from systems.combat_stats import CombatStats
from systems.skills_system import Skill


class Character(Entity):
    def __init__(self, x, y, sprite_path="PLAYER", game_state=None, voice='c', loading=False):
        super().__init__(x, y, sprite_path, SPRITES["OUTLINE_GREEN"], game_state=game_state, voice=voice, loading=loading)
        self.combat_stats = CombatStats(base_hp=PLAYER_START_HP, base_armor=PLAYER_START_ARMOR, max_damage=PLAYER_MAX_DAMAGE,
                                        base_damage=PLAYER_BASE_DAMAGE, ap=PLAYER_BASE_AP)
        if not loading:
            self.name = 'Ready_player_1'
            self.facing = DIRECTION_PLAYER_START
            self.face_path = SPRITES["HERO_FACE"]
            self.face_surface = pygame.image.load(SPRITES["HERO_FACE"]).convert_alpha()
            self.face_surface = pygame.transform.scale(self.face_surface, (256, 256))
            self.active_quests = []
            self.completed_quests = []
            self.skills = self.generate_skills()
            sword = Item('Basic sword', SPRITES["SWORD_1"], inv_sprite=SPRITES["SWORD_INV_1"], item_type="weapon",
                            description="Simple sword, sharp and balanced", price=40,
                            weight=5, equippable=True, slot='weapon', stats={'damage': 35}, game_state=game_state)
            self.inventory = [sword]
            self.inv_slots = {'head': None, 'body': None, 'weapon': sword, 'shield': None}
            self.gold = 25

    def use_skill(self, num, target=None):
        self.skills[num].skill_activated(target=target)

    def generate_skills(self):
        heal = Skill(self, name='heal', ap_cost=10, value=-100, cooldown=1, dist=1, image_path=SPRITES['SKILL_1'],
                     description='Heals a target',)
        damage = Skill(self, name='shout',  ap_cost=10, value=10, cooldown=1, dist=1, image_path=SPRITES['SKILL_2'],
                       description='Deal Damage to a target',)
        multiply = Skill(self, name='multiply', ap_cost=40, value=2, cooldown=4, dist=1, image_path=SPRITES['SKILL_3'],
                         description='Deal boosted damage to a target')
        breath = Skill(self, name='second_breath', ap_cost=5, value=30, cooldown=0, dist=1,
                       image_path=SPRITES['SKILL_3'], description='Recharge AP at the cost of taking damage')
        return [heal, damage, multiply, breath]

    def update(self):
        self.check_dead()
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
        self.combat_stats.spend_ap(val)

    @property
    def deal_dmg(self):
        weapon_dmg = 0
        if self.inv_slots['weapon']:
            weapon_dmg = self.inv_slots['weapon'].stats['damage']
        print(weapon_dmg)
        return self.combat_stats.get_dmg_val + weapon_dmg


    @property
    def get_ap_perc(self):
        return self.combat_stats.get_ap_perc

    def check_dead(self):
        if not self.is_alive:
            self.game_state.change_state(GameState.DEAD)

    def reset_turn(self):
        self.reset_action_points()
        for skill in self.skills:
            skill.update_cooldown()

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

    def heal_self(self, target=None, amount=0, ap_cost=10):
        if self.combat_stats.spend_ap(ap_cost):
            amount = amount or self.combat_stats.max_hp
            target.combat_stats.get_healed(amount)
            target.get_floating_nums(f"+{int(amount)}", color=GREEN)
            self.game_state.add_message(f"{target.name} gets healed by {amount}", GREEN)


    def get_dialogue_context(self):
        context = {"player_health": self.combat_stats.get_status()}
        return context

    def shout_intimidate(self, intimidation_level: int):
        damage = intimidation_level * 2  # 2-20 damage based on rating
        # Find all creatures within 5 tiles
        current_pos = (self.x // DISPLAY_TILE_SIZE, self.y // DISPLAY_TILE_SIZE)
        for y in range(max(0, current_pos[1] - 5), min(self.game_state.current_map.height, current_pos[1] + 6)):
            for x in range(max(0, current_pos[0] - 5), min(self.game_state.current_map.width, current_pos[0] + 6)):
                for entity in self.game_state.current_map.tiles[y][x].entities:
                    if isinstance(entity, Monster) and entity.is_alive:
                        dmg = random.randint(1, max(1, damage))
                        entity.take_damage(dmg, armor=False)
                        self.game_state.add_message(f"{entity.monster_type} {entity.name} was intimidated", YELLOW)

    def move_to_target(self, target_x, target_y, current_map):
        """Try to move towards target position using pathfinding
        Returns True if movement was made, False if no movement possible"""
        # Get current tile position
        start_x = self.x // DISPLAY_TILE_SIZE
        start_y = self.y // DISPLAY_TILE_SIZE

        # If we're already at the target tile, no need to move
        if start_x == target_x and start_y == target_y:
            return False

        # Check if target tile is adjacent
        dx = abs(target_x - start_x)
        dy = abs(target_y - start_y)
        movement_cost = self.game_state.current_map.get_movement_cost(start_x, start_y, target_x, target_y)
        if dx <= 1 and dy <= 1:  # Adjacent tile (including diagonals)
            if current_map.move_entity(self, target_x, target_y):
                return True
            return False

        # Find path to target tile
        path = current_map.find_path_to_target(start_x, start_y, target_x, target_y)

        # If no direct path exists, try to find path to closest reachable tile
        if not path:
            # Search in expanding radius around target for accessible tile
            for radius in range(1, 6):  # Check up to 5 tiles away
                for dy in range(-radius, radius + 1):
                    for dx in range(-radius, radius + 1):
                        check_x = target_x + dx
                        check_y = target_y + dy

                        # Skip if out of bounds
                        if not (0 <= check_x < current_map.width and 0 <= check_y < current_map.height):
                            continue

                        # Skip if tile is not passable
                        if not current_map.tiles[check_y][check_x].passable:
                            continue

                        # Try to find path to this tile
                        path = current_map.find_path_to_target(start_x, start_y, check_x, check_y)
                        if path:
                            break
                    if path:
                        break
                if path:
                    break

        # Try to move along the path if we have enough AP
        if path and self.can_do_action(MOVE_ACTION_COST):
            next_x, next_y = path[0]  # Get first step
            if current_map.move_entity(self, next_x, next_y):
                return True

        return False