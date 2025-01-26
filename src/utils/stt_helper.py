import requests
import time
import pygame as pg
from constants import *


class STTHandler:
    def __init__(self):
        self.api_url = "http://localhost:1921"
        self.is_recording = False
        self.start_time = 0
        self.duration = VOICE_DURATION  # seconds
        self.BAR_BACKGROUND = (128, 128, 128, 100)  # Light gray with transparency
        self.BAR_FILL = (160, 160, 160, 130)  # Slightly darker gray with transparency
        self.BAR_BORDER = (200, 200, 200, 150)  # Almost white with transparency
        self.TEXT_COLOR = (220, 220, 220)

    def start_recording(self):
            try:
                response = requests.post(f"{self.api_url}/start_recording")
                if response.status_code == 200:
                    self.is_recording = True
                    self.start_time = time.time()
                    return True
                return False
            except Exception as e:
                print(f"Error starting recording: {e}")
                return False

    def stop_recording(self):
        try:
            response = requests.post(f"{self.api_url}/stop_recording")
            if response.status_code == 200:
                self.is_recording = False
                return response.json().get("text", "")
            return ""
        except Exception as e:
            print(f"Error stopping recording: {e}")
            return ""

    def get_progress(self):
        if not self.is_recording:
            return 0.0
        elapsed = time.time() - self.start_time
        return min(0.1 + elapsed / self.duration, 1.0)


    def draw_recording_bar(self, screen):
        bar_width = 400
        bar_height = 40
        x = (screen.get_width() - bar_width) // 2
        y = screen.get_height() // 2

        # Create a surface with alpha channel for transparency
        bar_surface = pg.Surface((bar_width, bar_height), pg.SRCALPHA)

        # Draw background with transparency
        pg.draw.rect(bar_surface, self.BAR_BACKGROUND, (0, 0, bar_width, bar_height))

        # Draw progress with transparency
        progress = self.get_progress()
        pg.draw.rect(bar_surface, self.BAR_FILL, (0, 0, int(bar_width * progress), bar_height))

        # Draw border with transparency
        pg.draw.rect(bar_surface, self.BAR_BORDER, (0, 0, bar_width, bar_height), 2)

        # Blit the bar surface to the screen
        screen.blit(bar_surface, (x, y))

        # Draw "Recording..." text
        font = pg.font.Font(None, 36)
        text = font.render("Recording...", True, self.TEXT_COLOR)
        text_rect = text.get_rect(center=(screen.get_width() // 2, y - 30))
        screen.blit(text, text_rect)

    def draw_voice_recording(self, screen):
        if self.is_recording:
            if self.get_progress() >= 1.0:
                return self.stop_recording()
            else:
                self.draw_recording_bar(screen)

    def handle_record_button(self):
        if not self.is_recording:
            if self.start_recording():
                print("Started recording...")
