import random
from utils.sprite_loader import SpriteLoader
from constants import *


class Tile:
    def __init__(self, x, y, sprite_path, passable=True, rotate=True):
        self.x = x
        self.y = y
        self.sprite_loader = SpriteLoader(
            ORIGINAL_SPRITE_SIZE,
            PREPROCESSED_TILE_SIZE,
            DISPLAY_TILE_SIZE
        )
        self.sprite_path = sprite_path
        # Unpack the tuple returned by load_sprite
        self.surface, self.pil_sprite = self.sprite_loader.load_sprite(sprite_path)
        self.rotation = random.choice([0, 90, 180, 270]) if rotate else 0
        self.entities = []
        self.ground_items = []
        self.passable = passable

    def draw(self, screen, offset_x=0, offset_y=0):
        if self.pil_sprite:
            # Use PIL-based rotation
            rotated_surface = self.sprite_loader.rotate_sprite(self.pil_sprite, self.rotation)
            if rotated_surface:
                screen.blit(rotated_surface, (self.x + offset_x, self.y + offset_y))
        else:
            # Fallback to regular surface if PIL sprite isn't available
            screen.blit(self.surface, (self.x + offset_x, self.y + offset_y))
        for item in self.ground_items:
            item.draw(screen, offset_x, offset_y)

    def add_item(self, item):
        print('Added item at: (x,y)', self.x, self.y)
        self.ground_items.append(item)

    def remove_item(self, item):
        if item in self.ground_items:
            self.ground_items.remove(item)

    def add_entity(self, entity):
        """Add an entity to this tile"""
        if entity not in self.entities:
            self.entities.append(entity)

    def remove_entity(self, entity):
        """Remove an entity from this tile"""
        if entity in self.entities:
            self.entities.remove(entity)

    def get_blocking_entity(self):
        """Return the first non-passable entity on this tile, or None if tile is passable"""
        for entity in self.entities:
            if not entity.is_passable:
                return entity
        return None