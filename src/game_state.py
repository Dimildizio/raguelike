from enum import Enum
from world.worldmap import WorldMap
from entities.character import Character
from systems.combat import CombatSystem
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



    def start_new_game(self):
        self.player = None
        self.current_map = None

        # Create player
        self.player = Character(0, 0, SPRITES["PLAYER"])

        # Create monsters
        monsters = [
            Monster(0, 0, SPRITES["MONSTER"]) for _ in range(NUM_MONSTERS)
        ]

        # Create NPCs
        npcs = [
            NPC(0, 0, SPRITES["NPC"]) for _ in range(NUM_NPCS)
        ]

        # Create and setup map
        self.current_map = WorldMap(MAP_WIDTH, MAP_HEIGHT)
        self.current_map.generate_map()
        # Place all entities
        self.current_map.place_entities(self.player, monsters, npcs)
        self.change_state(GameState.MAIN_MENU)


    def change_state(self, new_state):
        self.current_state = new_state
    
    def enter_combat(self, enemies):
        self.combat_system = CombatSystem()
        self.combat_system.start_combat(self.player, enemies)
        self.change_state(GameState.COMBAT)
