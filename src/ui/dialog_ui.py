import pygame
from constants import *
from utils.dialogue_processor import DialogueProcessor
import json


class DialogUI:
    def __init__(self, game_state_manager):
        self.font = pygame.font.Font(None, 32)
        self.input_text = ""
        self.last_input_text = ""
        self.max_input_length = 100
        self.game_state_manager = game_state_manager
        self.predefined_options = ["Got any quests?", "How are you?", "Bye"]
        self.selected_option = 0
        self.should_exit = False
        self.current_npc = None
        self.current_response = None
        self.dialogue_processor = DialogueProcessor()
        self.current_response = "Hello traveler! How can I help you today?"

        self.streaming_response = ""
        self.is_streaming = False
        self.stream = None

        self.SIDE_PANEL_WIDTH = 0.2  # 20% of screen width
        self.TOP_MARGIN = 0.03  # 3% of screen height
        self.PORTRAIT_SIZE = 0.15  # 15% of screen height
        self.TEXT_AREA_HEIGHT = 0.25  # 25% of screen height
        self.INPUT_HEIGHT = 0.06  # 6% of screen height
        self.PADDING = 20

    def start_dialog(self, npc):
        """Call this when starting dialog with an NPC"""
        self.current_npc = npc
        #npc.last_response if hasattr(npc, 'last_response') else
        self.input_text = ""
        self.should_exit = False
        self.streaming_response = ""
        self.is_streaming = False
        self.stream = None
        self.current_response = "Hello traveler! How can I help you today?"

    def clear_dialogue_state(self):
        """Reset all dialogue-related state"""
        self.current_response = None
        self.current_npc = None
        self.input_text = ""
        self.streaming_response = ""
        self.is_streaming = False
        self.stream = None
        self.should_exit = False

    def is_valid_char(self, char):
        # Allow only letters, numbers, spaces and basic punctuation
        return (char.isalnum() or
                char.isspace() or
                char in ".,!?'-")

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.input_text:
                    self.process_input(self.input_text, self.current_npc)
                    self.last_input_text = self.input_text
                    self.input_text = ""
                else:
                    selected_text = self.predefined_options[self.selected_option]
                    self.last_input_text = selected_text
                    self.process_input(selected_text, self.current_npc)

                    # If no input text, use selected predefined option
                    selected_text = self.predefined_options[self.selected_option]
                    if selected_text == "Bye":
                        self.should_exit = True
                    else:
                        print(f"Player chose: {selected_text}")
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(self.predefined_options)
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(self.predefined_options)
            elif event.key == pygame.K_SPACE and len(self.input_text) < self.max_input_length:
                self.input_text += " "
            # Only add character if it's valid and there's room
            elif (len(event.unicode) == 1 and
                  self.is_valid_char(event.unicode) and
                  len(self.input_text) < self.max_input_length):
                self.input_text += event.unicode

    def process_input(self, text, npc):
        if text.lower() in ["bye", "goodbye", "see you"]:
            self.should_exit = True
            self.clear_dialogue_state()  # Clear state when saying goodbye
            return

        try:
            response = self.dialogue_processor.process_dialogue(
                player_input=text,
                npc_name=npc.name,
                npc_mood=npc.mood,
                player_reputation=npc.reputation,
                active_quests=npc.active_quests,
                interaction_history=npc.interaction_history
            )

            # Get the complete response first (not as stream)
            if isinstance(response, dict):  # Error response
                self.current_response = response["text"]
                return

            # Initialize streaming
            self.stream = response
            self.streaming_response = ""
            self.is_streaming = True
            self.current_response = ""  # Clear current response while streaming

        except Exception as e:
            print(f"Unexpected error: {e}")  # Debug print
            self.current_response = "Sorry, I didn't quite understand that."

    def update(self):
        """Call this in your game loop"""
        if self.is_streaming and self.stream:
            try:
                # Try to get next chunk
                chunk = next(self.stream, None)

                if chunk is None:
                    # Stream finished
                    self.is_streaming = False
                    print("\nFinal JSON response:", self.streaming_response)  # Debug print for final JSON

                    # Find the actual response text between markers
                    start_marker = '"text": "'
                    end_marker = '"}'

                    start_idx = self.streaming_response.find(start_marker)
                    if start_idx != -1:
                        start_idx += len(start_marker)  # Move past the marker
                        end_idx = self.streaming_response.find('"}\n') or self.streaming_response.find(
                            '"}') or self.streaming_response.find('" }') or self.streaming_response.find(
                            '}```') or self.streaming_response.find('}')
                        if end_idx:
                            actual_response = self.streaming_response[start_idx:end_idx]
                            self.current_response = (actual_response.replace('```', '')
                                                                    .replace('}', '')
                                                                    .replace('"', '')
                                                                    .replace('``', ''))
                            self.current_npc.add_to_history(self.last_input_text, self.current_response)

                            # Check for inappropriate flag in the remaining JSON
                            if '"player_inappropriate_request": true' in self.streaming_response:
                                self.current_npc.reputation = max(0, self.current_npc.reputation - 10)
                    return

                # Accumulate streaming response
                if 'message' in chunk and 'content' in chunk['message']:
                    self.streaming_response += chunk['message']['content']

                    # Try to show partial response by finding the text between markers
                    start_marker = '"text": "'
                    start_idx = self.streaming_response.find(start_marker)
                    if start_idx != -1:
                        start_idx += len(start_marker)
                        self.current_response = self.streaming_response[start_idx:].replace('}', '').replace('"', '').replace('```', '')

            except Exception as e:
                print(f"Streaming error: {e}")
                self.is_streaming = False

    def draw(self, screen, npc):
        screen_width = screen.get_width()
        screen_height = screen.get_height()

        # Calculate dimensions
        side_panel_width = int(screen_width * self.SIDE_PANEL_WIDTH)
        portrait_size = int(screen_height * self.PORTRAIT_SIZE)
        top_margin = int(screen_height * self.TOP_MARGIN)

        # Calculate text area width and height
        text_area_width = screen_width - (side_panel_width * 2) - (self.PADDING * 4)
        required_height = self._calculate_text_height(self.current_response, text_area_width - self.PADDING * 2)
        text_area_height = max(int(screen_height * self.TEXT_AREA_HEIGHT), required_height)

        # Draw dialog background
        pygame.draw.rect(screen, (50, 50, 50), (0, 0, screen_width, screen_height))

        # NPC section (top-left)
        npc_panel = pygame.Rect(
            self.PADDING,
            top_margin,
            side_panel_width,
            portrait_size + self.PADDING * 2
        )
        pygame.draw.rect(screen, (70, 70, 70), npc_panel)

        # NPC name
        name_text = self.font.render(npc.name, True, WHITE)
        screen.blit(name_text, (npc_panel.x + self.PADDING, npc_panel.y + self.PADDING))

        # NPC face
        face_rect = npc.face_surface.get_rect(
            center=(npc_panel.centerx, npc_panel.centery + self.PADDING)
        )
        screen.blit(npc.face_surface, face_rect)

        # Dialog text area (top-middle)
        dialog_text_area = pygame.Rect(
            side_panel_width + self.PADDING * 2,
            top_margin,
            text_area_width,
            text_area_height
        )
        pygame.draw.rect(screen, (40, 40, 40), dialog_text_area)
        pygame.draw.rect(screen, WHITE, dialog_text_area, 2)

        # Draw the wrapped text
        self._draw_wrapped_text(screen, dialog_text_area)

        # Player section (bottom-left)
        player_panel = pygame.Rect(
            self.PADDING,
            screen_height - portrait_size - self.PADDING * 3 - int(screen_height * self.INPUT_HEIGHT),
            side_panel_width,
            portrait_size + self.PADDING * 2
        )
        pygame.draw.rect(screen, (70, 70, 70), player_panel)

        # Player name
        player_name_text = self.font.render("Ready_Player_1", True, WHITE)
        screen.blit(player_name_text, (player_panel.x + self.PADDING, player_panel.y + self.PADDING))

        # Player face
        player_face_rect = self.game_state_manager.player.face_surface.get_rect(
            center=(player_panel.centerx, player_panel.centery + self.PADDING)
        )
        screen.blit(self.game_state_manager.player.face_surface, player_face_rect)

        # Options panel (to the right of player)
        options_panel = pygame.Rect(
            side_panel_width + self.PADDING * 2,
            screen_height - portrait_size - self.PADDING * 3 - int(screen_height * self.INPUT_HEIGHT),
            side_panel_width * 3,  # Made wider for options
            portrait_size + self.PADDING * 2  # Made taller to match player panel
        )
        pygame.draw.rect(screen, (40, 40, 40), options_panel)
        pygame.draw.rect(screen, WHITE, options_panel, 2)

        # Draw options
        for i, option in enumerate(self.predefined_options):
            color = RED if i == self.selected_option else WHITE
            option_text = self.font.render(option, True, color)
            screen.blit(option_text, (
                options_panel.x + self.PADDING,
                options_panel.y + self.PADDING + i * 40
            ))

        # Input field (starting from right of player panel)
        input_rect = pygame.Rect(
            player_panel.right + self.PADDING,
            screen_height - self.PADDING - int(screen_height * self.INPUT_HEIGHT),
            screen_width - player_panel.right - self.PADDING * 2,
            int(screen_height * self.INPUT_HEIGHT)
        )
        pygame.draw.rect(screen, (40, 40, 40), input_rect)
        pygame.draw.rect(screen, WHITE, input_rect, 2)

        # Input text
        if self.input_text:
            text_surface = self.font.render(self.input_text, True, WHITE)
            screen.blit(text_surface, (
                input_rect.x + self.PADDING,
                input_rect.centery - text_surface.get_height() // 2
            ))

        # Cursor
        if pygame.time.get_ticks() % 1000 < 500:
            cursor_pos = self.font.size(self.input_text)[0] + input_rect.x + self.PADDING
            pygame.draw.line(screen, WHITE,
                             (cursor_pos, input_rect.centery - 10),
                             (cursor_pos, input_rect.centery + 10))

    def _calculate_text_height(self, text, max_width):
        """Calculate the height needed for the wrapped text"""
        if text is None:  # Safety check for None
            text = self.current_response or "Hello traveller!"  # Use current_response if available, empty string if not

        words = text.split()
        lines = []
        current_line = []

        for word in words:
            current_line.append(word)
            # Check if current line is too long
            if self.font.size(' '.join(current_line))[0] > max_width:
                current_line.pop()
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return len(lines) * 30 + self.PADDING * 2  # Height per line + padding

    def _draw_wrapped_text(self, screen, text_area):
        if not self.current_response:  # Safety check for None or empty string
            return
        words = self.current_response.split()
        lines = []
        current_line = []
        max_width = text_area.width - self.PADDING * 2

        for word in words:
            current_line.append(word)
            if self.font.size(' '.join(current_line))[0] > max_width:
                current_line.pop()
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        for i, line in enumerate(lines):
            text_surface = self.font.render(line, True, WHITE)
            screen.blit(text_surface, (
                text_area.x + self.PADDING,
                text_area.y + self.PADDING + i * 30
            ))