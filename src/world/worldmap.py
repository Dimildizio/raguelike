import pygame
from .tile import Tile
import random
from constants import *
from entities.character import Character
from entities.monster import Monster
from entities.npc import NPC
from constants import SPRITES
from utils.sprite_loader import SpriteLoader
from systems.combat_animation import CombatAnimation


class WorldMap:
    def __init__(self, state_manager, width=MAP_WIDTH, height=MAP_HEIGHT):
        self.state_manager = state_manager
        self.width = width
        self.height = height
        self.tile_size = DISPLAY_TILE_SIZE
        self.combat_animation = CombatAnimation()

        self.sprite_loader = SpriteLoader(
            ORIGINAL_SPRITE_SIZE,
            PREPROCESSED_TILE_SIZE,
            DISPLAY_TILE_SIZE
        )
        
        # Initialize empty tiles list
        self.tiles = [[None for _ in range(width)] for _ in range(height)]
        self.entities = []
        
        # Generate the map
        self.generate_map()
    
    def generate_map(self):
        # Create a grid of tiles
        for y in range(self.height):
            for x in range(self.width):
                # Calculate pixel positions
                pixel_x = x * self.tile_size
                pixel_y = y * self.tile_size
                
                # Create tile with preprocessed sprite
                self.tiles[y][x] = Tile(pixel_x, pixel_y, SPRITES["FLOOR"])

    def generate(self):
        """Generate a simple room-based map"""
        # Fill map with walls initially
        for y in range(self.height):
            for x in range(self.width):
                self.tiles[y][x].type = TILE_WALL

        # Create a main room in the center
        room_width = self.width // 2
        room_height = self.height // 2
        start_x = (self.width - room_width) // 2
        start_y = (self.height - room_height) // 2

        # Fill room with floor tiles
        for y in range(start_y, start_y + room_height):
            for x in range(start_x, start_x + room_width):
                self.tiles[y][x].type = TILE_FLOOR

        print(f"Generated map with dimensions {self.width}x{self.height}")
        print(f"Created room at {start_x},{start_y} with size {room_width}x{room_height}")

    def update(self):
        self.entities = [entity for entity in self.entities if entity.is_alive]
        for entity in self.entities:
            entity.update()

        if hasattr(self, 'combat_animation'):
            self.combat_animation.update()

    def draw(self, screen, camera_x=0, camera_y=0):
        # Draw tiles
        for y in range(self.height):
            for x in range(self.width):
                self.tiles[y][x].draw(screen, -camera_x, -camera_y)

        # Draw entities with potential shake offset
        for entity in self.entities:
            draw_x = entity.x
            draw_y = entity.y

            # Apply shake offset if this is the target entity
            if (hasattr(self, 'combat_animation') and
                    self.combat_animation.is_playing and
                    entity == self.combat_animation.target):
                draw_x += self.combat_animation.shake_offset[0]
                draw_y += self.combat_animation.shake_offset[1]

            # Draw the entity at the calculated position
            entity.draw(screen, -camera_x + (draw_x - entity.x), -camera_y + (draw_y - entity.y))

        # Draw combat animation effects
        if hasattr(self, 'combat_animation'):
            self.combat_animation.draw(screen, camera_x, camera_y)

    
    def remove_entity(self, entity):
        if entity in self.entities:
            # Find and clear tile's entity reference
            tile_x = entity.x // self.tile_size
            tile_y = entity.y // self.tile_size
            self.tiles[tile_y][tile_x].entity = None
            self.entities.remove(entity)
    
    def get_tile_at(self, tile_x, tile_y):
        if 0 <= tile_x < self.width and 0 <= tile_y < self.height:
            return self.tiles[tile_y][tile_x]
        return None

    def move_entity(self, entity, new_tile_x, new_tile_y):
        new_tile_x = int(new_tile_x)
        new_tile_y = int(new_tile_y)
        if hasattr(self, 'combat_animation') and self.combat_animation.is_playing:
            return False  # Don't allow movement/attack during animation

        # Check if movement is valid
        if not (0 <= new_tile_x < self.width and 0 <= new_tile_y < self.height):
            return False

        # Get entity at destination tile
        destination_tile = self.tiles[new_tile_y][new_tile_x]
        destination_entity = destination_tile.entity

        # Debug prints
        if destination_entity:
            print(f"Found entity at destination: {type(destination_entity)}")
            print(f"Entity HP: {destination_entity.combat_stats.current_hp}")
            print(f"Is alive: {destination_entity.is_alive}")

        # Check if destination has a living entity
        if destination_entity is not None:
            if not destination_entity.is_alive:
                print(f"Removing dead entity from tile {new_tile_x}, {new_tile_y}")
                # Remove dead entity and allow movement to its tile
                destination_tile.entity = None
                if destination_entity in self.entities:
                    self.entities.remove(destination_entity)
                return self.move_entity(entity, new_tile_x, new_tile_y)  # Retry move after removing

            elif isinstance(entity, Character) and isinstance(destination_entity, Monster):
                print(f"Combat initiated")
                # Player attacks monster
                damage = destination_entity.combat_stats.take_damage(entity.combat_stats.damage)
                print(f"Damage dealt: {damage}")
                print(f"Monster HP after damage: {destination_entity.combat_stats.current_hp}")
                print(f"Monster alive after damage: {destination_entity.is_alive}")

                # Start combat animation
                if hasattr(self, 'combat_animation'):
                    self.combat_animation.start_attack(entity, destination_entity)

                # If monster died from this attack, remove it
                if not destination_entity.is_alive:
                    print(f"Monster died, removing from game")
                    destination_tile.entity = None
                    if destination_entity in self.entities:
                        self.entities.remove(destination_entity)
                return True

            return False  # Can't move into occupied tile

        # Move to empty tile
        old_tile_x = entity.x // self.tile_size
        old_tile_y = entity.y // self.tile_size

        # Update tiles
        self.tiles[old_tile_y][old_tile_x].entity = None
        destination_tile.entity = entity

        # Update entity position
        entity.x = new_tile_x * self.tile_size
        entity.y = new_tile_y * self.tile_size

        return True

    def get_random_empty_position(self):
        """Find a random empty tile position"""
        while True:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            
            # Check if tile exists and is empty
            if (0 <= y < len(self.tiles) and 
                0 <= x < len(self.tiles[y]) and 
                self.tiles[y][x] is not None and 
                self.tiles[y][x].entity is None):
                return (x, y)

    def add_entity(self, entity, tile_x, tile_y):
        # Check if position is within bounds and tile is empty
        if (0 <= tile_x < self.width and
                0 <= tile_y < self.height and
                self.tiles[tile_y][tile_x].entity is None):
            # Place entity
            self.tiles[tile_y][tile_x].entity = entity
            entity.x = tile_x * self.tile_size
            entity.y = tile_y * self.tile_size
            self.entities.append(entity)
            return True
        return False

    def place_entities(self, player, monsters, npcs):
        # Place all entities (including player) at random empty tiles
        all_entities = [player] + monsters + npcs

        for entity in all_entities:
            placed = False
            while not placed:
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)
                placed = self.add_entity(entity, x, y)