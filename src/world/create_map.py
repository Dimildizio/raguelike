from PIL import Image
import random
import pygame
from .tile import Tile
from constants import *
from entities.npc import NPC
from entities.monster import Monster


class MapCreator:
    def __init__(self, sprite_loader):
        self.sprite_loader = sprite_loader
        self.width = MAP_WIDTH
        self.height = MAP_HEIGHT
        self.tiles = [[None for _ in range(self.width)] for _ in range(self.height)]


    def create_base_terrain(self):
        """Create grass terrain with random rotation"""
        grass_sprites = [SPRITES["GRASS_0"], SPRITES["GRASS_2"]]

        for y in range(self.height):
            for x in range(self.width):
                # Calculate pixel positions
                pixel_x = x * DISPLAY_TILE_SIZE
                pixel_y = y * DISPLAY_TILE_SIZE

                # Select random grass sprite
                sprite_path = random.choice(grass_sprites)

                # Create tile with sprite path (rotation will be handled by Tile class)
                self.tiles[y][x] = Tile(pixel_x, pixel_y, sprite_path)


    def create_road(self):
            """Create road pattern"""
            # Vertical road (middle of map)
            road_x = self.width // 2
            for y in range(self.height):
                self.tiles[y][road_x] = Tile(road_x * DISPLAY_TILE_SIZE, y * DISPLAY_TILE_SIZE, SPRITES["FLOOR"])
                self.tiles[y][road_x + 1] = Tile((road_x + 1) * DISPLAY_TILE_SIZE, y * DISPLAY_TILE_SIZE,
                                                 SPRITES["FLOOR"])

            # Horizontal road
            road_y = self.height // 2
            for x in range(self.width):
                # Always place road tile, even at intersection
                self.tiles[road_y][x] = Tile(x * DISPLAY_TILE_SIZE, road_y * DISPLAY_TILE_SIZE, SPRITES["FLOOR"])

    def place_house(self):
        """Place 6x6 house using separate sprite pieces"""
        house_x = self.width // 2 + 3  # A bit to the right of road
        house_y = self.height // 2 - 2  # Aligned with road, moved up a bit

        # Map of positions to sprite pieces for 6x6 house
        positions = ['top', 'top2', 'mid', 'mid2', 'bot', 'bot2']
        house_pieces = []

        # Generate all combinations for 6x6 grid
        for row_idx, row in enumerate(positions):
            for col_idx, col in enumerate(positions):
                sprite_key = f"HOUSE_1_{row.upper()}_{col.upper()}"
                house_pieces.append([(col_idx, row_idx), SPRITES[sprite_key]])

        # Place each piece
        for (dx, dy), sprite_path in house_pieces:
            tile_x = house_x + dx
            tile_y = house_y + dy

            self.tiles[tile_y][tile_x] = Tile(
                tile_x * DISPLAY_TILE_SIZE,
                tile_y * DISPLAY_TILE_SIZE,
                sprite_path,
                passable=False,
                rotate=False  # Prevent rotation for house pieces
            )

    def get_npc_positions(self):
        """Get designated positions for NPCs"""
        positions = []

        # Position near house for Amelia
        positions.append((self.width // 2 + 2, self.height // 2 + 2))

        # Position for Merchant Tom
        positions.append((self.width // 2 + 3, self.height // 2 + 5))

        return positions

    def create_map(self):
        """Create complete map with all elements"""
        self.create_base_terrain()
        self.create_road()
        self.place_house()
        npc_positions = self.get_npc_positions()
        return self.tiles, npc_positions
