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
        self.combat_system = CombatSystem()



    def start_new_game(self):
        self.player = None
        self.current_map = None

        # Create player
        self.player = Character(0, 0, "PLAYER")

        # Create monsters
        monsters = [
            Monster(0, 0, "MONSTER") for _ in range(NUM_MONSTERS)
        ]

        # Create NPCs
        npc_imgs = [{'name': 'Villager Amelia', 'sprite': 'NPC_1', 'face': 'NPC_FACE_1'},
                    {'name': 'Merchant Tom', 'sprite': 'NPC_2', 'face': 'NPC_FACE_2'},
                    {'name': 'Elara the Elara', 'sprite': 'NPC_3', 'face': 'NPC_FACE_3'},]
        moods = ['playful', 'happy', 'silly', 'friendly', 'neutral', 'greedy', 'vicious', 'unfriendly']
        npcs = [
            NPC(0, 0, npc_imgs[n]['sprite'], face_path=npc_imgs[n]['face'], name=npc_imgs[n]['name'],
                mood=random.choice(moods)) for n in range(NUM_NPCS)]

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
