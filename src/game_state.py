from enum import Enum
from world.create_map import MapCreator
from world.worldmap import WorldMap
from entities.character import Character
from systems.quest import QuestManager
from entities.monster import Monster
from entities.npc import NPC
from constants import *
import random


class GameState(Enum):
    MAIN_MENU = 1
    PLAYING = 2
    COMBAT = 3
    DIALOG = 4
    INVENTORY = 5


class GameStateManager:
    def __init__(self):
        self.current_state = GameState.MAIN_MENU
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
        moods = ['playful', 'happy', 'silly', 'friendly', 'neutral', 'greedy', 'vicious', 'unfriendly']
        npcs = [
            NPC(0, 0, npc_imgs[n]['sprite'], face_path=npc_imgs[n]['face'], name=npc_imgs[n]['name'],
                mood=random.choice(moods), game_state=self, description=npc_imgs[n]['description'],
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
        tiles, npc_positions = map_creator.create_map()
        self.current_map.tiles = tiles

        # Place NPCs at their designated positions from MapCreator
        for npc, position in zip(npcs, npc_positions):
            x, y = position
            print('npc_start', npc.name, 'x', x, 'y', y)
            self.current_map.add_entity(npc, x, y)

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