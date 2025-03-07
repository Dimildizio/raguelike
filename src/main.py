import pygame as pg
import sys
import time
import gc
import random
from game_state import GameStateManager
from systems.sound_manager import SoundManager
from systems.save_system import SaveSystem
from utils.async_requests_handler import AsyncRequestHandler
from constants import *
from entities.entity import House
from entities.monster import Monster
from entities.npc import NPC
from ui.dialog_ui import DialogUI
from ui.mouse_ui import MouseUI
from ui.inventory_ui import InventoryUI


class Game:
    def __init__(self):
        pg.init()
        # self.screen = pg.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pg.FULLSCREEN)
        self.screen = pg.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.load_loading_image()
        pg.display.set_caption(GAME_TITLE)
        self.clock = pg.time.Clock()
        self.last_action_time = 0
        self.sound_manager = SoundManager(SOUND_DIR)
        self.state_manager = GameStateManager(self.sound_manager, self)
        self.dialog_ui = DialogUI(self.state_manager, self.sound_manager)
        self.async_handler = AsyncRequestHandler()
        self.mouse_ui = MouseUI(self)
        self.inventory_ui = None
        self.monsters_queue = None
        self.camera_x = None
        self.camera_y = None
        self.update_camera()

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

    def exit_dialogue(self):
        print('EXITING DIALOGUE')
        self.dialog_ui.should_exit = False  # Reset flag
        self.dialog_ui.clear_dialogue_state()
        self.state_manager.current_npc = None
        self.state_manager.change_state(GameState.PLAYING)

    def check_async_requests(self):
        self.async_handler.process_requests(self.dialog_ui.dialogue_processor)
        completed_requests = self.async_handler.get_completed_requests()
        for request in completed_requests:
            self.dialog_ui.handle_async_response(request)

    def run(self):
        running = True
        while running:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                elif event.type == pg.USEREVENT + 1:  # Music track ended
                    self.sound_manager.play_next_track()
                self.handle_input(event)
            if self.state_manager.current_state == GameState.DIALOG and self.dialog_ui.should_exit:
                self.exit_dialogue()
            # Updates
            if self.state_manager.current_state == GameState.PLAYING:
                if self.state_manager.player:  # Check if player exists
                    self.state_manager.player.update()
                    self.state_manager.floating_text_manager.update()
                    self.state_manager.current_map.update(self.camera_x, self.camera_y)
                    self.check_async_requests()
                    self.update_camera()
                    self.state_manager.achievement_manager.check_achievements(self.state_manager.stats)
                    if hasattr(self, 'monsters_queue') and self.monsters_queue:
                        self.process_next_monster()
                        if not self.monsters_queue:
                            self.state_manager.add_message("Your turn", BLUE)
            # Draw
            self.screen.fill(BLACK)
            if self.state_manager.current_state == GameState.PLAYING:
                if self.state_manager.player:  # Check if player exists
                    self.state_manager.current_map.draw(self.screen, self.camera_x, self.camera_y)
                    self.state_manager.floating_text_manager.draw(self.screen, self.camera_x, self.camera_y)
                    self.draw_player_ui()
                    self.state_manager.draw_progress_voice(self.screen)
                    if self.state_manager.message_log:
                        self.state_manager.message_log.draw(self.screen)
                    self.state_manager.achievement_manager.draw(self.screen)
            elif self.state_manager.current_state == GameState.MAIN_MENU:
                self.draw_menu()
            elif self.state_manager.current_state == GameState.INVENTORY:
                if not self.inventory_ui:
                    self.inventory_ui = InventoryUI(self.state_manager)
                #self.state_manager.current_map.draw(self.screen, self.camera_x, self.camera_y)
                self.inventory_ui.draw(self.screen)
            elif self.state_manager.current_state == GameState.DIALOG:
                self.dialog_ui.update()
                self.dialog_ui.draw(self.screen, self.state_manager.current_npc)
            elif self.state_manager.current_state == GameState.PROCESSING:
                self.draw_loading_screen()
            elif self.state_manager.current_state == GameState.DEAD:
                self.draw_death_screen()
            elif self.state_manager.current_state == GameState.DEMO_COMPLETE:
                self.draw_demo_complete_screen()

            pg.display.flip()
            self.sound_manager.update()
            self.clock.tick(FPS)
            gc.collect()

        # Quit
        self.sound_manager.stop_all()
        pg.quit()

    def handle_monster_turns(self):
        # Get all monsters from the current map
        self.monsters_queue = [entity for entity in self.state_manager.current_map.entities
                               if isinstance(entity, Monster) and entity.is_alive]
        # Reset action points for all monsters
        for monster in self.monsters_queue:
            monster.reset_action_points()
            monster.shout_cooldown = max(0, monster.shout_cooldown - 1)
        # Start processing the first monster
        self.process_next_monster()

    def process_next_monster(self):
        # If there are no more monsters to process, we're done
        if not self.monsters_queue:
            return

        # Get the next monster
        monster = self.monsters_queue[0]
        if not monster.is_alive:
            self.monsters_queue.pop(0)
            return self.process_next_monster()
        print(monster.name, 'acts')
        if monster.try_initiate_dialog((self.state_manager.player.x, self.state_manager.player.y)):
            # Monster wants to talk - switch to dialog state
            self.dialog_ui.current_npc = monster
            self.state_manager.current_npc = monster

            self.state_manager.change_state(GameState.DIALOG)
            self.dialog_ui.start_dialog(monster)
            self.monsters_queue.pop(0)

        # If no dialog initiated, proceed with normal monster turn
        elif monster.is_hostile:
            if monster.dist2player((self.state_manager.player.x, self.state_manager.player.y), DIALOGUE_DISTANCE)\
              and monster.can_shout():
                self.async_handler.add_request('shout', monster)
            # If there's an animation playing, wait
            if hasattr(self.state_manager.current_map, 'combat_animation') and \
                    self.state_manager.current_map.combat_animation.is_playing:
                return

            # Add a pause between actions
            current_time = time.time()
            if not hasattr(self, 'last_action_time'):
                self.last_action_time = 0

            # Wait for MOVEMENT_DELAY seconds between actions
            if current_time - self.last_action_time < MOVEMENT_DELAY:
                return

            # Process the monster's turn
            action_result = self.state_manager.current_map.handle_monster_turn(monster)
            self.last_action_time = current_time

            # Only remove monster from queue if it can't take any more actions
            if not action_result:
                self.monsters_queue.pop(0)
        else:
            self.monsters_queue.pop(0)

    def handle_input(self, event):
        if self.state_manager.current_state == GameState.PLAYING:
            self.handle_playing_input(event)
            if self.state_manager.message_log:
                self.state_manager.message_log.handle_event(event)
        elif self.state_manager.current_state == GameState.MAIN_MENU:
            self.handle_menu_input(event)
        elif self.state_manager.current_state == GameState.INVENTORY:
            self.handle_inv_ui(event)
        elif self.state_manager.current_state == GameState.DIALOG:
            self.dialog_ui.handle_input(event)
        elif self.state_manager.current_state == GameState.DEAD:
            self.handle_death_input(event)
        elif self.state_manager.current_state == GameState.DEMO_COMPLETE:
            self.handle_demo_complete_input(event)

    def handle_inv_ui(self, event):
        if event.type == pg.KEYDOWN and (event.key == pg.K_ESCAPE or event.key == pg.K_i):
            self.state_manager.change_state(GameState.PLAYING)
            if self.inventory_ui:
                self.inventory_ui.destroy_ui()
                self.inventory_ui = None
            return
        if self.inventory_ui:
            self.inventory_ui.handle_input(event)

    def toggle_fullscreen(self):
        is_fullscreen = bool(self.screen.get_flags() & pg.FULLSCREEN)
        if is_fullscreen:
            # Switch to windowed mode
            self.screen = pg.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        else:
            # Switch to fullscreen
            self.screen = pg.display.set_mode((0, 0), pg.FULLSCREEN | pg.SCALED)

    def handle_playing_input(self, event):
        if hasattr(self, 'monsters_queue') and self.monsters_queue:
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                self.state_manager.change_state(GameState.MAIN_MENU)  # Only allow ESC key during monster turns
            return
        if event.type in (pg.MOUSEBUTTONDOWN, pg.MOUSEBUTTONUP, pg.MOUSEMOTION):
            self.mouse_ui.handle_mouse_input(event)
            return
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_F11:
                self.toggle_fullscreen()

            elif event.key == pg.K_F8:
                self.load_loading_image()
                SaveSystem.load_game(self.state_manager)
                self.state_manager.add_message("Game Loaded!", WHITE)
            elif event.key == pg.K_F5 and self.state_manager.player:
                SaveSystem.save_game(self.state_manager)
                self.state_manager.add_message("Game saved!", WHITE)
            player_tile_x = self.state_manager.player.x // self.state_manager.current_map.tile_size
            player_tile_y = self.state_manager.player.y // self.state_manager.current_map.tile_size
            if self.state_manager.current_state == GameState.PLAYING:
                if event.key == pg.K_SPACE:  # End turn
                    self.handle_monster_turns()
                    self.state_manager.player.reset_turn()
                    return
                elif event.key == pg.K_BACKQUOTE:  # ` key record
                    self.state_manager.stt.handle_record_button()

                elif event.key == pg.K_1:
                    self.state_manager.player.use_skill(0)  # heal_self
                elif event.key == pg.K_2:
                    self.state_manager.player.use_skill(1)  # shout
                elif event.key == pg.K_3:
                    self.state_manager.player.use_skill(2)  # multiply hit
                elif event.key == pg.K_4:
                    self.state_manager.player.use_skill(3)  # recharge ap

                # Movement
                elif event.key in (pg.K_w, pg.K_s, pg.K_a, pg.K_d):
                    direction, tile_x, tile_y = self.get_move_direction(event.key, player_tile_x, player_tile_y)
                    self.state_manager.player.set_facing(direction)
                    if not self.try_interact_with_npc(tile_x, tile_y):
                        self.state_manager.current_map.move_entity(self.state_manager.player, tile_x, tile_y)

                elif event.key == pg.K_j:  # View quest journal
                    quest_status = self.state_manager.quest_manager.format_all_quests_status()
                    print("\n" + quest_status + "\n")
                    print('money:', self.state_manager.player.gold)
                    print('inv:', self.state_manager.player.inventory)
                    print(self.state_manager.stats)

                # Interaction
                elif event.key == pg.K_e:  # Interact
                    # Check adjacent tiles for NPCs
                    facing_pos = self.state_manager.current_map.get_facing_tile_position(self.state_manager.player)
                    if facing_pos:
                        self.try_interact_with_npc(facing_pos[0], facing_pos[1])

                # Menu controls
                elif event.key == pg.K_i:  # Inventory
                    self.inventory_ui = InventoryUI(self.state_manager)
                    self.state_manager.change_state(GameState.INVENTORY)
            #elif self.state_manager.current_state == GameState.INVENTORY and event.key == pg.K_i:  # Inventory
            #    self.inventory_ui.destroy_ui()
            #    self.state_manager.change_state(GameState.PLAYING)
            if event.key == pg.K_ESCAPE:  # Menu
                self.state_manager.change_state(GameState.MAIN_MENU)

    def handle_menu_input(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_w or event.key == pg.K_UP:  # Move up
                self.state_manager.selected_menu_item = (self.state_manager.selected_menu_item - 1) % len(MENU_OPTIONS)
            elif event.key == pg.K_s or event.key == pg.K_DOWN:  # Move down
                self.state_manager.selected_menu_item = (self.state_manager.selected_menu_item + 1) % len(MENU_OPTIONS)
            elif event.key == pg.K_RETURN or event.key == pg.K_SPACE:  # Select option
                self.handle_menu_selection()
            elif event.key == pg.K_ESCAPE:  # Return to game if we were playing
                if self.state_manager.player:  # If game is in progress
                    self.state_manager.change_state(GameState.PLAYING)

    def handle_demo_complete_input(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:  # Return to main menu
                self.state_manager.change_state(GameState.MAIN_MENU)

    def handle_menu_selection(self):
        selected_option = MENU_OPTIONS[self.state_manager.selected_menu_item]
        if selected_option == "New Game":
            self.load_loading_image()
            self.dialog_ui.dialogue_processor.rag_manager.clear_knowledge_base()  # Clean db
            self.state_manager.start_new_game()
        elif selected_option == "Load Game":
            self.load_loading_image()
            SaveSystem.load_game(self.state_manager)
            pass
        elif selected_option == "Settings":
            # Implement settings menu
            pass
        elif selected_option == "Quit":
            pg.quit()
            sys.exit()

    def handle_death_input(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self.state_manager.change_state(GameState.MAIN_MENU)

    def draw_menu(self):
        # Draw menu background
        self.screen.fill(BLACK)

        # Draw title
        title_font = pg.font.Font(None, MENU_FONT_SIZE * 2)
        title_surface = title_font.render(GAME_TITLE, True, WHITE)
        title_rect = title_surface.get_rect(centerx=WINDOW_WIDTH // 2, y=50)
        self.screen.blit(title_surface, title_rect)

        # Draw menu options
        menu_font = pg.font.Font(None, MENU_FONT_SIZE)
        for i, option in enumerate(MENU_OPTIONS):
            color = RED if i == self.state_manager.selected_menu_item else WHITE
            text_surface = menu_font.render(option, True, color)
            text_rect = text_surface.get_rect(centerx=WINDOW_WIDTH // 2, y=MENU_START_Y + i * MENU_SPACING)
            self.screen.blit(text_surface, text_rect)

    def draw_player_ui(self):
        # Calculate UI dimensions based on screen size
        padding = int(WINDOW_HEIGHT * 0.01)
        bar_width = int(WINDOW_WIDTH * 0.15)
        bar_height = int(WINDOW_HEIGHT * 0.03)
        font_size = int(WINDOW_HEIGHT * 0.025)
        font = pg.font.Font(None, font_size)

        # Create a surface for the health bar with alpha channel
        health_surface = pg.Surface((bar_width, bar_height), pg.SRCALPHA)
        # Draw background with alpha (R, G, B, A) - A=128 means 50% transparent
        pg.draw.rect(health_surface, (255, 0, 0, 180), (0, 0, bar_width, bar_height))
        stats = self.state_manager.player.combat_stats
        # Draw current health with alpha
        health_percentage = stats.current_hp / stats.max_hp
        health_width = int(bar_width * health_percentage)
        pg.draw.rect(health_surface, (0, 255, 0, 180), (0, 0, health_width, bar_height))

        # Blit the health surface to the screen
        self.screen.blit(health_surface, (padding, padding))

        # Health text
        health_text = f"HP: {int(stats.current_hp)}/{stats.max_hp}"
        health_text_surface = font.render(health_text, True, WHITE)
        text_y_offset = (bar_height - health_text_surface.get_height()) // 2
        self.screen.blit(health_text_surface, (padding + 5, padding + text_y_offset))

        # Create a surface for the AP bar with alpha channel
        ap_y = padding * 2 + bar_height
        ap_surface = pg.Surface((bar_width, bar_height), pg.SRCALPHA)
        # Draw background with alpha
        pg.draw.rect(ap_surface, (50, 50, 150, 180), (0, 0, bar_width, bar_height))

        # Draw current AP with alpha
        ap_percentage = self.state_manager.player.get_ap_perc
        ap_width = int(bar_width * ap_percentage)
        pg.draw.rect(ap_surface, (100, 100, 255, 180), (0, 0, ap_width, bar_height))

        # Blit the AP surface to the screen
        self.screen.blit(ap_surface, (padding, ap_y))

        # AP text
        ap_text = f"AP: {self.state_manager.player.combat_stats.ap}/{self.state_manager.player.combat_stats.max_ap}"
        ap_text_surface = font.render(ap_text, True, WHITE)

        # Draw bottom skills panel
        self.draw_skills_panel()
        self.mouse_ui.draw(self.screen)
        self.screen.blit(ap_text_surface, (padding + 5, ap_y + text_y_offset))

    def draw_skills_panel(self):
        """Draw the skills panel with numbered slots at the bottom of the screen"""
        for i, skill in enumerate(self.state_manager.player.skills):
            skill.draw(self.screen, (WINDOW_WIDTH // 2 - 2 * SKILL_PANEL_SIZE + SKILL_PANEL_SIZE * i + i * SKILL_OFFSET,
                                     WINDOW_HEIGHT - 10 - SKILL_PANEL_SIZE))

    @staticmethod
    def get_move_direction(key, player_tile_x, player_tile_y):
        moves = {pg.K_w: {'direction': DIRECTION_UP, 'tile_x': player_tile_x, 'tile_y': player_tile_y - 1},
                 pg.K_s: {'direction': DIRECTION_DOWN, 'tile_x': player_tile_x, 'tile_y': player_tile_y + 1},
                 pg.K_a: {'direction': DIRECTION_LEFT, 'tile_x': player_tile_x - 1, 'tile_y': player_tile_y},
                 pg.K_d: {'direction': DIRECTION_RIGHT, 'tile_x': player_tile_x + 1, 'tile_y': player_tile_y}}
        return moves[key]['direction'], int(moves[key]['tile_x']), int(moves[key]['tile_y'])

    def try_interact_with_npc(self, tile_x, tile_y, click_talk=False):
        """Try to interact with an NPC at the given tile position"""
        if not (0 <= tile_x < self.state_manager.current_map.width and
                0 <= tile_y < self.state_manager.current_map.height):
            return False

        tile = self.state_manager.current_map.tiles[tile_y][tile_x]
        for entity in tile.entities:
            if isinstance(entity, NPC) or isinstance(entity, House) or (isinstance(entity, Monster) and click_talk):
                self.dialog_ui.current_npc = entity
                self.state_manager.current_npc = entity
                self.state_manager.change_state(GameState.DIALOG)
                if isinstance(entity, House):
                    self.dialog_ui.start_house_dialog(entity)
                else:
                    self.dialog_ui.start_dialog(entity)
                return True
        return False

    def draw_death_screen(self):
        self.screen.fill(BLACK + (100,))
        font = pg.font.Font(None, MENU_FONT_SIZE * 2)
        text_surface = font.render("You Died!", True, RED)
        text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
        self.screen.blit(text_surface, text_rect)

    def load_loading_image(self):
        n = random.randint(1, 8)
        loading_image = pg.image.load(LOADING_IMG[f'BG_{n}']).convert()
        image_aspect = loading_image.get_width() / loading_image.get_height()
        scaled_width = WINDOW_WIDTH
        scaled_height = int(WINDOW_WIDTH / image_aspect)

        # If height is too large, scale based on height instead
        if scaled_height > WINDOW_HEIGHT * 0.8:
            scaled_height = int(WINDOW_HEIGHT * 0.8)
            scaled_width = int(WINDOW_HEIGHT * image_aspect)

        self.loading_image = pg.transform.scale(loading_image, (scaled_width, scaled_height))
        self.loading_image_rect = self.loading_image.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))

    def draw_loading_screen(self):
        self.screen.fill(BLACK)
        self.screen.blit(self.loading_image, self.loading_image_rect)

        bar_width = int(WINDOW_WIDTH * 0.6)
        bar_height = int(WINDOW_HEIGHT * 0.05)
        x = (WINDOW_WIDTH - bar_width) // 2
        y = WINDOW_HEIGHT - bar_height - 50  # Position bar near bottom

        border_padding = int(bar_height * 0.1)
        border_rect = pg.Rect(x - border_padding, y - border_padding,
                              bar_width + (border_padding * 2), bar_height + (border_padding * 2))
        pg.draw.rect(self.screen, WHITE, border_rect, 2)

        progress_width = int((bar_width * int(self.state_manager.loading_progress)) / 100)
        progress_rect = pg.Rect(x, y, progress_width, bar_height)
        pg.draw.rect(self.screen, BLUE, progress_rect)

        font_size = int(WINDOW_HEIGHT * 0.05)
        font = pg.font.Font(None, font_size)
        text = font.render(f"Loading... {int(self.state_manager.loading_progress)}%", True, WHITE)
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, y - int(bar_height * 1.5)))
        self.screen.blit(text, text_rect)

        pg.display.flip()

    def draw_demo_complete_screen(self):
        self.screen.fill(BLACK)
        font = pg.font.Font(None, MENU_FONT_SIZE * 2)

        # Draw title
        title = font.render("Demo Complete!", True, GREEN)
        title_rect = title.get_rect(centerx=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT // 4)
        self.screen.blit(title, title_rect)

        # Draw stats
        stats_font = pg.font.Font(None, MENU_FONT_SIZE)
        stats = [
            f"Days Survived: {self.state_manager.current_day}",
            f"Quests Completed: {self.state_manager.stats['quests_completed']}",
            f"Monsters Slain: {self.state_manager.stats['monsters_killed']}",
            f"Gold Collected: {self.state_manager.stats['gold_collected']}",
            "",
            "Press ESC to return to menu"
        ]

        for i, stat in enumerate(stats):
            text = stats_font.render(stat, True, WHITE)
            rect = text.get_rect(centerx=WINDOW_WIDTH // 2,
                                 y=WINDOW_HEIGHT // 2 + i * MENU_SPACING)
            self.screen.blit(text, rect)


if __name__ == "__main__":
    game = Game()
    game.run()
