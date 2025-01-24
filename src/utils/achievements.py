import json
import os
from typing import Dict, List
import pygame as pg
from constants import WINDOW_WIDTH, WINDOW_HEIGHT


class AchievementManager:
    # Achievement display constants as percentages of screen size
    DISPLAY_WIDTH_PCT = 0.4  # 20% of screen width
    DISPLAY_HEIGHT_PCT = 0.25  # 15% of screen height
    MARGIN_PCT = 0.02  # 2% margin from screen edges
    ICON_SIZE_PCT = 0.2  # 10% of screen height for icon size

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
        """Draw active achievements with dynamic sizing"""
        current_time = pg.time.get_ticks()
        remaining_achievements = []

        # Base dimensions
        margin = int(WINDOW_WIDTH * self.MARGIN_PCT)
        icon_size = int(min(WINDOW_WIDTH, WINDOW_HEIGHT) * self.ICON_SIZE_PCT)
        min_height = icon_size + margin * 2

        for achievement in self.active_achievements:
            elapsed = current_time - achievement['start_time']

            if elapsed < self.display_time:
                # Start with initial font sizes
                title_font_size = int(min_height * 0.2)
                desc_font_size = int(min_height * 0.15)

                # Dynamically adjust font sizes and measure text
                title_font = pg.font.Font(None, title_font_size)
                desc_font = pg.font.Font(None, desc_font_size)

                name_text = achievement['data']['name']
                desc_text = achievement['data']['description']

                # Calculate required width for text
                name_width = title_font.size(name_text)[0]
                desc_width = desc_font.size(desc_text)[0]

                # Calculate required display width based on text and icon
                text_width = max(name_width, desc_width)
                display_width = icon_size + text_width + margin * 4

                # Limit width to maximum percentage of screen width
                max_width = int(WINDOW_WIDTH * self.DISPLAY_WIDTH_PCT)
                if display_width > max_width:
                    display_width = max_width
                    # Recalculate font sizes to fit width
                    available_text_width = max_width - icon_size - margin * 4
                    scale_factor = min(available_text_width / name_width,
                                       available_text_width / desc_width)
                    title_font_size = int(title_font_size * scale_factor)
                    desc_font_size = int(desc_font_size * scale_factor)
                    title_font = pg.font.Font(None, max(12, title_font_size))  # Minimum size of 12
                    desc_font = pg.font.Font(None, max(10, desc_font_size))  # Minimum size of 10

                # Calculate text heights with adjusted fonts
                name_height = title_font.size(name_text)[1]
                desc_height = desc_font.size(desc_text)[1]

                # Calculate required display height
                display_height = max(min_height, name_height + desc_height + margin * 3)

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
                    icon_y = (display_height - icon_size) // 2
                    surface.blit(icon, (margin, icon_y))

                # Render text with adjusted fonts
                name_surface = title_font.render(name_text, True, (255, 255, 255))
                desc_surface = desc_font.render(desc_text, True, (200, 200, 200))
                name_surface.set_alpha(achievement['alpha'])
                desc_surface.set_alpha(achievement['alpha'])

                # Position text next to icon
                text_x = icon_size + margin * 2
                name_y = (display_height - (name_height + desc_height + margin)) // 2
                desc_y = name_y + name_height + margin

                # Draw text
                surface.blit(name_surface, (text_x, name_y))
                surface.blit(desc_surface, (text_x, desc_y))

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
        if achievement_id in self.achievements and not self.achievements[achievement_id]['completed']:
            self.achievements[achievement_id]['completed'] = True
            self.active_achievements.append({
                'data': self.achievements[achievement_id],
                'start_time': pg.time.get_ticks(),
                'alpha': 255  # For fade effect
            })
            self.save_achievements()
