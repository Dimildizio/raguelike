import pygame as pg
from constants import *
from entities.monster import Monster
from entities.npc import NPC


class ContextMenu:
    def __init__(self, options, pos, font_size=24, title=None):
        self.options = options
        self.font = pg.font.Font(None, font_size)
        self.padding = 10
        self.margin_top = 5  # New margin for top spacing
        self.hover_index = -1
        self.title = title

        # Calculate menu dimensions
        text_widths = [self.font.size(option['name'])[0] for option in options]
        if title:
            text_widths.append(self.font.size(title)[0])
        self.width = max(text_widths) + self.padding * 2
        self.height = len(options) * (font_size + self.padding)
        if title:
            self.height += font_size + self.padding * 2  # Extra padding for separator line

        # Adjust position to ensure menu fits on screen
        x, y = pos
        if x + self.width > WINDOW_WIDTH:
            x = WINDOW_WIDTH - self.width
        if y + self.height > WINDOW_HEIGHT:
            y = WINDOW_HEIGHT - self.height

        self.x = max(0, x)  # Ensure x is not negative
        self.y = max(0, y)  # Ensure y is not negative

    def draw(self, screen):
        # Draw background with alpha
        menu_surface = pg.Surface((self.width, self.height), pg.SRCALPHA)
        pg.draw.rect(menu_surface, (50, 50, 50, 200), menu_surface.get_rect())
        screen.blit(menu_surface, (self.x, self.y))
        pg.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height), 2)

        y_offset = self.margin_top
        # Draw title if exists
        if self.title:
            text = self.font.render(self.title, True, YELLOW)
            screen.blit(text, (self.x + self.padding, self.y + y_offset))
            y_offset += self.font.get_height() + self.padding

            # Draw separator line
            pg.draw.line(screen, WHITE,
                         (self.x, self.y + y_offset),
                         (self.x + self.width, self.y + y_offset))
            y_offset += self.padding

        # Draw options
        for i, option in enumerate(self.options):
            color = RED if i == self.hover_index else WHITE
            text = self.font.render(option['name'], True, color)
            screen.blit(text, (self.x + self.padding,
                               self.y + y_offset + i * (self.font.get_height() + self.padding)))

    def get_option_at(self, mouse_pos):
        mx, my = mouse_pos
        if not (self.x <= mx <= self.x + self.width and self.y <= my <= self.y + self.height):
            return -1

        title_offset = 0
        if self.title:
            title_offset = self.font.get_height() + self.padding * 2 + self.margin_top

        option_idx = (my - self.y - title_offset) // (self.font.get_height() + self.padding)
        if 0 <= option_idx < len(self.options):
            return option_idx
        return -1


