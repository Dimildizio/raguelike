import pygame as pg
import time
from constants import FPS, RED


class FloatingText:
    def __init__(self, text, x, y, color=RED, duration=3.0, rise_speed=40):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.start_time = time.time()
        self.duration = duration
        self.rise_speed = rise_speed
        self.font = pg.font.Font(None, 30)
        self.alpha = 255


class FloatingTextManager:
    def __init__(self):
        self.floating_texts = []

    def add_text(self, text, x, y, color=RED, duration=3.0, rise_speed=40):
        """Add a new floating text at the specified position"""
        self.floating_texts.append(FloatingText(text, x, y, color, duration, rise_speed))

    def update(self):
        """Update all floating texts"""
        current_time = time.time()
        # Update in reverse to safely remove items
        for i in range(len(self.floating_texts) - 1, -1, -1):
            text = self.floating_texts[i]
            elapsed = current_time - text.start_time

            if elapsed >= text.duration:
                self.floating_texts.pop(i)
            else:
                # Move text upward
                text.y -= text.rise_speed * (1 / FPS)  # Assuming 60 FPS
                # Fade out
                text.alpha = int(255 * (1 - (elapsed / text.duration)))

    def draw(self, screen, camera_x=0, camera_y=0):
        """Draw all floating texts"""
        for text in self.floating_texts:
            text_surface = text.font.render(text.text, True, text.color)
            # Create a surface with alpha channel
            alpha_surface = pg.Surface(text_surface.get_rect().size, pg.SRCALPHA)
            # Blit with alpha
            alpha_surface.fill((255, 255, 255, text.alpha))
            text_surface.blit(alpha_surface, (0, 0), special_flags=pg.BLEND_RGBA_MULT)

            screen.blit(text_surface, (
                text.x - camera_x - text_surface.get_width() // 2,
                text.y - camera_y - text_surface.get_height() // 2
            ))