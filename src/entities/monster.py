import math
import pygame as pg
from .entity import Entity
from constants import *
from systems.combat_stats import CombatStats
import random


class Monster(Entity):
    def __init__(self, x, y, sprite_path="MONSTER", name='Goblin', monster_type='goblin',
                 game_state=None, can_talk=True, description="vile greenskin creature"):
        super().__init__(x, y, SPRITES[sprite_path], SPRITES["OUTLINE_RED"], ap=60, game_state=game_state)
        self.name = name
        self.monster_type = monster_type
        self.is_hostile = True
        self.can_talk = can_talk
        self.description = description
        self.dialog_cooldown = DIALOGUE_COOLDOWN
        self.set_stats(MONSTER_PERSONALITY_TYPES, MONSTER_BASE_DAMAGE, MONSTER_BASE_ARMOR, MONSTER_BASE_HP)
        face_path = SPRITES["NPC_FACE_3"]
        self.face_surface = pg.image.load(face_path).convert_alpha()
        self.face_surface = pg.transform.scale(self.face_surface, (256, 256))

        self.interaction_history = []
        self.money = 40

    def set_stats(self, personality_types, dmg, armor, hp):
        # Set personality-based traits
        personalities = {'aggressive': {'aggression': random.uniform(1.0, 1.6),
                                        'bravery': random.uniform(0.75, 1.0),
                                        'dialogue_chance': 0.1,
                                        'dmg': 1.2, 'armor': 1, 'hp': 1},
                         'cautious': {'aggression': random.uniform(0.8, 1.4),
                                      'bravery': random.uniform(0.6, 0.8),
                                      'dialogue_chance': 0.3,
                                      'dmg': 1, 'armor': 1.2, 'hp': 1},
                         'territorial': {'aggression': random.uniform(1.2, 1.5),
                                         'bravery': random.uniform(0.7, 0.9),
                                         'dialogue_chance': 0.2,
                                         'dmg': 1, 'armor': 1, 'hp': 1},
                         'cowardly': {'aggression': random.uniform(0.7, 1.3),
                                      'bravery': random.uniform(0.4, 0.6),
                                      'dialogue_chance': 0.4,
                                      'dmg': 1, 'armor': 1, 'hp': 1.2}}

        self.personality = random.choice(personality_types)
        perc = personalities[self.personality]
        self.aggression = perc['aggression']
        self.bravery = perc['bravery']
        self.dialogue_chance = 1  # perc['dialogue_chance']
        self.combat_stats = CombatStats(base_hp=hp * perc['hp'],
                                        base_armor=armor * perc['armor'],
                                        base_damage=dmg * perc['dmg'])

    def attack(self, target):
        # Basic attack with random variation
        base_damage = self.combat_stats.damage * random.uniform(0.8, 1.2)

        # Personality affects critical hit chance
        crit_chance = CRITICAL_HIT_CHANCE
        if self.personality == "aggressive":
            crit_chance *= 1.5  # More likely to crit

        if random.random() < crit_chance:
            base_damage *= 2

        actual_damage = max(0, base_damage - target.combat_stats.armor)
        target.health -= actual_damage
        return actual_damage

    def take_damage(self, amount):
        actual_damage = self.combat_stats.take_damage(amount)
        if not self.is_alive:
            self.update_quest_progress()
        return actual_damage

    def should_flee(self):
        # More brave monsters will fight at lower health
        return (self.health / self.max_health) < self.bravery

    def wants_to_attack(self, distance):
        # More aggressive monsters will attack from further away
        return distance <= (MONSTER_AGGRO_RANGE * self.aggression)

    def count_dialogue_turns(self):
        self.dialog_cooldown += 1

    def update(self):
        self.update_breathing()

    def set_hostility(self, is_hostile: bool):
        """Change monster's hostility status"""
        self.is_hostile = is_hostile
        # Update outline color based on hostility
        self.outline = SPRITES["OUTLINE_RED"] if is_hostile else SPRITES["OUTLINE_YELLOW"]

    def get_dialogue_context(self):
        """Get context for dialog based on monster's state"""
        context = {
            "monster name": self.name,
            "monster type": self.monster_type,
            "personality": self.personality,
            "monster health": self.combat_stats.get_status(),
            "is_fleeing": self.should_flee(),
            "gold": self.money
        }
        return context

    def try_initiate_dialog(self, player_pos):
        """Try to initiate dialog with player"""
        if not self.can_talk or not self.is_hostile:
            return False
        if hasattr(self.game_state, 'current_npc') and self.game_state.current_npc == self:
            return False
        if self.dialog_cooldown > DIALOGUE_COOLDOWN:

            # Calculate distance to player
            dx = abs(self.x - player_pos[0])
            dy = abs(self.y - player_pos[1])
            distance = math.sqrt(dx * dx + dy * dy)

            if distance <= DIALOGUE_DISTANCE * DISPLAY_TILE_SIZE:  # and self.should_flee():
                if random.random() < self.dialogue_chance:
                    self.dialog_cooldown = 0

                    return True
            return False

    def update_quest_progress(self):
        """Update all relevant quest conditions when this monster dies"""
        if not self.game_state:
            return
        active_quests = self.game_state.quest_manager.get_active_quests()
        for quest in active_quests:
            for condition in quest.completion_conditions:
                if self.monster_type in condition.monster_tags:
                    print(
                        f"Monster {self.monster_type} killed, updating condition {condition.type} "
                        f"for quest {quest.quest_id}")
                    condition.current_value += 1

    def add_to_history(self, player_text, npc_response):
        # Add new interaction
        interaction = {
            "player": player_text,
            f"monster": npc_response
        }
        self.interaction_history.append(interaction)
        if len(self.interaction_history) > 10:
            self.interaction_history.pop(0)

    def detect_nearby_monsters(self, current_map, radius=5):
        """
        Detect other monsters within specified tile radius
        Returns list of (monster, distance) tuples
        """
        print('detecting')
        nearby_monsters = []
        monster_tile_x = int(self.x // DISPLAY_TILE_SIZE)
        monster_tile_y = int(self.y // DISPLAY_TILE_SIZE)

        # Check tiles in square area around monster
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                check_x = monster_tile_x + dx
                check_y = monster_tile_y + dy

                # Skip if outside map bounds
                if (dx == 0 and dy == 0) or not (
                        0 <= check_x < current_map.width and 0 <= check_y < current_map.height):
                    continue

                # Check if tile contains a monster
                tile = current_map.tiles[check_y][check_x]
                for entity in tile.entities:
                    if tile and entity and isinstance(entity, Monster) and entity.is_hostile:
                        # Calculate actual distance
                        distance = math.sqrt(dx * dx + dy * dy)
                        if distance <= radius:  # Only include if within circular radius
                            nearby_monsters.append((entity, distance))
        result = [(x[0], x[0].get_dialogue_context()) for x in sorted(
                   nearby_monsters, key=lambda x: x[1])] if nearby_monsters else ('', 'None')
        print(result)
        return result
