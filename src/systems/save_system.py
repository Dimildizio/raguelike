import json
import os
from typing import Dict, Any
import pygame
from datetime import datetime
from entities.character import Character
from entities.npc import NPC
from entities.entity import House, Tree, Entity
from entities.monster import Monster, KoboldTeacher, Dryad, GreenTroll, WillowWhisper, HellBard

class SaveSystem:
    SAVE_DIR = "data/saves"
    ENTITY_KEYS = {cls.__name__: cls for cls in [Entity, Character, NPC, House, Tree, Monster, KoboldTeacher, Dryad,
                                                 GreenTroll, WillowWhisper, HellBard,]}

    @staticmethod
    def save_game(game_state, slot=None):
        """Save game to specific slot or create new save"""
        SaveSystem.ensure_save_directory()

        if slot is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"save_{timestamp}.json"
        else:
            filename = f"save_slot_{slot}.json"

        filepath = os.path.join(SaveSystem.SAVE_DIR, filename)

        # Create save data dictionary with only serializable data
        save_data = {
            "save_date": datetime.now().isoformat(),
            "current_day": game_state.current_day,
            "stats": game_state.stats,

            # Save player data
            "player": SaveSystem.serialize_entity(game_state.player) if game_state.player else None,

            # Save entities
            "entities": [
                SaveSystem.serialize_entity(entity)
                for entity in game_state.current_map.entities
                if entity != game_state.player  # Don't save player twice
            ],

            # Save map data
            "map": {
                "width": game_state.current_map.width,
                "height": game_state.current_map.height,
                "tiles": [
                    [
                        {
                            "sprite_path": tile.sprite_path,
                            "passable": tile.passable,
                            "x": tile.x,
                            "y": tile.y
                        } for tile in row
                    ] for row in game_state.current_map.tiles
                ]
            },

            # Save quest data
            "quests": game_state.quest_manager.save_quests(),

            # Save achievements
            "achievements": {
                id: {
                    "name": ach["name"],
                    "description": ach["description"],
                    "completed": ach["completed"]
                }
                for id, ach in game_state.achievement_manager.achievements.items()
            }
        }

        try:
            with open(filepath, 'w') as f:
                json.dump(save_data, f, indent=2)
            return filename
        except Exception as e:
            print(f"Error saving game: {e}")
            return None

    @staticmethod
    def ensure_save_directory():
        """Create saves directory if it doesn't exist"""
        if not os.path.exists(SaveSystem.SAVE_DIR):
            os.makedirs(SaveSystem.SAVE_DIR)

    @staticmethod
    def serialize_entity(entity) -> Dict[str, Any]:
        """Convert an entity instance to serializable dictionary using recursive serialization"""
        return SaveSystem.make_serializable(entity)

    @staticmethod
    def make_serializable(obj) -> Any:
        """Recursively convert an object and its attributes to a serializable format"""
        # Handle None
        if obj is None:
            return None

        # Handle basic types that are already serializable
        if isinstance(obj, (str, int, float, bool)):
            return obj

        # Handle lists
        if isinstance(obj, list):
            return [SaveSystem.make_serializable(item) for item in obj]

        # Handle dictionaries
        if isinstance(obj, dict):
            return {key: SaveSystem.make_serializable(value) for key, value in obj.items()}

        # Skip pygame objects, logging objects, and other problematic types
        if isinstance(obj, (pygame.Surface, pygame.sprite.Sprite, pygame.font.Font)) or \
                any(type_name in str(type(obj)) for type_name in ['logging', 'Logger', 'Manager']):
            return None

        # For all other objects, try to convert to dictionary
        try:
            # Get all attributes that don't start with underscore
            obj_dict = {
                key: value for key, value in vars(obj).items()
                if not key.startswith('_') and
                   not any(type_name in str(type(value)) for type_name in ['logging', 'Logger', 'Manager'])
            }

            # Add class type information
            serialized = {
                "__class__": obj.__class__.__name__,
                "__module__": obj.__class__.__module__,
                "attributes": {}
            }

            # Recursively serialize each attribute
            for key, value in obj_dict.items():
                try:
                    serialized["attributes"][key] = SaveSystem.make_serializable(value)
                except Exception:
                    continue

            return serialized

        except Exception:
            return None

    @staticmethod
    def deserialize_object(data: Dict) -> Any:
        """Recursively reconstruct an object from serialized data"""
        # Handle None
        if data is None:
            return None

        # Handle basic types
        if isinstance(data, (str, int, float, bool)):
            return data

        # Handle lists
        if isinstance(data, list):
            return [SaveSystem.deserialize_object(item) for item in data]

        # Handle dictionaries
        if isinstance(data, dict):
            # Check if this is a serialized class
            if "__class__" in data:
                try:
                    # Import the module and get the class
                    module_name = data["__module__"]
                    class_name = data["__class__"]

                    # Special handling for known types that need specific initialization
                    if class_name in ["Monster", "NPC", "Player"]:
                        # These will be handled separately by create_entity_from_data
                        return data

                    # For other classes, try to reconstruct them
                    module = __import__(module_name, fromlist=[class_name])
                    cls = getattr(module, class_name)

                    # Create instance and set attributes
                    instance = cls()
                    for key, value in data["attributes"].items():
                        setattr(instance, key, SaveSystem.deserialize_object(value))
                    return instance

                except Exception as e:
                    print(f"Warning: Failed to deserialize {data['__class__']}: {e}")
                    return None

            # Regular dictionary
            return {key: SaveSystem.deserialize_object(value) for key, value in data.items()}

        return data

    @staticmethod
    def load_game(game_state, filename="save.json"):
        """Load game state from file"""
        if not os.path.exists(filename):
            return False

        try:
            with open(filename, 'r') as f:
                data = json.load(f)

            # Create new game state
            game_state.start_new_game()

            # Load map
            map_data = data["map"]
            game_state.current_map.width = map_data["width"]
            game_state.current_map.height = map_data["height"]

            # Recreate tiles
            for y, row in enumerate(map_data["tiles"]):
                for x, tile_data in enumerate(row):
                    # Use vars() to set all attributes
                    for key, value in tile_data.items():
                        setattr(game_state.current_map.tiles[y][x], key, value)

            # Load player
            player_data = data["player"]
            # Set all serializable attributes
            for key, value in player_data.items():
                if key != "combat_stats" and not isinstance(value, (pygame.Surface, pygame.sprite.Sprite)):
                    setattr(game_state.player, key, value)

            # Set combat stats separately
            if "combat_stats" in player_data:
                for key, value in player_data["combat_stats"].items():
                    setattr(game_state.player.combat_stats, key, value)

            # Load entities
            game_state.current_map.entities = []
            for entity_data in data["entities"]:
                entity = SaveSystem.create_entity_from_data(entity_data, game_state)
                if entity:
                    game_state.current_map.add_entity(
                        entity,
                        entity_data["x"] // game_state.current_map.tile_size,
                        entity_data["y"] // game_state.current_map.tile_size
                    )

            # Load other game state attributes
            for key, value in data.items():
                if key not in ["player", "map", "entities"] and not isinstance(value,
                                                                               (pygame.Surface, pygame.sprite.Sprite)):
                    setattr(game_state, key, value)

            return True

        except Exception as e:
            print(f"Error loading save file: {e}")
            return False

    @staticmethod
    def create_entity_from_data(data: Dict, game_state) -> Any:
        """Create appropriate entity instance from saved data"""
        from entities.monster import Monster
        from entities.npc import NPC

        entity_type = data["type"]
        entity_class = {"Monster": Monster, "NPC": NPC}.get(entity_type)

        if not entity_class:
            return None

        # Create basic instance
        entity = entity_class(
            x=data["x"],
            y=data["y"],
            game_state=game_state
        )

        # Set all attributes from saved data
        for key, value in data.items():
            if key not in ["type", "x", "y", "combat_stats"] and not isinstance(value,
                                                                                (pygame.Surface, pygame.sprite.Sprite)):
                setattr(entity, key, value)

        # Set combat stats if present
        if "combat_stats" in data:
            for key, value in data["combat_stats"].items():
                setattr(entity.combat_stats, key, value)

        return entity


    @staticmethod
    def save_game(game_state, slot=None):
        if slot is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"save_{timestamp}.json"
        else:
            filename = f"save_slot_{slot}.json"
        filepath = os.path.join(SaveSystem.SAVE_DIR, filename)

        save_data = {
            "save_date": datetime.now().isoformat(),
            "current_day": game_state.current_day,
            "stats": game_state.stats,
            # Save entities
            "entities": [entity.save_entity() for entity in game_state.current_map.entities
                         ],}  # if entity != game_state.player  # Don't save player twice


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
                    for entity_data in data['entities']:
                        new_creature = cls.ENTITY_KEYS[entity_data['entity_class']]
                        entity = new_creature(entity_data['x'], entity_data['y'], sprite_path=entity_data['sprite_path'],
                                              game_state=game_state, loading=True)
                        entity.load_entity(entity_data)
                        if new_creature == Character:
                            t_size = game_state.current_map.tile_size
                            game_state.current_map.remove_entity(game_state.player)
                            game_state.current_map.add_entity(entity, entity.x // t_size, entity.y // t_size)
                            game_state.player = entity

            except ValueError as e:
                print(f"Error loading save file {filename}: {e}")
                return False