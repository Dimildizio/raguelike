from enum import Enum
from world.create_map import MapCreator
from world.worldmap import WorldMap
from entities.character import Character
from systems.quest import QuestManager
from entities.monster import Monster
from entities.entity import Tree, House
from entities.npc import NPC
from constants import *
import random


class GameStateManager:
    def __init__(self, sound_manager):
        self.current_state = GameState.MAIN_MENU
        self.sound_manager = sound_manager
        self.selected_menu_item = 0  # Track which menu item is selected
        self.current_map = WorldMap(self)
        self.player = None  # Don't create player until game starts
        self.combat_system = None
        self.current_npc = None
        self.quest_manager = QuestManager()

    def start_new_game1(self):
        self.player = None
        self.current_map = None

        # Create player
        self.player = Character(0, 0, "PLAYER", game_state=self)

        # Create monsters
        monsters = [
            Monster(0, 0, "MONSTER", name=f'Monster_{n}', game_state=self) for n in range(NUM_MONSTERS)
        ]

        # Create NPCs
        npc_imgs = [{'name': 'Villager Amelia', 'sprite': 'NPC_1', 'face': 'NPC_FACE_1', 'description': 'young girl'},
                    {'name': 'Merchant Tom', 'sprite': 'NPC_2', 'face': 'NPC_FACE_2', 'description': 'old tired merchant'},
                    {'name': 'Elara the Elara', 'sprite': 'NPC_3', 'face': 'NPC_FACE_3', 'description': 'middle aged half ork woman'},]
        npcs = [
            NPC(0, 0, npc_imgs[n]['sprite'], face_path=npc_imgs[n]['face'], name=npc_imgs[n]['name'],
                mood=random.choice(NPC_MOOD), game_state=self, description=npc_imgs[n]['description'],
                ) for n in range(NUM_NPCS)]

        # Create and setup map
        self.current_map = WorldMap(self, MAP_WIDTH, MAP_HEIGHT)
        self.current_map.generate_map()
        # Place all entities
        self.current_map.place_entities(self.player, monsters, npcs)
        self.change_state(GameState.MAIN_MENU)

    def start_new_game(self):
        self.player = None
        self.current_map = None

        # Create player
        self.player = Character(0, 0, "PLAYER", game_state=self)

        # Create monsters
        monsters = [
            Monster(0, 0, "MONSTER", name=f'Monster_{n}', game_state=self) for n in range(NUM_MONSTERS)
        ]

        # Create NPCs with specific attributes
        npc_data = [
            {
                'name': 'Villager Amelia',
                'sprite': 'NPC_1',
                'face': 'NPC_FACE_1',
                'description': 'young girl',
                'position': None  # Will be set by MapCreator
            },
            {
                'name': 'Merchant Tom',
                'sprite': 'NPC_2',
                'face': 'NPC_FACE_2',
                'description': 'old tired merchant',
                'position': None
            }
        ]
        moods = ['playful', 'happy', 'silly', 'friendly', 'neutral', 'greedy', 'vicious', 'unfriendly']
        npcs = [
            NPC(0, 0, npc['sprite'], face_path=npc['face'], name=npc['name'],
                mood=random.choice(moods), game_state=self, description=npc['description']
                ) for npc in npc_data
        ]

        # Create and setup map with MapCreator
        self.current_map = WorldMap(self, MAP_WIDTH, MAP_HEIGHT)
        map_creator = MapCreator(self.current_map.sprite_loader)
        tiles, house_pos, npc_positions, tree_positions = map_creator.create_map()
        self.current_map.tiles = tiles

        # Place house at random valid position from MapCreator
        for (h_x, h_y) in house_pos:
            self.current_map.add_entity(House(h_x, h_y), h_x, h_y)
        # Place NPCs at their designated positions from MapCreator
        for npc, position in zip(npcs, npc_positions):
            x, y = position
            print('npc_start', npc.name, 'x', x, 'y', y)
            self.current_map.add_entity(npc, x, y)
        for x, y in tree_positions:
            tree = Tree(x, y, random.choice([SPRITES["TREE_1"], SPRITES["TREE_2"], SPRITES["TREE_3"]]))
            self.current_map.add_entity(tree, x, y)

        # Place player and monsters in random valid positions
        valid_positions = self.current_map.get_valid_positions(len(monsters) + 1)

        # Place player
        player_pos = valid_positions.pop()
        print('npc', self.player, 'x', player_pos[0], 'y', player_pos[1])
        self.current_map.add_entity(self.player, player_pos[0], player_pos[1])

        # Place monsters
        for monster in monsters:
            if valid_positions:
                pos = valid_positions.pop()
                print('monster', monster, 'x', pos[0], 'y', [pos[1]])
                self.current_map.add_entity(monster, pos[0], pos[1])

        self.change_state(GameState.MAIN_MENU)

    def change_state(self, new_state):
        self.current_state = new_state

    def accept_quest(self, quest_id: str) -> bool:
        """Handle quest acceptance through the game state"""
        if self.player and self.quest_manager.start_quest(quest_id):
            return self.player.accept_quest(quest_id)
        return False

    def complete_quest(self, quest_id: str):
        """Handle quest completion through the game state"""
        if self.player:
            rewards = self.quest_manager.check_quest_completion(quest_id, self.player, self.current_npc)
            if rewards:
                self.player.complete_quest(quest_id)
                return rewards
        return None

    def get_active_quests(self):
        """Get list of active quests for dialogue context"""
        if not self.player:
            return []
        return [self.quest_manager.quests[qid].to_dict()
                for qid in self.player.active_quests
                if qid in self.quest_manager.quests]

    def get_available_quests(self, npc_id: str):
        """Get available quests for specific NPC that player hasn't accepted/completed"""
        if not self.player:
            return []
        return [quest for quest in self.quest_manager.get_available_quests(npc_id)
                if quest.quest_id not in self.player.active_quests
                and quest.quest_id not in self.player.completed_quests]

    def update_quest_progress(self, condition_type: str, value: int = 1):
        """Update progress for all active quests"""
        if self.player:
            self.quest_manager.update_quest_progress(condition_type, value)

    def on_monster_death(self, monster):
        """Handle monster death and quest updates"""
        if not self.player:
            return
        # Update quest progress based on monster type
        print(f"{monster.monster_type} dies")
        self.update_quest_progress(f"kill_{monster.monster_type}s")
        if monster.monster_type == "wolf":
            self.player.inventory.append("wolf_pelt")

    def pass_night(self, fee=0):
        """Handle night passing effects"""
        # Check if player can afford lodging

        if not self.player or not self.player.spend_gold(fee):
            print('not enough money')
            return False
        print('night has passed')
        # Heal all entities with combat stats
        self.player.heal_self()
        self.player.action_points = self.player.max_action_points

        # Heal NPCs and change their moods
        for entity in self.current_map.get_all_entities():
            if hasattr(entity, 'combat_stats'):
                if isinstance(entity, NPC):
                    entity.mood = random.choice(NPC_MOOD)
                    entity.heal_self()
                elif isinstance(entity, Monster):
                    entity.heal_self()

        # Get player position
        player_x = self.player.x // DISPLAY_TILE_SIZE
        player_y = self.player.y // DISPLAY_TILE_SIZE

        # Get valid positions for monsters (5+ tiles away from player)
        valid_positions = []
        for y in range(self.current_map.height):
            for x in range(self.current_map.width):
                dist_to_player = abs(x - player_x) + abs(y - player_y)

                if (dist_to_player >= SPAWN_DISTANCE and self.current_map.tiles[y][x].passable and
                        not self.current_map.tiles[y][x].entities):
                    valid_positions.append((x, y))
        if not valid_positions:
            return True
        for entity in self.current_map.get_all_entities():
            if isinstance(entity, Monster):
                if valid_positions:
                    new_pos = random.choice(valid_positions)
                    valid_positions.remove(new_pos)
                    self.current_map.move_entity_to(entity, new_pos[0], new_pos[1])

        # Spawn new goblin if positions available
        if valid_positions:
            spawn_pos = random.choice(valid_positions)
            new_goblin = Monster(x=spawn_pos[0] * DISPLAY_TILE_SIZE, y=spawn_pos[1] * DISPLAY_TILE_SIZE,
                sprite_path="MONSTER", name='Unknown Goblin', monster_type='goblin', game_state=self)
            self.current_map.add_entity(new_goblin, spawn_pos[0], spawn_pos[1])
        return True