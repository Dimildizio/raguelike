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
            self.game_state.add_message(f"Critical hit!", RED)

        actual_damage = target.take_damage(base_damage)
        return actual_damage

    def take_damage(self, amount):
        actual_damage = self.combat_stats.take_damage(amount)
        self.get_floating_nums(f"-{actual_damage}", color=RED)
        self.game_state.add_message(f"{self.name} got hit for {int(actual_damage)} dmg", WHITE)
        if not self.is_alive:
            self.on_death()
        return actual_damage

    def heal_self(self, amount=0, ap_cost=10):
        if self.action_points >= ap_cost:
            self.action_points -= ap_cost
            amount = amount or self.combat_stats.max_hp
            self.combat_stats.get_healed(amount)
            self.game_state.add_message(f"{self.monster_type} got healed for {amount}", WHITE)


    def on_death(self):
        dead = Remains(self.x, self.y, SPRITES[f"DEAD_{self.monster_type.upper()}"], name=f"Dead {self.monster_type}",
                       description=f"The remains of a {self.monster_type} {self.name}",game_state=self.game_state)
        print('created', type(dead))
        self.game_state.current_map.add_entity(dead, self.x // DISPLAY_TILE_SIZE, self.y // DISPLAY_TILE_SIZE)
        self.update_quest_progress()
        self.game_state.add_message(f"{self.monster_type} dies", WHITE)

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
        if len(self.interaction_history) > 10:
            self.interaction_history.pop(0)

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
        return "none"

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
            if self.monster_type == 'green_troll':
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
                 dmg=MONSTER_BASE_DAMAGE *1.5, armor=MONSTER_BASE_ARMOR*1.5, hp=MONSTER_BASE_HP*1.5,
                 face_path=SPRITES["GREEN_TROLL_FACE"]):
        super().__init__(x, y, game_state=game_state, name=name, monster_type=monster_type, sprite_path=sprite_path,
                         voice=voice, can_talk=can_talk, description=description, ap=ap, money=money,
                         dmg=dmg, armor=armor, hp=hp, face_path=face_path)
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
                 dmg=MONSTER_BASE_DAMAGE *0.8, armor=MONSTER_BASE_ARMOR*0.8, hp=MONSTER_BASE_HP*0.8,
                 face_path=SPRITES["DRYAD_FACE"]):
        super().__init__(x, y, game_state=game_state, name=name, monster_type=monster_type, sprite_path=sprite_path,
                         voice=voice, can_talk=can_talk, description=description, ap=ap, money=money,
                         dmg=dmg, armor=armor, hp=hp, face_path=face_path)

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
                self.is_hostile = False
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
        """Decide what action the monster should take based on its personality and situation"""
        if not self.transformed:
            if distance == 1 and random.random() < self.aggression:
                return "attack"
            else:
                self.combat_stats.get_healed()
            return 'none'
        return super().decide_monster_action(distance)
