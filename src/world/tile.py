import pygame
import random
from utils.sprite_loader import SpriteLoader
from constants import *

class Tile:
    def __init__(self, x, y, sprite_path):
        self.x = x
        self.y = y
        self.sprite_loader = SpriteLoader(
            ORIGINAL_SPRITE_SIZE,
            PREPROCESSED_TILE_SIZE,
            DISPLAY_TILE_SIZE
        )
        self.sprite = self.sprite_loader.load_sprite(sprite_path)
        self.rotation = random.choice([0, 90, 180, 270])
        self.entity = None  # Stores what's on this tile
        
    def draw(self, screen, offset_x=0, offset_y=0):
        rotated_sprite = pygame.transform.rotate(self.sprite, self.rotation)
        screen.blit(rotated_sprite, (self.x + offset_x, self.y + offset_y))