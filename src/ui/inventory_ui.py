import pygame as pg
from src.constants import *


class InventoryUI:
    def __init__(self, game_state):
        self.game_state = game_state

        # Use constants for grid dimensions
        self.grid_width = 4
        self.grid_height = 4

        # Use the constant from constants.py for slot size
        self.slot_size = INVENTORY_TILE_SIZE

        # Make padding and margin relative to screen size
        self.padding = int(WINDOW_WIDTH * 0.01)  # 1% of screen width
        self.margin = int(WINDOW_WIDTH * 0.02)  # 2% of screen width

        self.selected_slot = None
        self.dragging_item = None
        self.drag_start_pos = None

        # Calculate inventory panel dimensions
        self.panel_width = self.grid_width * self.slot_size + (self.grid_width - 1) * self.padding + 2 * self.margin
        self.panel_height = self.grid_height * self.slot_size + (self.grid_height - 1) * self.padding + 2 * self.margin

        # Position the panel in the right half of the screen
        self.panel_x = WINDOW_WIDTH // 2 + (WINDOW_WIDTH // 2 - self.panel_width) // 2
        self.panel_y = int(WINDOW_HEIGHT * 0.15)  # Position at 25% from the top

        # Info panel dimensions - scale with screen size
        self.info_panel_width = int(WINDOW_WIDTH * 0.6)  # 60% of screen width
        self.info_panel_height = int(WINDOW_HEIGHT * 0.25)  # 25% of screen height
        self.info_panel_x = (WINDOW_WIDTH - self.info_panel_width) // 2
        self.info_panel_y = WINDOW_HEIGHT - self.info_panel_height - int(WINDOW_HEIGHT * 0.05)  # 5% margin from bottom

        # Create font for item labels - scale with screen size
        self.font_size = int(WINDOW_HEIGHT * 0.023)  # ~18px at 768 height
        self.font = pg.font.Font(None, self.font_size)
        self.bag_bg = pg.image.load("assets/images/art/bag_background.png").convert_alpha()
        # Scale to fit the right half of the screen, from top to info panel
        self.bag_bg_width = WINDOW_WIDTH // 2
        self.bag_bg_height = WINDOW_HEIGHT - self.info_panel_height - int(WINDOW_HEIGHT * 0.05)
        self.bag_bg = pg.transform.scale(self.bag_bg, (self.bag_bg_width, self.bag_bg_height))
        self.bag_bg_x = WINDOW_WIDTH // 2
        self.bag_bg_y = 0

    def destroy_ui(self):
        """Clean up any resources used by the inventory UI"""
        self.selected_slot = None
        self.dragging_item = None
        self.drag_start_pos = None
        print('STATE:', self.game_state.current_state)

    def draw(self, screen):
        # Draw semi-transparent background overlay
        overlay = pg.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Black with 70% opacity
        screen.blit(overlay, (0, 0))

        # Draw the bag background on the right side
        screen.blit(self.bag_bg, (self.bag_bg_x, self.bag_bg_y))

        # Draw title - scale font with screen size
        title_font_size = int(WINDOW_HEIGHT * 0.042)  # ~32px at 768 height
        title_font = pg.font.Font(None, title_font_size)
        title_text = title_font.render("Inventory", True, WHITE)
        title_rect = title_text.get_rect(centerx=self.panel_x + self.panel_width // 2,
                                         y=self.panel_y - int(WINDOW_HEIGHT * 0.052))  # ~40px at 768 height
        screen.blit(title_text, title_rect)

        self.draw_inventory_grid(screen)
        self.draw_info_panel(screen)

        # Draw dragging item if applicable
        if self.dragging_item:
            mouse_pos = pg.mouse.get_pos()
            item = self.dragging_item
            screen.blit(item.inv_surface, (mouse_pos[0] - self.slot_size // 2,
                                           mouse_pos[1] - self.slot_size // 2))

    def draw_inventory_grid(self, screen):
        inventory = self.game_state.player.inventory

        for y in range(self.grid_height):
            for x in range(self.grid_width):
                # Calculate slot position
                slot_x = self.panel_x + self.margin + x * (self.slot_size + self.padding)
                slot_y = self.panel_y + self.margin + y * (self.slot_size + self.padding)

                # Draw slot outline only
                slot_rect = pg.Rect(slot_x, slot_y, self.slot_size, self.slot_size)
                slot_surface = pg.Surface((self.slot_size, self.slot_size), pg.SRCALPHA)
                slot_surface.fill((GREY + (150,)))  # Dark gray with 50% transparency
                screen.blit(slot_surface, (slot_x, slot_y))

                # Highlight selected slot with a more visible outline
                if self.selected_slot == (x, y):
                    pg.draw.rect(screen, (255, 215, 0), slot_rect, 2)  # Gold outline for selected slot
                else:
                    pg.draw.rect(screen, (200, 200, 200, 150), slot_rect, 1)  # Light gray border

                # Draw item if exists in this slot
                index = y * self.grid_width + x
                if index < len(inventory):
                    item = inventory[index]
                    if item != self.dragging_item:  # Don't draw item if it's being dragged
                        screen.blit(item.inv_surface, (slot_x, slot_y))


                        # Draw item count if stackable (future feature)
                        # if hasattr(item, 'count') and item.count > 1:
                        #     count_text = self.font.render(str(item.count), True, WHITE)
                        #     screen.blit(count_text, (slot_x + self.slot_size - 15, slot_y + self.slot_size - 15))

    def draw_info_panel(self, screen):
        # Draw info panel at the bottom center
        info_rect = pg.Rect(self.info_panel_x, self.info_panel_y, self.info_panel_width, self.info_panel_height)
        pg.draw.rect(screen, (50, 50, 50), info_rect)
        pg.draw.rect(screen, (100, 100, 100), info_rect, 2)  # Border

        # If an item is selected, display its information
        if self.selected_slot is not None:
            index = self.selected_slot[1] * self.grid_width + self.selected_slot[0]
            if index < len(self.game_state.player.inventory):
                item = self.game_state.player.inventory[index]

                # Scale fonts with screen size
                name_font_size = int(WINDOW_HEIGHT * 0.036)  # ~28px at 768 height
                desc_font_size = int(WINDOW_HEIGHT * 0.029)  # ~22px at 768 height
                stats_font_size = int(WINDOW_HEIGHT * 0.026)  # ~20px at 768 height

                name_font = pg.font.Font(None, name_font_size)
                desc_font = pg.font.Font(None, desc_font_size)
                stats_font = pg.font.Font(None, stats_font_size)

                # Draw item name
                name_text = name_font.render(item.name, True, WHITE)
                name_rect = name_text.get_rect(centerx=self.info_panel_x + self.info_panel_width // 2,
                                               y=self.info_panel_y + int(self.info_panel_height * 0.1))
                screen.blit(name_text, name_rect)

                # Draw item description
                desc_text = desc_font.render(item.description, True, WHITE)
                desc_rect = desc_text.get_rect(centerx=self.info_panel_x + self.info_panel_width // 2,
                                               y=self.info_panel_y + int(self.info_panel_height * 0.3))
                screen.blit(desc_text, desc_rect)

                # Draw item stats in two columns
                left_col_x = self.info_panel_x + self.info_panel_width // 4
                right_col_x = self.info_panel_x + 3 * self.info_panel_width // 4
                y_offset = int(self.info_panel_height * 0.5)  # Start at 50% of panel height
                line_height = int(self.info_panel_height * 0.125)  # ~25px at 200px panel height

                # Left column
                # Draw item type
                type_text = stats_font.render(f"Type: {item.item_type}", True, WHITE)
                type_rect = type_text.get_rect(centerx=left_col_x, y=self.info_panel_y + y_offset)
                screen.blit(type_text, type_rect)
                y_offset += line_height

                # Draw item value
                value_text = stats_font.render(f"Value: {item.price} gold", True, YELLOW)
                value_rect = value_text.get_rect(centerx=left_col_x, y=self.info_panel_y + y_offset)
                screen.blit(value_text, value_rect)
                y_offset += line_height

                # Draw item weight
                weight_text = stats_font.render(f"Weight: {item.weight}", True, WHITE)
                weight_rect = weight_text.get_rect(centerx=left_col_x, y=self.info_panel_y + y_offset)
                screen.blit(weight_text, weight_rect)

                # Right column - stats and equip info
                y_offset = int(self.info_panel_height * 0.5)  # Reset to 50% of panel height

                # Draw item stats if any
                if item.stats:
                    for stat, value in item.stats.items():
                        stat_text = stats_font.render(f"{stat.capitalize()}: {value}", True,
                                                      GREEN if stat == 'heal' else WHITE)
                        stat_rect = stat_text.get_rect(centerx=right_col_x, y=self.info_panel_y + y_offset)
                        screen.blit(stat_text, stat_rect)
                        y_offset += line_height

                # Draw equip status if applicable
                if item.equippable:
                    equipped = False
                    for slot, equipped_item in self.game_state.player.inv_slots.items():
                        if equipped_item == item:
                            equipped = True
                            equip_text = stats_font.render(f"Equipped in {slot} slot", True, GREEN)
                            equip_rect = equip_text.get_rect(centerx=right_col_x, y=self.info_panel_y + y_offset)
                            screen.blit(equip_text, equip_rect)
                            break

                    if not equipped:
                        equip_text = stats_font.render(f"Can be equipped in {item.slot} slot", True, WHITE)
                        equip_rect = equip_text.get_rect(centerx=right_col_x, y=self.info_panel_y + y_offset)
                        screen.blit(equip_text, equip_rect)

    def handle_input(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE or event.key == pg.K_i:
                return True

        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = pg.mouse.get_pos()
                clicked_slot = self.get_slot_at_position(mouse_pos)

                if clicked_slot is not None:
                    index = clicked_slot[1] * self.grid_width + clicked_slot[0]
                    if index < len(self.game_state.player.inventory):
                        # Select the slot
                        self.selected_slot = clicked_slot

                        # Future: Start dragging the item
                        # self.dragging_item = self.game_state.player.inventory[index]
                        # self.drag_start_pos = clicked_slot

            return True  # Event was handled

        return False  # Event was not handled

    def get_slot_at_position(self, pos):
        # Check if position is within the inventory grid
        if (self.panel_x <= pos[0] <= self.panel_x + self.panel_width and
                self.panel_y <= pos[1] <= self.panel_y + self.panel_height):

            # Calculate relative position within the grid
            rel_x = pos[0] - (self.panel_x + self.margin)
            rel_y = pos[1] - (self.panel_y + self.margin)

            # Calculate grid coordinates
            grid_x = rel_x // (self.slot_size + self.padding)
            grid_y = rel_y // (self.slot_size + self.padding)

            # Check if click is within a valid slot
            if (0 <= grid_x < self.grid_width and
                    0 <= grid_y < self.grid_height and
                    rel_x % (self.slot_size + self.padding) < self.slot_size and
                    rel_y % (self.slot_size + self.padding) < self.slot_size):
                return int(grid_x), int(grid_y)

        return None
