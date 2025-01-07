import pygame
from .tile import Tile
import random
from constants import *
from entities.character import Character
from entities.monster import Monster
from entities.npc import NPC
from constants import SPRITES
from utils.sprite_loader import SpriteLoader


class WorldMap:
    def __init__(self, state_manager, width=MAP_WIDTH, height=MAP_HEIGHT):
        self.state_manager = state_manager
        self.width = width
        self.height = height
        self.tile_size = DISPLAY_TILE_SIZE
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
    
    def draw(self, screen, camera_x=0, camera_y=0):
        # Draw all tiles
        for row in self.tiles:
            for tile in row:
                tile.draw(screen, -camera_x, -camera_y)
        
        # Draw all entities
        for entity in self.entities:
            entity.draw(screen, -camera_x, -camera_y)

    def add_entity(self, entity, tile_x, tile_y):
        # Convert tile coordinates to pixel coordinates
        entity.x = tile_x * self.tile_size
        entity.y = tile_y * self.tile_size
        self.entities.append(entity)
        
        # Update tile's entity reference
        self.tiles[tile_y][tile_x].entity = entity
    
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
        # Check if movement is valid
        if not (0 <= new_tile_x < self.width and 0 <= new_tile_y < self.height):
            return False
            
        # Get entity at destination tile
        destination_entity = self.tiles[new_tile_y][new_tile_x].entity
        
        # Check if destination has an entity
        if destination_entity is not None:
            # If player moves into monster, trigger combat
            if isinstance(entity, Character) and isinstance(destination_entity, Monster):
                self.state_manager.enter_combat([destination_entity])
            return False
            
        # Clear old tile's entity reference
        old_tile_x = entity.x // self.tile_size
        old_tile_y = entity.y // self.tile_size
        self.tiles[old_tile_y][old_tile_x].entity = None
        
        # Update entity position
        entity.x = new_tile_x * self.tile_size
        entity.y = new_tile_y * self.tile_size
        
        # Update new tile's entity reference
        self.tiles[new_tile_y][new_tile_x].entity = entity
        return True
        
    def draw(self, screen, camera_x=0, camera_y=0):
        # Calculate visible area
        visible_start_x = camera_x // self.tile_size
        visible_start_y = camera_y // self.tile_size
        visible_end_x = visible_start_x + (WINDOW_WIDTH // self.tile_size) + 2
        visible_end_y = visible_start_y + (WINDOW_HEIGHT // self.tile_size) + 2
        
        # Clamp to map bounds
        visible_start_x = max(0, visible_start_x)
        visible_start_y = max(0, visible_start_y)
        visible_end_x = min(self.width, visible_end_x)
        visible_end_y = min(self.height, visible_end_y)
        
        # Draw only visible tiles
        for y in range(visible_start_y, visible_end_y):
            for x in range(visible_start_x, visible_end_x):
                self.tiles[y][x].draw(screen, -camera_x, -camera_y)
        
        # Draw visible entities
        for entity in self.entities:
            # Check if entity is in visible area
            entity_tile_x = entity.x // self.tile_size
            entity_tile_y = entity.y // self.tile_size
            if (visible_start_x <= entity_tile_x <= visible_end_x and
                visible_start_y <= entity_tile_y <= visible_end_y):
                entity.draw(screen, -camera_x, -camera_y)

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
        # Ensure coordinates are within bounds
        if not (0 <= tile_x < self.width and 0 <= tile_y < self.height):
            print(f"Warning: Attempted to place entity outside map bounds ({tile_x}, {tile_y})")
            tile_x = min(max(0, tile_x), self.width - 1)
            tile_y = min(max(0, tile_y), self.height - 1)
        
        # Convert tile coordinates to pixel coordinates
        entity.x = tile_x * self.tile_size
        entity.y = tile_y * self.tile_size
        self.entities.append(entity)
        
        # Update tile's entity reference
        self.tiles[tile_y][tile_x].entity = entity