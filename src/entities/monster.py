import math
import pygame as pg
from .entity import Entity, Remains, Tree
from constants import *
from systems.combat_stats import CombatStats
import random


class Monster(Entity):
    def __init__(self, x, y, sprite_path="MONSTER", name='Goblin', monster_type='goblin', voice='b', game_state=None,
                 can_talk=True, description="vile greenskin creature", ap=60, money=40, dmg=MONSTER_BASE_DAMAGE,
                 armor=MONSTER_BASE_ARMOR, hp=MONSTER_BASE_HP, face_path=SPRITES["NPC_FACE_3"]):
        super().__init__(x, y, SPRITES[sprite_path], SPRITES["OUTLINE_RED"], ap=ap, game_state=game_state, voice=voice)
        self.name = name
        self.monster_type = monster_type
        self.is_hostile = True
        self.is_fleeing = False
        self.can_talk = can_talk
        self.description = description
        self.dialog_cooldown = DIALOGUE_COOLDOWN
        self.shout_cooldown = SHOUT_COOLDOWN
        self.set_stats(MONSTER_PERSONALITY_TYPES, dmg, armor, hp)
        self.face_surface = pg.image.load(face_path).convert_alpha()
        self.face_surface = pg.transform.scale(self.face_surface, (256, 256))

        self.interaction_history = []
        self.money = money

    def set_stats(self, personality_types, dmg, armor, hp):
        # Set personality-based traits
        personalities = {'aggressive': {'aggression': random.uniform(1.0, 1.6),
                                        'bravery': random.uniform(0.1, 0.2),
                                        'dialogue_chance': 0.01,
                                        'dmg': 1.2, 'armor': 1, 'hp': 1},
                         'cautious': {'aggression': random.uniform(0.8, 1.4),
                                      'bravery': random.uniform(0.3, 0.5),
                                      'dialogue_chance': 0.05,
                                      'dmg': 1, 'armor': 1.2, 'hp': 1},
                         'territorial': {'aggression': random.uniform(1.2, 1.5),
                                         'bravery': random.uniform(0.2, 0.4),
                                         'dialogue_chance': 0.02,
                                         'dmg': 1, 'armor': 1, 'hp': 1},
                         'cowardly': {'aggression': random.uniform(0.7, 1.3),
                                      'bravery': random.uniform(0.4, 0.6),
                                      'dialogue_chance': 0.1,
                                      'dmg': 1, 'armor': 1, 'hp': 1.2}}

        self.personality = random.choice(personality_types)
        perc = personalities[self.personality]
        self.aggression = perc['aggression']
        self.chance_to_run = perc['bravery']
        self.dialogue_chance = perc['dialogue_chance']
        self.shout_chance = perc['dialogue_chance']
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

        actual_damage = target.take_damage(base_damage)
        return actual_damage

    def take_damage(self, amount):
        actual_damage = self.combat_stats.take_damage(amount)
        self.get_floating_nums(f"-{actual_damage}", color=RED)
        if not self.is_alive:
            self.on_death()
        return actual_damage

    def heal_self(self, amount=0, ap_cost=10):
        if self.action_points >= ap_cost:
            self.action_points -= ap_cost
            amount = amount or self.combat_stats.max_hp
            self.combat_stats.get_healed(amount)


    def on_death(self):
        dead = Remains(self.x, self.y, SPRITES[f"DEAD_{self.monster_type.upper()}"], name=f"Dead {self.monster_type}",
                       description=f"The remains of a {self.monster_type} {self.name}",game_state=self.game_state)
        print('created', type(dead))
        self.game_state.current_map.add_entity(dead, self.x // DISPLAY_TILE_SIZE, self.y // DISPLAY_TILE_SIZE)
        self.update_quest_progress()

    def add_self_to_stats(self):
        if self.monster_type in self.game_state.stats['monsters_killed']:
            self.game_state.stats['monsters_killed'][self.monster_type] += 1
        else:
            self.game_state.stats['monsters_killed'][self.monster_type] = 1


    def should_flee(self):
        # More brave monsters will fight at lower health
        return self.combat_stats.get_hp_perc < self.chance_to_run

    def lost_resolve(self):
        if(self.should_flee() and random.random() < self.chance_to_run) or self.is_fleeing:
            num = random.random()
            print(num, 'vs', self.chance_to_run)
            if num < self.chance_to_run * 0.05 and self.is_fleeing:  # chance to regain it
                if self.is_fleeing:
                    self.chance_to_run = max(0, self.chance_to_run - 0.1)
                    self.is_fleeing = False
                    print(self.name, 'routed')
            else:
                self.is_fleeing = True
                print(self.name, 'is fleeing')
            return self.is_fleeing

    def count_dialogue_turns(self):
        self.dialog_cooldown += 1

    def update(self):
        self.update_breathing()

    def set_hostility(self, is_hostile: bool):
        """Change monster's hostility status"""
        self.is_hostile = is_hostile
        # Update outline color based on hostility
        self.outline, self.pil_outline = self.sprite_loader.load_sprite(SPRITES["OUTLINE_RED"] if is_hostile else SPRITES["OUTLINE_YELLOW"])


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

    def dist2player(self, player_pos, limit):
        dx = abs(self.x - player_pos[0])
        dy = abs(self.y - player_pos[1])
        distance = math.sqrt(dx * dx + dy * dy)
        return distance <= limit * DISPLAY_TILE_SIZE


    def try_initiate_dialog(self, player_pos):
        """Try to initiate dialog with player"""
        if not self.can_talk or not self.is_hostile:
            return False
        if hasattr(self.game_state, 'current_npc') and self.game_state.current_npc == self:
            return False
        if self.dialog_cooldown > DIALOGUE_COOLDOWN and self.dist2player(player_pos, DIALOGUE_DISTANCE):
            # and self.should_flee():
            rand = random.random()
            if rand < self.dialogue_chance:
                print(rand, self.dialogue_chance)
                self.dialog_cooldown = 0
                return True

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

    def find_nearest_edge_tree(self, current_map):
        """Find coordinates of nearest tree at map edge"""
        monster_x = self.x // DISPLAY_TILE_SIZE
        monster_y = self.y // DISPLAY_TILE_SIZE

        # Get all edge tiles with trees
        edge_trees = []

        # Check top and bottom edges
        for x in range(current_map.width):
            for y in [0, current_map.height - 1]:
                tile = current_map.tiles[y][x]
                if any(isinstance(entity, Tree) for entity in tile.entities):
                    distance = abs(monster_x - x) + abs(monster_y - y)
                    edge_trees.append((x, y, distance))

        # Check left and right edges
        for y in range(current_map.height):
            for x in [0, current_map.width - 1]:
                tile = current_map.tiles[y][x]
                if any(isinstance(entity, Tree) for entity in tile.entities):
                    distance = abs(monster_x - x) + abs(monster_y - y)
                    edge_trees.append((x, y, distance))

        # Return closest tree coordinates or None if no trees found
        if edge_trees:
            edge_trees.sort(key=lambda x: x[2])  # Sort by distance
            return edge_trees[0][0], edge_trees[0][1]
        return None

    def is_at_edge_tree(self, current_map):
        """Check if monster is next to a tree at the map edge"""
        monster_x = self.x // DISPLAY_TILE_SIZE
        monster_y = self.y // DISPLAY_TILE_SIZE
        print(monster_x, monster_y)
        # Check if at map edge
        is_at_edge = (monster_x <= 1 or monster_x >= current_map.width - 2 or
                      monster_y <= 1 or monster_y >= current_map.height - 2)
        if not is_at_edge:
            return False

        # Check adjacent tiles for trees
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            check_x = monster_x + dx
            check_y = monster_y + dy
            if 0 <= check_x < current_map.width and 0 <= check_y < current_map.height:
                tile = current_map.tiles[check_y][check_x]
                if any(isinstance(entity, Tree) for entity in tile.entities):
                    return True
        return False

    def get_shout_prompt(self):
        self.shout_cooldown = SHOUT_COOLDOWN
        return  f"""You are a {self.personality} {self.monster_type} named {self.name}. 
                    Extra info:{self.get_dialogue_context()}
                    Generate a single short battle shout or taunt (max 6 words).
                    Make it aggressive and characteristic for your monster type. You want to offend the player.
                    DO NOT use quotes or any punctuation except ! and ? or emoji.
                    You cannot include neither explanations nor descriptions nor actions.
                    Examples:
                    - Hell yeah, I'll kick uer arse!
                    - You're a whiny little bitch!
                    - Come here, cocksucker!
                    - Bow down to me, {self.name}!
                    - I will piss on your corpse!
                    - Your skull be mine toilet!
                    - Me smash puny human!
                    - Sorry I have to do it!
                    - You won't like it, dear!"""