from enum import Enum
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

    def start_new_game(self):
        self.player = None
        self.current_map = None

        # Create player
        self.player = Character(0, 0, "PLAYER", game_state=self)

        # Create monsters
        monsters = [
            Monster(0, 0, "MONSTER", name=f'Monster_{n}', game_state=self) for n in range(NUM_MONSTERS)
        ]

        # Create NPCs
        npc_imgs = [{'name': 'Villager Amelia', 'sprite': 'NPC_1', 'face': 'NPC_FACE_1'},
                    {'name': 'Merchant Tom', 'sprite': 'NPC_2', 'face': 'NPC_FACE_2'},
                    {'name': 'Elara the Elara', 'sprite': 'NPC_3', 'face': 'NPC_FACE_3'},]
        moods = ['playful', 'happy', 'silly', 'friendly', 'neutral', 'greedy', 'vicious', 'unfriendly']
        npcs = [
            NPC(0, 0, npc_imgs[n]['sprite'], face_path=npc_imgs[n]['face'], name=npc_imgs[n]['name'],
                mood=random.choice(moods), game_state=self) for n in range(NUM_NPCS)]

        # Create and setup map
        self.current_map = WorldMap(self, MAP_WIDTH, MAP_HEIGHT)
        self.current_map.generate_map()
        # Place all entities
        self.current_map.place_entities(self.player, monsters, npcs)
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
            rewards = self.quest_manager.check_quest_completion(quest_id, self.player)
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
        if monster.monster_type == "goblin":
            self.update_quest_progress("kill_goblins")
        elif monster.monster_type == "wolf":
            self.update_quest_progress("kill_wolf")
            # Add wolf pelt to player inventory
            self.player.inventory.append("wolf_pelt")