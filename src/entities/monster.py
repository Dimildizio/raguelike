import math
import pygame as pg
from .entity import Entity, Remains, Tree
from constants import *
from systems.combat_stats import CombatStats
import random


class Monster(Entity):
    def __init__(self, x, y, sprite_path="MONSTER", name='Goblin', monster_type='goblin', voice='b', game_state=None,
                 can_talk=True, description="vile greenskin creature", ap=60, money=40, dmg=MONSTER_BASE_DAMAGE,
                 armor=MONSTER_BASE_ARMOR, hp=MONSTER_BASE_HP, max_damage=MONSTER_MAX_DAMAGE,
                 face_path=SPRITES["NPC_FACE_3"], loading=False):
        sprite_name = SPRITES[sprite_path] if not loading else sprite_path
        super().__init__(x, y, sprite_name, SPRITES["OUTLINE_RED"], ap=ap, game_state=game_state, voice=voice,
                         loading=loading)
        self.name = random.choice(MONSTER_NAMES['orkoids'])
        self.monster_type = monster_type
        self.is_hostile = True
        self.is_fleeing = False
        self.can_talk = can_talk
        self.description = description
        self.dialog_cooldown = DIALOGUE_COOLDOWN
        self.shout_cooldown = SHOUT_COOLDOWN
        self.sprite_key = sprite_path
        self.face_path = face_path
        self.face_surface = pg.image.load(face_path).convert_alpha()
        self.face_surface = pg.transform.scale(self.face_surface, (256, 256))

        self.interaction_history = []
        self.money = money
        self.entity_id = f"{monster_type}_{self.name}_{id(self)}"
        if not loading:
            self.set_stats(MONSTER_PERSONALITY_TYPES, dmg, max_damage, armor, hp, ap)

    def set_stats(self, personality_types, dmg, maxdmg, armor, hp, ap):
        # Set personality-based traits
        personalities = {'aggressive': {'aggression': random.uniform(1.0, 1.6),
                                        'bravery': random.uniform(0.1, 0.2),
                                        'dialogue_chance': 0.001,
                                        'dmg': 1.2, 'armor': 1, 'hp': 1},
                         'cautious': {'aggression': random.uniform(0.8, 1.4),
                                      'bravery': random.uniform(0.3, 0.5),
                                      'dialogue_chance': 0.005,
                                      'dmg': 1, 'armor': 1.2, 'hp': 1},
                         'territorial': {'aggression': random.uniform(1.2, 1.5),
                                         'bravery': random.uniform(0.2, 0.4),
                                         'dialogue_chance': 0.002,
                                         'dmg': 1, 'armor': 1, 'hp': 1},
                         'cowardly': {'aggression': random.uniform(0.7, 1.3),
                                      'bravery': random.uniform(0.4, 0.6),
                                      'dialogue_chance': 0.01,
                                      'dmg': 1, 'armor': 1, 'hp': 1.2}}

        self.personality = random.choice(personality_types)
        perc = personalities[self.personality]
        self.aggression = perc['aggression']
        self.chance_to_run = perc['bravery']
        self.dialogue_chance = perc['dialogue_chance']
        self.shout_chance = perc['dialogue_chance']
        self.combat_stats = CombatStats(base_hp=hp * perc['hp'],
                                        base_armor=armor * perc['armor'],
                                        base_damage=dmg * perc['dmg'],
                                        max_damage=maxdmg * perc['dmg'],
                                        ap=ap)

    def get_description(self):
        return f"You see {self.description}\n{self.monster_type.capitalize()} looks {self.combat_stats.get_status}"

    def attack(self, target):
        # Basic attack with random variation
        base_damage = self.deal_dmg
        # Personality affects critical hit chance
        crit_chance = CRITICAL_HIT_CHANCE
        if self.personality == "aggressive":
            crit_chance *= 1.5  # More likely to crit

        if random.random() < crit_chance:
            base_damage *= 2
            self.game_state.add_message(f"Critical hit!", RED)

        actual_damage = target.take_damage(base_damage)
        return actual_damage

    def take_damage(self, amount, armor=True):
        actual_damage = self.combat_stats.take_damage(amount, armor)
        self.get_floating_nums(f"-{actual_damage}", color=RED)
        self.game_state.add_message(f"{self.name} got hit for {int(actual_damage)} dmg", WHITE)
        if not self.is_alive:
            self.on_death()
        return actual_damage

    def heal_self(self, amount=0, ap_cost=10):
        if self.combat_stats.spend_ap(ap_cost):
            amount = amount or self.combat_stats.max_hp
            self.combat_stats.get_healed(amount)
            self.game_state.add_message(f"{self.monster_type} got healed for {amount}", WHITE)

    def on_death(self):
        dead = Remains(self.x, self.y, SPRITES[f"DEAD_{self.sprite_key.upper()}"],
                       name=f"Dead {self.monster_type}",
                       description=f"The remains of a {self.monster_type} {self.name}",game_state=self.game_state)
        print('created', type(dead))
        self.game_state.current_map.add_entity(dead, self.x // DISPLAY_TILE_SIZE, self.y // DISPLAY_TILE_SIZE)
        self.update_quest_progress()
        self.add_self_to_stats()
        self.game_state.add_message(f"{self.monster_type} dies", WHITE)
        if hasattr(self, 'rag_manager'):
            self.rag_manager.remove_entity_knowledge(self.entity_id)

    def add_self_to_stats(self):
        if self.monster_type in self.game_state.stats['monsters_killed']:
            self.game_state.stats['monsters_killed'][self.monster_type] += 1
        else:
            self.game_state.stats['monsters_killed'][self.monster_type] = 1

    def should_flee(self):
        # More brave monsters will fight at lower health
        return self.combat_stats.get_hp_perc < self.chance_to_run and random.random() < self.chance_to_run

    def lost_resolve(self):
        if self.should_flee() or self.is_fleeing:
            num = random.random()
            print(num, 'vs', self.chance_to_run)
            if num < self.chance_to_run * 0.05 and self.is_fleeing:  # chance to regain it
                if self.is_fleeing:
                    self.chance_to_run = max(0, self.chance_to_run - 0.1)
                    self.is_fleeing = False
                    self.game_state.add_message(f"{self.monster_type} routed", WHITE)
                    print(self.name, 'routed')
            else:
                self.is_fleeing = True
                print(self.name, 'is fleeing')

                self.game_state.add_message(f"{self.monster_type} flees for dear life", WHITE)
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
        self.game_state.add_message(f"{self.monster_type} {self.name} is "
                                    f"{'hostile' if self.is_hostile else 'friendly'}", YELLOW)

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

    def locate_target(self, current_map):
        return current_map.get_random_nearby_tile(self)

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
                self.game_state.add_message(
                    f"{self.monster_type} {self.name} initiates dialogue", WHITE)
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
                    self.game_state.add_message(
                        f"Monster {self.monster_type} killed, updating condition {condition.type} "
                        f"for quest {quest.quest_id}", YELLOW)
                    condition.current_value += 1

    def add_to_history(self, player_text, npc_response):
        # Add new interaction
        interaction = {
            "player": player_text,
            f"monster": npc_response
        }
        self.interaction_history.append(interaction)
        if len(self.interaction_history) > MEMORY_LIMIT:
            self.interaction_history.pop(0)
        if hasattr(self, 'rag_manager'):
            self.rag_manager.add_interaction(self.entity_id, interaction)

    def notify_nearby_entities(self, summary):
        """
        Notify all entities within 3 tiles of a conversation summary

        Args:
            summary: The conversation summary to share
        """
        if not (hasattr(self, 'x') and hasattr(self, 'y')):
            return

        # Get source entity's tile coordinates
        entity_tile_x = self.x // DISPLAY_TILE_SIZE
        entity_tile_y = self.y // DISPLAY_TILE_SIZE

        # Check all tiles within 3 tile radius
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                check_x = entity_tile_x + dx
                check_y = entity_tile_y + dy

                # Skip if outside map bounds
                if not (0 <= check_x < self.game_state.current_map.width and
                        0 <= check_y < self.game_state.current_map.height):
                    continue

                # Check entities in tile
                tile = self.game_state.current_map.tiles[check_y][check_x]
                for entity in tile.entities:
                    if (entity != self and
                            (isinstance(entity, Monster) or (hasattr(entity, 'monster_type')
                                                             and entity.monster_type == 'npc')
                            and hasattr(entity, 'interaction_history'))):
                        # Add overheard conversation to entity's knowledge
                        overheard = {
                            "type": "overheard",
                            "summary": f"Overheard nearby: {self.name} - {summary}"
                        }
                        if hasattr(entity, 'rag_manager'):
                            entity.rag_manager.add_interaction(entity.entity_id, overheard)
                        print(f'{entity.name} overheard that {overheard}')

    def decide_monster_action(self, distance):
        """Decide what action the monster should take based on its personality and situation"""
        # Should we flee?
        if self.lost_resolve():
                return "flee"
        # Should we attack?
        if distance == 1:  # Adjacent to player
            # Aggressive monsters are more likely to attack
            if random.random() < self.aggression:
                return "attack"
        # Should we approach?
        if distance <= MONSTER_AGGRO_RANGE:
            # Aggressive monsters are more likely to approach
            result = random.random()
            print(f'Lets attack: {result:.2f} vs {self.aggression:.2f}. flee: {result:.2f} vs {self.chance_to_run:.2f}')
            if result < self.aggression:
                return "approach"
        return "moveto"

    def decide_monster_action_llm(self, distance):
        """Decide what action the monster should take using LLM
        WARNING: Use only if got fast gpu since every action and every step any monster takes goes through llm"""
        # Get context for decision
        try:
            context = self.get_dialogue_context()
            context.update({
                'distance': distance,
                'dialog_cooldown': self.dialog_cooldown,
                'player_health': self.game_state.player.combat_stats.get_status(),
                'nearby_monsters': self.detect_nearby_monsters(self.game_state.current_map)
            })

            # Get decision from LLM
            decision = self.game_state.game.dialog_ui.dialogue_processor.decision_maker.get_decision(context)

            # Handle the decision
            if decision == 'flee' or self.lost_resolve():
                return 'flee'
            elif decision == 'talk' and self.can_talk and not self.dialog_cooldown:
                if self.try_initiate_dialog((self.game_state.player.x, self.game_state.player.y)):
                    return 'none'  # Dialog initiated, no other action needed
            elif decision == 'attack' and distance == 1:
                return 'attack'
            elif decision == 'approach' and distance <= MONSTER_AGGRO_RANGE:
                return 'approach'
            return 'none'  # Default to no action if decision can't be executed
        except Exception as e:  # Fallback
            print(f"Error in LLM decision: {str(e)}")
            return self.decide_monster_action(distance)

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
            check_x = int(monster_x + dx)
            check_y = int(monster_y + dy)
            if 0 <= check_x < current_map.width and 0 <= check_y < current_map.height:
                tile = current_map.tiles[check_y][check_x]
                if any(isinstance(entity, Tree) for entity in tile.entities):
                    return True
        return False

    def can_shout(self):
        """Check if monster can attempt to shout"""
        if self.shout_cooldown <= 0:
            if self.monster_type == 'green_troll' and random.random() < 0.9:
                self.shout_cooldown = SHOUT_COOLDOWN
                return True
            elif random.random() < self.shout_chance:
                self.shout_cooldown = SHOUT_COOLDOWN
                return True

    def get_shout_prompt(self):
        self.shout_cooldown = SHOUT_COOLDOWN
        return  f"""You are a {self.personality} {self.monster_type} named {self.name}. 
                    You cannot use emoji.
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


class GreenTroll(Monster):
    def __init__(self, x, y, game_state=None, sprite_path="GREEN_TROLL", name='Blaarggr', monster_type='green_troll',
                 voice='g', can_talk=True, description="an ugly hulking creature who likes to offend", ap=60, money=120,
                 dmg=MONSTER_BASE_DAMAGE *1.5, max_damage=MONSTER_MAX_DAMAGE*2, armor=MONSTER_BASE_ARMOR*1.5,
                 hp=MONSTER_BASE_HP*1.5, face_path=SPRITES["GREEN_TROLL_FACE"],loading=False):
        super().__init__(x, y, game_state=game_state, name=name, monster_type=monster_type, sprite_path=sprite_path,
                         voice=voice, can_talk=can_talk, description=description, loading=loading, ap=ap, money=money,
                         dmg=dmg, max_damage=max_damage, armor=armor, hp=hp, face_path=face_path)
        self.rage_chance = 0.1

    def take_damage(self, amount):
        actual_damage = self.combat_stats.take_damage(amount)
        self.get_floating_nums(f"-{actual_damage}", color=RED)
        if not self.is_alive:
            self.on_death()
        elif random.random() < self.rage_chance:
            self.get_enraged(actual_damage)
        return actual_damage

    def get_enraged(self, damage):
        print(f'{self.name} is enraged!')
        self.game_state.add_message(f"{self.monster_type} {self.name} is enraged!", color=YELLOW)
        rage = damage / self.combat_stats.max_hp
        self.combat_stats.get_healed(self.combat_stats.current_hp * rage)
        self.combat_stats.damage += self.combat_stats.damage * rage
        self.combat_stats.armor += self.combat_stats.armor * rage
        self.rage_chance /= 2

    def decide_monster_action(self, distance):
        """Decide what action the monster should take based on its personality and situation"""
        if distance == 1:  # Adjacent to player
            # Aggressive monsters are more likely to attack
            if random.random() < self.aggression:
                return "attack"
        # Should we approach?
        if distance <= MONSTER_AGGRO_RANGE:
            # Aggressive monsters are more likely to approach
            result = random.random()
            print(f'Lets attack: {result:.2f} vs {self.aggression:.2f}. flee: {result:.2f} vs {self.chance_to_run:.2f}')
            if result < self.aggression:
                return "approach"
        return "none"

class Dryad(Monster):
    def __init__(self, x, y, game_state=None, sprite_path="DRYAD", name='Elleinara', monster_type='dryad',
                 voice='j', can_talk=True, description="A mysterious tempting forest spirit", ap=70, money=100,
                 dmg=MONSTER_BASE_DAMAGE * 0.8, max_damage=MONSTER_MAX_DAMAGE * 0.8, armor=MONSTER_BASE_ARMOR*0.8,
                 hp=MONSTER_BASE_HP*0.8, face_path=SPRITES["DRYAD_FACE"], loading=False):
        super().__init__(x, y, game_state=game_state, name=name, monster_type=monster_type, sprite_path=sprite_path,
                         voice=voice, can_talk=can_talk, description=description, loading=loading, ap=ap, money=money,
                         dmg=dmg, max_damage=max_damage,  armor=armor, hp=hp, face_path=face_path)

        self.name = random.choice(MONSTER_NAMES['dryad'])
        self.transformed = False
        self.at_tree = False
        self.dialogue_chance = 0.5
        self.dialog_cooldown = 1

    def try_initiate_dialog(self, player_pos):
        """Override to make Dryad more likely to talk near trees"""
        if not self.can_talk or not self.is_hostile or self.transformed:
            return False
        if hasattr(self.game_state, 'current_npc') and self.game_state.current_npc == self:
            return False

        if self.dialog_cooldown > DIALOGUE_COOLDOWN and self.dist2player(player_pos, DIALOGUE_DISTANCE * 2):
            # Check if near a tree to increase dialogue chance
            self.at_tree = self.is_near_tree(self.game_state.current_map)
            if random.random() < self.dialogue_chance:
                self.dialog_cooldown = 0
                return True
        return False

    def can_transform(self):
        """Check if conditions are met for transformation"""
        if self.transformed or not self.is_near_tree(self.game_state.current_map):
            return False

        player = self.game_state.player
        # Check if player is within 2 tiles
        player_x = player.x // DISPLAY_TILE_SIZE
        player_y = player.y // DISPLAY_TILE_SIZE
        monster_x = self.x // DISPLAY_TILE_SIZE
        monster_y = self.y // DISPLAY_TILE_SIZE

        distance_to_player = math.sqrt(abs(player_x - monster_x)**2 + abs(player_y - monster_y)**2)
        return distance_to_player <= 2


    def transform(self):
        """Transform into powerful form or disappear with rewards"""
        if not self.transformed and self.at_tree:

            self.game_state.add_message(f"{self.monster_type} {self.name} transforms!", color=YELLOW)
            if random.random() < 0.4:  # 40% chance to be friendly
                # Give rewards and disappear
                self.set_hostility(False)
                self.game_state.player.gold += self.money
                self.game_state.player.combat_stats.get_healed()
                self.game_state.add_message(f"{self.monster_type} {self.name} disappears!", color=YELLOW)
                self.game_state.current_map.remove_entity(self)

                return "friendly"
            else:
                # Transform into powerful form
                self.transformed = True
                self.combat_stats.max_hp *= 3
                self.combat_stats.current_hp = self.combat_stats.max_hp
                self.combat_stats.damage *= 2
                self.combat_stats.armor *= 2
                self.game_state.add_message(f"{self.monster_type} {self.name} became more powerful!", color=YELLOW)
                return "hostile"
        return None

    def get_dialogue_context(self):
        """Add additional context for dialogue"""
        context = super().get_dialogue_context()
        context.update({
            "at_tree": self.at_tree,
            "transformed": self.transformed
        })
        return context

    def is_near_tree(self, current_map):
        """Check if monster is next to any tree"""
        monster_x = self.x // DISPLAY_TILE_SIZE
        monster_y = self.y // DISPLAY_TILE_SIZE
        # Check adjacent tiles for trees (including diagonals)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                check_x = int(monster_x + dx)
                check_y = int(monster_y + dy)
                if 0 <= check_x < current_map.width and 0 <= check_y < current_map.height:
                    tile = current_map.tiles[check_y][check_x]
                    if any(isinstance(entity, Tree) for entity in tile.entities):
                        return True
        return False

    def find_nearest_tree(self, current_map):
        """Find coordinates of the nearest tree"""
        monster_x = self.x // DISPLAY_TILE_SIZE
        monster_y = self.y // DISPLAY_TILE_SIZE
        nearest_tree = None
        min_distance = float('inf')

        # Search all tiles for trees
        for y in range(current_map.height):
            for x in range(current_map.width):
                tile = current_map.tiles[y][x]
                if any(isinstance(entity, Tree) for entity in tile.entities):
                    distance = abs(x - monster_x) + abs(y - monster_y)
                    if distance < min_distance and distance > 0:  # Ensure we don't target the tree we're already at
                        min_distance = distance
                        nearest_tree = (x, y)

        return nearest_tree

    def locate_target(self, current_map):
        if not self.at_tree:
            return self.find_nearest_tree(current_map)
        return 0, 0

    def update(self):
        if not self.transformed:  # Check for transformation conditions
            if self.can_transform():
                self.transform()
            else:
                self.update_breathing()  # Just do basic animations if not transformed
            return
        # Normal monster behavior after transformation
        super().update()

    def decide_monster_action(self, distance):
        """Decide what action the dryad should take"""
        if not self.transformed:
            current_map = self.game_state.current_map
            near_tree = self.is_near_tree(current_map)

            # Update tree status
            self.at_tree = near_tree

            # If near a tree, consider transformation or healing
            if near_tree:
                if self.can_transform():
                    self.transform()
                    return "none"
                else:
                    self.combat_stats.get_healed()  # Heal when near trees

                # If player is close, consider attacking
                if distance == 1 and random.random() < self.aggression:
                    return "attack"
                return "none"

            # If not near a tree, try to find one
            nearest_tree = self.find_nearest_tree(current_map)
            if nearest_tree:
                # Calculate distance to tree and player
                tree_x, tree_y = nearest_tree
                monster_x = self.x // DISPLAY_TILE_SIZE
                monster_y = self.y // DISPLAY_TILE_SIZE
                tree_distance = abs(tree_x - monster_x) + abs(tree_y - monster_y)

                # If player is closer than the tree and aggressive, might attack
                if distance < tree_distance and distance == 1 and random.random() < self.aggression:
                    return "attack"
                return "moveto"

            # If no trees found and player is close, might attack
            if distance == 1 and random.random() < self.aggression:
                return "attack"
            return "none"

        # If transformed, use standard monster behavior
        return super().decide_monster_action(distance)


class KoboldTeacher(Monster):
    def __init__(self, x, y, game_state=None, sprite_path="KOBOLD", name='Teacherrr', monster_type='kobold', voice='b',
                 can_talk=True, description="a small reptilian creature wearing tiny glasses", ap=45, money=3,
                 dmg=MONSTER_BASE_DAMAGE * 2, max_damage=MONSTER_MAX_DAMAGE * 2, armor=MONSTER_BASE_ARMOR * 0.6,
                 hp=MONSTER_BASE_HP * 0.6, face_path=SPRITES["KOBOLD_FACE"], loading=False):
        super().__init__(x, y, game_state=game_state, name=name, monster_type=monster_type, sprite_path=sprite_path,
                         voice=voice, can_talk=can_talk, description=description, loading=loading, ap=ap, money=money,
                         dmg=dmg, max_damage=max_damage,  armor=armor, hp=hp, face_path=face_path)
        self.dialog_cooldown = 1  # Override default cooldown
        self.has_passed_test = False
        self.dialogue_chance = 0.3  # More likely to initiate dialogue

    def get_dialogue_context(self):
        """Add additional context for dialogue"""
        context = super().get_dialogue_context()
        context.update({
            "has_passed_test": self.has_passed_test
        })
        return context

    def words_hurt(self, player, answer=False):
        if self.has_passed_test or answer:
            self.has_passed_test = True

            self.set_hostility(False)
            print("player passed the test")
        else:
            player.spend_ap(self.deal_dmg)
            player.take_damage(self.deal_dmg)
            self.game_state.add_message('Words hurt you!')

class HellBard(KoboldTeacher):
    def __init__(self, x, y, game_state=None, sprite_path="DEMON_BARD", name='Versifer', monster_type='demon_bard',
                 voice='d', can_talk=True, description="a melancholic figure in scorched robes holding a charred lute",
                 ap=66, money=666, dmg=MONSTER_BASE_DAMAGE * 0.5, max_damage=MONSTER_MAX_DAMAGE, loading=False,
                 armor=MONSTER_BASE_ARMOR * 0.5, hp=MONSTER_BASE_HP * 0.5, face_path=SPRITES["DEMON_BARD_FACE"]):
        super().__init__(x, y, game_state=game_state, name=name, monster_type=monster_type, sprite_path=sprite_path,
                         voice=voice, can_talk=can_talk, description=description, loading=loading, ap=ap, money=money,
                         dmg=dmg, max_damage=max_damage, armor=armor, hp=hp, face_path=face_path)
        self.dialogue_chance = 0.4  # Very chatty
        self.current_verse = None
        self.name = name

    def get_dialogue_context(self):
        """Add additional context for dialogue"""
        context = super().get_dialogue_context()
        context.update({
            "has_passed_rhyme": self.has_passed_test,
            "current_verse": self.current_verse
        })
        return context

    def words_hurt(self, player, rhymed=False):
        if self.has_passed_test or rhymed:
            self.has_passed_test = True
            self.set_hostility(False)
            print("player passed the rhyme test")
        else:
            gold = int(max(0, player.gold - self.combat_stats.damage))
            self.game_state.add_message(f'Rhymes hurt! You lost {int(player.gold-gold)} gold and {self.name} got stronger')
            player.gold = gold
            self.combat_stats.current_hp *= 1.1
            self.combat_stats.max_hp *= 1.1
            self.combat_stats.damage *= 1.1


class WillowWhisper(Monster):
    def __init__(self, x, y, game_state=None, sprite_path="WOLLOW", name='Lost Spirit',
                 monster_type='willow_whisper', voice='w', can_talk=True,
                 description="a faint, translucent figure surrounded by ethereal wisps",
                 ap=40, money=0, dmg=1, max_damage=1, armor=MONSTER_BASE_ARMOR * 0.2,
                 hp=MONSTER_BASE_HP * 4, face_path=SPRITES["WILLOW_FACE"], loading=False):
        super().__init__(x, y, game_state=game_state, name=name, monster_type=monster_type, loading=loading,
                         sprite_path=sprite_path, voice=voice, can_talk=can_talk, description=description,
                         ap=ap, money=money, dmg=dmg, max_damage=max_damage, armor=armor, hp=hp, face_path=face_path)

        self.dialog_cooldown = 1
        self.dialogue_chance = 0.3
        self.has_found_truth = False
        self.death_story = {'victim_name': 'placeholder'}
        if not loading:
            self.death_story = self.game_state.game.dialog_ui.dialogue_processor.generate_death_story()
        self.name = f"Spirit of {self.death_story['victim_name']}"
        self.discovered_clues = set()  # Track what the player has learned
        self.truth_requirements = 3



    def check_truth_discovery(self, player_input: str) -> bool:
        """Check if player's question/statement reveals new truth"""
        story = self.death_story
        new_discoveries = set()

        # Check each key detail against player input
        for detail in story['key_details']:
            if detail.lower() in player_input.lower() and detail not in self.discovered_clues:
                new_discoveries.add(detail)

        self.discovered_clues.update(new_discoveries)
        print('discovered clues: ', self.discovered_clues, 'story:', story['key_details'])
        # Check if player has discovered enough
        if len(self.discovered_clues) >= self.truth_requirements:
            self.has_found_truth = True
            self.set_hostility(False)
            return True

        return bool(new_discoveries)


    def decide_monster_action(self, distance):
        """Decide what action the monster should take based on its personality and situation"""
        # Should we flee?
        if self.is_hostile:
            self.words_hurt(self.game_state.player)
            return 'moveto'
        return "none"


    def words_hurt(self, player, discovered_new=False):
        """Spiritual damage when player fails to help or leaves too soon"""
        if self.has_found_truth or discovered_new or len(self.discovered_clues) >= self.truth_requirements:
            self.set_hostility(False)
        else:
            player.take_damage(self.combat_stats.damage, armor=False)
            self.heal_self(self.combat_stats.damage)
            self.game_state.add_message(f"The spirit's sorrow drains your life force!", RED)

    def update_breathing(self):
        """Override default breathing with continuous rotation"""
        # Increment rotation angle (adjust speed by changing the increment)
        self.rotation = (self.rotation + 0.5) % 360