class MouseUI:
    def __init__(self, game):
        self.game = game
        self.selected_tile = None  # Store tile coordinates
        self.context_menu = None
        self.hovering_skill = None
        self.selected_skill = None
        self.selected_entity = None  # Add this to store the currently selected entity

    def get_tile_menu_options(self, tile_x, tile_y):
        if not (0 <= tile_x < self.game.state_manager.current_map.width and
                0 <= tile_y < self.game.state_manager.current_map.height):
            return []

        options = []
        tile = self.game.state_manager.current_map.tiles[tile_y][tile_x]

        # First menu: Select target (tile or entities)
        target_options = []

        # Add tile as an option
        target_options.append({
            'name': 'Ground',
            'type': 'tile',
            'submenu': [
                {'name': 'Move here', 'action': 'move'},
                {'name': 'Examine', 'action': 'examine'}
            ]
        })

        # Add entities
        for entity in tile.entities:
            if isinstance(entity, Monster):
                target_options.append({
                    'name': f"{entity.name} ({entity.monster_type})",
                    'type': 'monster',
                    'entity': entity,
                    'submenu': [
                        {'name': 'Attack', 'action': 'attack'},
                        {'name': 'Talk', 'action': 'talk'} if entity.can_talk else None,
                        {'name': 'Examine', 'action': 'examine'}
                    ]
                })
            elif isinstance(entity, NPC):
                target_options.append({
                    'name': entity.name,
                    'type': 'npc',
                    'entity': entity,
                    'submenu': [
                        {'name': 'Talk', 'action': 'talk'},
                        {'name': 'Trade', 'action': 'trade'},
                        {'name': 'Examine', 'action': 'examine'}
                    ]
                })

        # Remove None values from submenus
        for option in target_options:
            if 'submenu' in option:
                option['submenu'] = [item for item in option['submenu'] if item is not None]

        return target_options

    def handle_mouse_input(self, event):
        if not self.game.state_manager.player:
            return

        mouse_pos = pg.mouse.get_pos()
        world_x = mouse_pos[0] + self.game.camera_x
        world_y = mouse_pos[1] + self.game.camera_y
        tile_x = world_x // DISPLAY_TILE_SIZE
        tile_y = world_y // DISPLAY_TILE_SIZE

        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 3:  # Right click
                options = self.get_tile_menu_options(tile_x, tile_y)
                if options:
                    self.selected_tile = (tile_x, tile_y)
                    self.context_menu = ContextMenu(options, mouse_pos)
            elif event.button == 1:  # Left click
                if self.context_menu:
                    option_idx = self.context_menu.get_option_at(mouse_pos)
                    if option_idx >= 0:
                        selected = self.context_menu.options[option_idx]
                        if 'submenu' in selected:
                            self.selected_entity = selected.get('entity')
                            # Calculate position for submenu
                            submenu_x = mouse_pos[0]
                            # Position y so that mouse points to first option
                            font_height = self.context_menu.font.get_height()
                            title_offset = font_height + self.context_menu.padding * 2 + self.context_menu.margin_top
                            submenu_y = mouse_pos[1] - title_offset

                            self.context_menu = ContextMenu(
                                selected['submenu'],
                                (submenu_x, submenu_y),
                                title=selected['name']
                            )
                        else:
                            self.handle_menu_action(selected)
                    else:
                        self.context_menu = None
                        self.selected_tile = None
                        self.selected_entity = None
                else:
                    # Check if clicked on skills panel
                    skill_idx = self.get_clicked_skill(mouse_pos)
                    if skill_idx >= 0:
                        self.selected_skill = self.game.state_manager.player.skills[skill_idx]

    def handle_menu_action(self, option):
        if not self.selected_tile:
            return

        tile_x, tile_y = self.selected_tile
        action = option.get('action')
        entity = self.selected_entity  # Use the stored entity instead of getting it from the option

        if action == 'move':
            # Keep trying to move until we can't anymore
            player = self.game.state_manager.player
            while player.move_to_target(tile_x, tile_y, self.game.state_manager.current_map):
                pass  # Continue moving until we can't move anymore
        elif action == 'talk':
            self.game.try_interact_with_npc(tile_x, tile_y, click_talk=True)
        elif action == 'examine':
            if entity:
                self.game.state_manager.add_message(
                    f"You see {entity.description}", WHITE)
            else:
                self.game.state_manager.add_message(
                    "You see nothing special here", WHITE)
        elif action == 'attack':
            if isinstance(entity, Monster):
                pass

        self.context_menu = None
        self.selected_tile = None
        self.selected_entity = None

    def draw(self, screen):
        # Draw context menu if active
        if self.context_menu:
            self.context_menu.draw(screen)

    def get_clicked_skill(self, mouse_pos):
        # Calculate skill panel area
        panel_start_x = WINDOW_WIDTH // 2 - 2 * SKILL_PANEL_SIZE
        panel_y = WINDOW_HEIGHT - 10 - SKILL_PANEL_SIZE

        for i in range(len(self.game.state_manager.player.skills)):
            skill_x = panel_start_x + SKILL_PANEL_SIZE * i + i * SKILL_OFFSET
            skill_rect = pg.Rect(skill_x, panel_y, SKILL_PANEL_SIZE, SKILL_PANEL_SIZE)
            if skill_rect.collidepoint(mouse_pos):
                print(self.game.state_manager.player.skills[i].name)
                return i
        return -1