import pygame
from PIL import Image


class SpriteLoader:
    def __init__(self, original_size=512, tile_size=256, display_scale=32):
        self.original_size = original_size
        self.tile_size = tile_size
        self.display_scale = display_scale
        self.sprite_cache = {}
        self.rotation_cache = {}

    def load_sprite(self, path):
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

            return surface, pil_image

        except Exception as e:
            print(f"Error loading sprite {path}: {e}")
            # Create a default colored square as fallback
            surface = pygame.Surface((self.display_scale, self.display_scale))
            surface.fill((255, 0, 255))  # Magenta for missing textures
            return surface, None

    def rotate_sprite(self, pil_image, angle):
        """Rotate a PIL image and return a pygame surface without caching"""
        if pil_image is None:
            return None

        # Rotate with PIL (expand=True to prevent cropping)
        rotated_pil = pil_image.rotate(angle, Image.Resampling.BICUBIC, expand=False)

        # Convert to pygame surface
        str_data = rotated_pil.tobytes()
        surface = pygame.image.fromstring(str_data, rotated_pil.size, 'RGBA')

        return surface