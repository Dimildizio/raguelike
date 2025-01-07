import pygame
import sys

from game_state import GameStateManager, GameState
from entities.character import Character
from world.worldmap import WorldMap  
from constants import *
from entities.monster import Monster
from entities.npc import NPC
from constants import SPRITES



class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)
        self.clock = pygame.time.Clock()
        self.state_manager = GameStateManager()

    def update_camera(self):
        # Center camera on player
        if self.state_manager.player:
            # Calculate where the camera should be to center on player
            self.camera_x = self.state_manager.player.x - WINDOW_WIDTH // 2 + DISPLAY_TILE_SIZE // 2
            self.camera_y = self.state_manager.player.y - WINDOW_HEIGHT // 2 + DISPLAY_TILE_SIZE // 2
            
            # Optional: Add camera bounds to prevent showing outside the map
            max_camera_x = self.state_manager.current_map.width * DISPLAY_TILE_SIZE - WINDOW_WIDTH
            max_camera_y = self.state_manager.current_map.height * DISPLAY_TILE_SIZE - WINDOW_HEIGHT
            
            # Clamp camera position
            self.camera_x = max(0, min(self.camera_x, max_camera_x))
            self.camera_y = max(0, min(self.camera_y, max_camera_y))
    
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.handle_input(event)

            # Update
            if self.state_manager.current_state == GameState.PLAYING:
                if self.state_manager.player:  # Check if player exists
                    self.state_manager.player.update()
                    for entity in self.state_manager.current_map.entities:
                        entity.update()
                    self.update_camera() 
            elif self.state_manager.current_state == GameState.COMBAT:
                self.update_combat()

            # Draw
            self.screen.fill(BLACK)
            if self.state_manager.current_state == GameState.PLAYING:
                if self.state_manager.player:  # Check if player exists
                    self.state_manager.current_map.draw(self.screen, 
                                                      self.camera_x, 
                                                      self.camera_y)
            elif self.state_manager.current_state == GameState.COMBAT:
                self.draw_combat()
            elif self.state_manager.current_state == GameState.MAIN_MENU:
                self.draw_menu()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

    def update_combat(self):
        if self.state_manager.combat_system.is_combat_active:
            current_entity = self.state_manager.combat_system.turn_order[
                self.state_manager.combat_system.current_turn]
            if isinstance(current_entity, Monster):
                # AI turn
                self.handle_monster_turn(current_entity)

    def handle_monster_turn(self, monster):
        # Simple AI: attack player
        damage = self.state_manager.combat_system.process_attack(monster, self.state_manager.player)
        self.state_manager.combat_system.next_turn()

    def handle_input(self, event):
        if self.state_manager.current_state == GameState.PLAYING:
            self.handle_playing_input(event)
        elif self.state_manager.current_state == GameState.COMBAT:
            self.handle_combat_input(event)
        elif self.state_manager.current_state == GameState.MAIN_MENU:
            self.handle_menu_input(event)

    def handle_combat_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:  # Basic attack
                current_entity = self.state_manager.combat_system.turn_order[
                    self.state_manager.combat_system.current_turn]
                if isinstance(current_entity, Character):  # Player's turn
                    target = self.state_manager.combat_system.current_target
                    if target:
                        damage = self.state_manager.combat_system.process_attack(current_entity, target)
                        self.state_manager.combat_system.next_turn()

    def handle_playing_input(self, event):
        if event.type == pygame.KEYDOWN:
            player_tile_x = self.state_manager.player.x // self.state_manager.current_map.tile_size
            player_tile_y = self.state_manager.player.y // self.state_manager.current_map.tile_size

            # Movement
            if event.key == pygame.K_w:  # Up
                self.state_manager.player.set_facing(DIRECTION_UP)
                self.state_manager.current_map.move_entity(
                    self.state_manager.player,
                    player_tile_x,
                    player_tile_y - 1
                )
            elif event.key == pygame.K_s:  # Down

                self.state_manager.player.set_facing(DIRECTION_DOWN)
                self.state_manager.current_map.move_entity(
                    self.state_manager.player,
                    player_tile_x,
                    player_tile_y + 1
                )
            elif event.key == pygame.K_a:  # Left

                self.state_manager.player.set_facing(DIRECTION_LEFT)
                self.state_manager.current_map.move_entity(
                    self.state_manager.player,
                    player_tile_x - 1,
                    player_tile_y
                )
            elif event.key == pygame.K_d:  # Right
                self.state_manager.player.set_facing(DIRECTION_RIGHT)
                self.state_manager.current_map.move_entity(
                    self.state_manager.player,
                    player_tile_x + 1,
                    player_tile_y
                )

            # Interaction
            elif event.key == pygame.K_e:  # Interact
                # Check adjacent tiles for NPCs
                adjacent_positions = [
                    (player_tile_x + 1, player_tile_y),
                    (player_tile_x - 1, player_tile_y),
                    (player_tile_x, player_tile_y + 1),
                    (player_tile_x, player_tile_y - 1)
                ]

                for pos_x, pos_y in adjacent_positions:
                    tile = self.state_manager.current_map.get_tile_at(pos_x, pos_y)
                    if tile and tile.entity and isinstance(tile.entity, NPC):
                        self.state_manager.change_state(GameState.DIALOG)
                        break

            # Menu controls
            elif event.key == pygame.K_i:  # Inventory
                self.state_manager.change_state(GameState.INVENTORY)
            elif event.key == pygame.K_ESCAPE:  # Menu
                self.state_manager.change_state(GameState.MAIN_MENU)

    def handle_menu_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w or event.key == pygame.K_UP:  # Move up
                self.state_manager.selected_menu_item = (self.state_manager.selected_menu_item - 1) % len(MENU_OPTIONS)
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:  # Move down
                self.state_manager.selected_menu_item = (self.state_manager.selected_menu_item + 1) % len(MENU_OPTIONS)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:  # Select option
                self.handle_menu_selection()
            elif event.key == pygame.K_ESCAPE:  # Return to game if we were playing
                if self.state_manager.player:  # If game is in progress
                    self.state_manager.change_state(GameState.PLAYING)

    def handle_menu_selection(self):
        selected_option = MENU_OPTIONS[self.state_manager.selected_menu_item]
        if selected_option == "New Game":
            self.state_manager.start_new_game()  # Initialize player and entities
            self.state_manager.change_state(GameState.PLAYING)
        elif selected_option == "Load Game":
            # Implement load game functionality
            pass
        elif selected_option == "Settings":
            # Implement settings menu
            pass
        elif selected_option == "Quit":
            pygame.quit()
            sys.exit()

    def draw_menu(self):
        # Draw menu background
        self.screen.fill(BLACK)

        # Draw title
        title_font = pygame.font.Font(None, MENU_FONT_SIZE * 2)
        title_surface = title_font.render(GAME_TITLE, True, WHITE)
        title_rect = title_surface.get_rect(centerx=WINDOW_WIDTH // 2, y=50)
        self.screen.blit(title_surface, title_rect)

        # Draw menu options
        menu_font = pygame.font.Font(None, MENU_FONT_SIZE)
        for i, option in enumerate(MENU_OPTIONS):
            color = RED if i == self.state_manager.selected_menu_item else WHITE
            text_surface = menu_font.render(option, True, color)
            text_rect = text_surface.get_rect(
                centerx=WINDOW_WIDTH // 2,
                y=MENU_START_Y + i * MENU_SPACING
            )
            self.screen.blit(text_surface, text_rect)


    def draw_combat(self):
        # Fill background
        self.screen.fill(BLACK)

        # Draw combat UI area at bottom of screen
        combat_ui_rect = pygame.Rect(0, WINDOW_HEIGHT - COMBAT_UI_HEIGHT,
                                     WINDOW_WIDTH, COMBAT_UI_HEIGHT)
        pygame.draw.rect(self.screen, (50, 50, 50), combat_ui_rect)

        # Draw entities
        player = self.state_manager.player
        current_enemy = self.state_manager.combat_system.current_target

        # Draw player on left side
        player_x = WINDOW_WIDTH // 4
        player_y = WINDOW_HEIGHT // 2
        player.draw(self.screen, player_x - player.x, player_y - player.y)

        # Draw enemy on right side
        if current_enemy:
            enemy_x = (WINDOW_WIDTH * 3) // 4
            enemy_y = WINDOW_HEIGHT // 2
            current_enemy.draw(self.screen, enemy_x - current_enemy.x, enemy_y - current_enemy.y)

        # Draw health bars
        self.draw_health_bar(self.screen, player, COMBAT_UI_PADDING,
                             WINDOW_HEIGHT - COMBAT_UI_HEIGHT + COMBAT_UI_PADDING)
        if current_enemy:
            self.draw_health_bar(self.screen, current_enemy,
                                 WINDOW_WIDTH // 2 + COMBAT_UI_PADDING,
                                 WINDOW_HEIGHT - COMBAT_UI_HEIGHT + COMBAT_UI_PADDING)

        # Draw turn indicator
        font = pygame.font.Font(None, 36)
        current_entity = self.state_manager.combat_system.turn_order[
            self.state_manager.combat_system.current_turn]
        turn_text = f"Current Turn: {current_entity.__class__.__name__}"
        text_surface = font.render(turn_text, True, WHITE)
        text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, 50))
        self.screen.blit(text_surface, text_rect)


    def draw_health_bar(self, screen, entity, x, y):
        # Draw health bar background
        bar_bg_rect = pygame.Rect(x, y, HEALTH_BAR_WIDTH, HEALTH_BAR_HEIGHT)
        pygame.draw.rect(screen, RED, bar_bg_rect)

        # Draw current health
        health_percentage = entity.health / PLAYER_START_HP  # You might want to use max_health instead
        health_width = int(HEALTH_BAR_WIDTH * health_percentage)
        health_rect = pygame.Rect(x, y, health_width, HEALTH_BAR_HEIGHT)
        pygame.draw.rect(screen, GREEN, health_rect)

        # Draw health text
        font = pygame.font.Font(None, 24)
        health_text = f"HP: {entity.health}"
        text_surface = font.render(health_text, True, WHITE)
        text_rect = text_surface.get_rect(
            centerx=x + HEALTH_BAR_WIDTH // 2,
            centery=y + HEALTH_BAR_HEIGHT // 2
        )
        screen.blit(text_surface, text_rect)

        # Draw entity name
        name_text = entity.__class__.__name__
        name_surface = font.render(name_text, True, WHITE)
        name_rect = name_surface.get_rect(
            centerx=x + HEALTH_BAR_WIDTH // 2,
            bottom=y - 5
        )
        screen.blit(name_surface, name_rect)


if __name__ == "__main__":
    game = Game()
    game.run()