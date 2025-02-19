import json
import os
from datetime import datetime
from entities.character import Character
from entities.npc import NPC
from entities.entity import House, Tree, Entity
from entities.monster import Monster, KoboldTeacher, Dryad, GreenTroll, WillowWhisper, HellBard
from constants import *


class SaveSystem:
    SAVE_DIR = "data/saves"
    ENTITY_KEYS = {cls.__name__: cls for cls in [Entity, Character, NPC, House, Tree, Monster, KoboldTeacher, Dryad,
                                                 GreenTroll, WillowWhisper, HellBard,]}


    @staticmethod
    def save_game(game_state, slot=None):
        if slot is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"save_{timestamp}.json"
        else:
            filename = f"save_slot_{slot}.json"
        filepath = os.path.join(SaveSystem.SAVE_DIR, filename)

        save_data = game_state.save_game_state()

        with open(filepath, 'w') as f:
            json.dump(save_data, f, indent=2)


    @classmethod
    def load_game(cls, game_state):
        save_files = os.listdir(cls.SAVE_DIR)
        if save_files:
            filename = max([os.path.join(cls.SAVE_DIR, f) for f in save_files], key=os.path.getmtime)
            if not os.path.exists(filename):
                return False
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)

                game_state.load_game_state(data)

            except ValueError as e:
                print(f"Error loading save file {filename}: {e}")
                return False