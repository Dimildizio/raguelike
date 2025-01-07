import pygame
import random
from utils.sprite_loader import SpriteLoader
from constants import *

import pygame
import random
from utils.sprite_loader import SpriteLoader
from constants import *

import pygame
from utils.sprite_loader import SpriteLoader
from constants import *

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
        # Unpack the tuple returned by load_sprite
        self.surface, self.pil_sprite = self.sprite_loader.load_sprite(sprite_path)
        self.rotation = random.choice([0, 90, 180, 270])
        self.entity = None

    def draw(self, screen, offset_x=0, offset_y=0):
        if self.pil_sprite:
            # Use PIL-based rotation
            rotated_surface = self.sprite_loader.rotate_sprite(self.pil_sprite, self.rotation)
            if rotated_surface:
                screen.blit(rotated_surface, (self.x + offset_x, self.y + offset_y))
        else:
            # Fallback to regular surface if PIL sprite isn't available
            screen.blit(self.surface, (self.x + offset_x, self.y + offset_y))