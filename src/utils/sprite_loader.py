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


import pygame
from PIL import Image
import numpy as np
import io


class SpriteLoader:
    def __init__(self, original_size=512, tile_size=256, display_scale=32):
        self.original_size = original_size
        self.tile_size = tile_size
        self.display_scale = display_scale
        self.sprite_cache = {}
        self.rotation_cache = {}

    def load_sprite(self, path):
        if path in self.sprite_cache:
            return self.sprite_cache[path]

        try:
            # Load with Pillow
            pil_image = Image.open(path).convert('RGBA')

            # Resize if needed
            if pil_image.size != (self.original_size, self.original_size):
                pil_image = pil_image.resize((self.original_size, self.original_size), Image.Resampling.LANCZOS)

            # Preprocess to tile size
            pil_image = pil_image.resize((self.tile_size, self.tile_size), Image.Resampling.LANCZOS)

            # Scale down to display size
            pil_image = pil_image.resize((self.display_scale, self.display_scale), Image.Resampling.LANCZOS)

            # Convert PIL to pygame surface
            str_data = pil_image.tobytes()
            surface = pygame.image.fromstring(str_data, pil_image.size, 'RGBA')

            # Cache the processed sprite
            self.sprite_cache[path] = (surface, pil_image)
            return surface, pil_image

        except Exception as e:
            print(f"Error loading sprite {path}: {e}")
            # Create a default colored square as fallback
            surface = pygame.Surface((self.display_scale, self.display_scale))
            surface.fill((255, 0, 255))  # Magenta for missing textures
            return surface, None

    def rotate_sprite(self, pil_image, angle):
        """Rotate a PIL image and return a pygame surface"""
        if pil_image is None:
            return None

        # Cache key for this rotation
        cache_key = (id(pil_image), angle)
        if cache_key in self.rotation_cache:
            return self.rotation_cache[cache_key]

        # Rotate with PIL (expand=True to prevent cropping)
        rotated_pil = pil_image.rotate(angle, Image.Resampling.BICUBIC, expand=False)

        # Convert to pygame surface
        str_data = rotated_pil.tobytes()
        surface = pygame.image.fromstring(str_data, rotated_pil.size, 'RGBA')

        # Cache the rotated surface
        self.rotation_cache[cache_key] = surface

        return surface