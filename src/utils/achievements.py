import json
import os
from typing import Dict, List
import pygame as pg
from constants import WINDOW_WIDTH, WINDOW_HEIGHT


class AchievementManager:
    # Achievement display constants as percentages of screen size
    DISPLAY_WIDTH_PCT = 0.2  # 20% of screen width
    DISPLAY_HEIGHT_PCT = 0.15  # 15% of screen height
    MARGIN_PCT = 0.02  # 2% margin from screen edges
    ICON_SIZE_PCT = 0.1  # 10% of screen height for icon size

    def __init__(self, save_file="data/achievements.json"):
        self.save_file = save_file
        self.achievements = {
            "goblin_slayer": {
                "name": "Goblin Slayer",
                "description": "Kill 10 goblins",
                "image": "assets/achievements/goblin_slayer.png",
                "completed": False
            },
            "quest_master": {
                "name": "Quest Master",
                "description": "Complete your first quest",
                "image": "assets/achievements/quest_master.png",
                "completed": False
            }
        }
        self.active_achievements: List[Dict] = []
        self.display_time = 5000  # 5 seconds in milliseconds
        self.achievement_images = {}  # Cache for resized images
        self.load_achievements()
        self.load_images()

    def load_images(self):
        """Load and resize achievement images"""
        icon_size = int(min(WINDOW_WIDTH, WINDOW_HEIGHT) * self.ICON_SIZE_PCT)

        for achievement_id, data in self.achievements.items():
            try:
                original_image = pg.image.load(data['image']).convert_alpha()
                # Resize from 1024x1024 to icon_size x icon_size
                resized_image = pg.transform.smoothscale(original_image, (icon_size, icon_size))
                self.achievement_images[achievement_id] = resized_image
            except Exception as e:
                print(f"Error loading achievement image {data['image']}: {e}")
                # Create a fallback colored square if image loading fails
                fallback = pg.Surface((icon_size, icon_size))
                fallback.fill((100, 100, 100))
                self.achievement_images[achievement_id] = fallback

    def draw(self, screen):
        """Draw active achievements"""
        current_time = pg.time.get_ticks()
        remaining_achievements = []

        # Calculate dimensions based on screen size
        display_width = int(WINDOW_WIDTH * self.DISPLAY_WIDTH_PCT)
        display_height = int(WINDOW_HEIGHT * self.DISPLAY_HEIGHT_PCT)
        margin = int(WINDOW_WIDTH * self.MARGIN_PCT)
        icon_size = int(min(WINDOW_WIDTH, WINDOW_HEIGHT) * self.ICON_SIZE_PCT)

        # Calculate text area dimensions
        text_area_width = display_width - icon_size - margin

        for achievement in self.active_achievements:
            elapsed = current_time - achievement['start_time']

            if elapsed < self.display_time:
                # Calculate position (top-right corner)
                x = WINDOW_WIDTH - display_width - margin
                y = margin

                # Create achievement display surface
                surface = pg.Surface((display_width, display_height), pg.SRCALPHA)

                # Calculate alpha for fade effect
                if elapsed > self.display_time - 1000:
                    achievement['alpha'] = max(0, 255 * (self.display_time - elapsed) / 1000)

                # Draw achievement background
                bg_color = (0, 0, 0, min(200, achievement['alpha']))
                pg.draw.rect(surface, bg_color, (0, 0, display_width, display_height), border_radius=10)

                # Draw achievement icon
                achievement_id = next(k for k, v in self.achievements.items() if v == achievement['data'])
                if achievement_id in self.achievement_images:
                    icon = self.achievement_images[achievement_id]
                    icon.set_alpha(achievement['alpha'])
                    surface.blit(icon, (margin, (display_height - icon_size) // 2))

                # Draw achievement text
                font_size = int(display_height * 0.25)  # Dynamic font size
                font = pg.font.Font(None, font_size)

                # Name text
                name_text = font.render(achievement['data']['name'], True, (255, 255, 255))
                name_text.set_alpha(achievement['alpha'])

                # Description text (slightly smaller)
                desc_font = pg.font.Font(None, int(font_size * 0.8))
                desc_text = desc_font.render(achievement['data']['description'], True, (200, 200, 200))
                desc_text.set_alpha(achievement['alpha'])

                # Position text next to icon
                text_x = icon_size + margin * 2
                name_y = margin
                desc_y = display_height // 2

                surface.blit(name_text, (text_x, name_y))
                surface.blit(desc_text, (text_x, desc_y))

                screen.blit(surface, (x, y))
                remaining_achievements.append(achievement)

        self.active_achievements = remaining_achievements

    def load_achievements(self):
        """Load achievements from file or create new if doesn't exist"""
        try:
            if os.path.exists(self.save_file):
                with open(self.save_file, 'r') as f:
                    saved_data = json.load(f)
                    # Update only the 'completed' status from saved data
                    for achievement_id, data in saved_data.items():
                        if achievement_id in self.achievements:
                            self.achievements[achievement_id]['completed'] = data['completed']
        except Exception as e:
            print(f"Error loading achievements: {e}")

    def save_achievements(self):
        """Save achievements to file"""
        try:
            with open(self.save_file, 'w') as f:
                json.dump(self.achievements, f)
        except Exception as e:
            print(f"Error saving achievements: {e}")

    def check_achievements(self, stats):
        """Check if any achievements have been completed"""
        goblin_kills = stats['monsters_killed'].get('goblin', 0)
        quests_completed = stats['quests_completed']

        if not self.achievements['goblin_slayer']['completed'] and goblin_kills >= 10:
            self.unlock_achievement('goblin_slayer')

        if not self.achievements['quest_master']['completed'] and quests_completed >= 1:
            self.unlock_achievement('quest_master')

    def unlock_achievement(self, achievement_id):
            """Unlock an achievement and add it to display queue"""
            #if achievement_id in self.achievements and not self.achievements[achievement_id]['completed']:
            #self.achievements[achievement_id]['completed'] = True
            self.active_achievements.append({
                'data': self.achievements[achievement_id],
                'start_time': pg.time.get_ticks(),
                'alpha': 255  # For fade effect
            })
            self.save_achievements()
