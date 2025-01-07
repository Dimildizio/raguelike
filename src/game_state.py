from enum import Enum
from world.worldmap import WorldMap
from entities.character import Character
from systems.combat import CombatSystem
from entities.monster import Monster
from entities.npc import NPC
from constants import SPRITES
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

    def start_new_game(self):
        self.player = Character(0, 0, SPRITES["PLAYER"])
        
        # Get random empty positions for entities
        player_pos = self.current_map.get_random_empty_position()
        monster_pos = self.current_map.get_random_empty_position()
        npc_pos = self.current_map.get_random_empty_position()
        
        # Add entities at random positions
        self.current_map.add_entity(self.player, player_pos[0], player_pos[1])
        
        # Add test entities
        test_monster = Monster(0, 0, SPRITES["MONSTER"])
        self.current_map.add_entity(test_monster, monster_pos[0], monster_pos[1])
        
        test_npc = NPC(0, 0, SPRITES["NPC"], "Test NPC")
        test_npc.add_dialog("Hello, traveler!")
        self.current_map.add_entity(test_npc, npc_pos[0], npc_pos[1])
        
    def change_state(self, new_state):
        self.current_state = new_state
    
    def enter_combat(self, enemies):
        self.combat_system = CombatSystem()
        self.combat_system.start_combat(self.player, enemies)
        self.change_state(GameState.COMBAT)
