import pygame
import os
import random

class SpriteLoader:
    def __init__(self, original_size=512, tile_size=256, display_scale=32):
        self.original_size = original_size  # Original sprite size (512x512)
        self.tile_size = tile_size         # Size to preprocess to (256x256)
        self.display_scale = display_scale  # Final display size (32x32)
        self.sprite_cache = {}             # Store processed sprites
        
    def load_sprite(self, path):
        if path in self.sprite_cache:
            return self.sprite_cache[path]
            
        # Load original sprite
        try:
            original = pygame.image.load(path)
            if original.get_size() != (self.original_size, self.original_size):
                original = pygame.transform.scale(original, (self.original_size, self.original_size))
            
            # Preprocess to tile size
            preprocessed = pygame.transform.scale(original, (self.tile_size, self.tile_size))
            
            # Scale down to display size
            display_sprite = pygame.transform.scale(preprocessed, (self.display_scale, self.display_scale))
            
            # Cache the processed sprite
            self.sprite_cache[path] = display_sprite
            return display_sprite
            
        except pygame.error as e:
            print(f"Error loading sprite {path}: {e}")
            # Create a default colored square as fallback
            surface = pygame.Surface((self.display_scale, self.display_scale))
            surface.fill((255, 0, 255))  # Magenta for missing textures
            return surface
    
    def create_tiled_surface(self, tile_sprite_path, width, height):
        # Create a surface for the entire map
        full_width = width * self.tile_size
        full_height = height * self.tile_size
        surface = pygame.Surface((full_width, full_height))
        
        # Load and preprocess the tile sprite once
        tile_sprite = pygame.image.load(tile_sprite_path)
        if tile_sprite.get_size() != (self.original_size, self.original_size):
            tile_sprite = pygame.transform.scale(tile_sprite, (self.original_size, self.original_size))
        preprocessed_tile = pygame.transform.scale(tile_sprite, (self.tile_size, self.tile_size))
        
        # Fill the surface with tiles
        for y in range(height):
            for x in range(width):
                # Random rotation for variety
                angle = random.choice([0, 90, 180, 270])
                rotated_tile = pygame.transform.rotate(preprocessed_tile, angle)
                surface.blit(rotated_tile, (x * self.tile_size, y * self.tile_size))
        
        # Scale the entire surface down to display size
        final_width = width * self.display_scale
        final_height = height * self.display_scale
        return pygame.transform.scale(surface, (final_width, final_height))