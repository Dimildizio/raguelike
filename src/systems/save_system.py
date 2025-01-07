import json
import os

class SaveSystem:
    @staticmethod
    def save_game(game_state, filename="save.json"):
        save_data = {
            "player": {
                "position": (game_state.player.x, game_state.player.y),
                "health": game_state.player.health,
               
            },
            "entities": [
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(save_data, f)
            
    @staticmethod
    def load_game(filename="save.json"):
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return None