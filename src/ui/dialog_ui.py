import pygame
from constants import *
from utils.dialogue_processor import DialogueProcessor
import json


class DialogUI:
    def __init__(self):
        self.font = pygame.font.Font(None, 32)
        self.input_text = ""
        self.max_input_length = 100
        self.predefined_options = ["Got any quests?", "How are you?", "Bye"]
        self.selected_option = 0
        self.should_exit = False
        self.current_npc = None
        self.dialogue_processor = DialogueProcessor()
        self.current_response = "Hello traveler! How can I help you today?"

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
                    self.input_text = ""
                else:
                    selected_text = self.predefined_options[self.selected_option]
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
            return
        try:
            response = self.dialogue_processor.process_dialogue(
                player_input=text,
                npc_name=npc.name,
                player_reputation=npc.reputation,
                active_quests=npc.active_quests,
                interaction_history=npc.interaction_history
            )

            # Find the first and last curly braces
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]

                # Parse JSON response
                print(f"Parsing JSON: {json_str}")  # Debug print
                response_data = json.loads(json_str)
                self.current_response = response_data["text"]

                # Update NPC reputation if request was inappropriate
                if response_data["player_inappropriate_request"]:
                    npc.reputation = max(0, npc.reputation - 10)  # Decrease reputation

            else:
                print(f"Invalid JSON format: {response}")  # Debug print
                self.current_response = "Sorry, I didn't quite understand that."

        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")  # Debug print
            self.current_response = "Sorry, I didn't quite understand that."
        except Exception as e:
            print(f"Unexpected error: {e}")  # Debug print
            self.current_response = "Sorry, I didn't quite understand that."

    def draw(self, screen, npc):
        # Draw dialog background
        dialog_rect = pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(screen, (50, 50, 50), dialog_rect)

        # Draw NPC section (top-left)
        npc_section = pygame.Rect(20, 20, 200, 200)
        pygame.draw.rect(screen, (70, 70, 70), npc_section)

        # Draw NPC name
        name_text = self.font.render(npc.name, True, WHITE)
        screen.blit(name_text, (30, 30))

        # Draw NPC sprite
        npc_sprite_rect = npc.surface.get_rect(center=(120, 120))
        screen.blit(npc.surface, npc_sprite_rect)

        # Draw dialog text area (top-middle) with background
        dialog_text_area = pygame.Rect(250, 30, WINDOW_WIDTH - 300, 180)
        pygame.draw.rect(screen, (40, 40, 40), dialog_text_area)
        pygame.draw.rect(screen, WHITE, dialog_text_area, 2)  # Border

        # Word wrap the response text
        words = self.current_response.split()
        lines = []
        current_line = []
        line_spacing = 30
        max_width = dialog_text_area.width - 20  # Padding

        for word in words:
            current_line.append(word)
            # Check if current line is too long
            if self.font.size(' '.join(current_line))[0] > max_width:
                current_line.pop()  # Remove last word
                if current_line:  # Only add if there are words
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:  # Add the last line
            lines.append(' '.join(current_line))

        # Draw each line of the response
        for i, line in enumerate(lines):
            if i * line_spacing + 50 < dialog_text_area.height:  # Check if within bounds
                text_surface = self.font.render(line, True, WHITE)
                screen.blit(text_surface, (dialog_text_area.x + 10, dialog_text_area.y + 10 + i * line_spacing))

        # Draw predefined options (bottom-left)
        options_area = pygame.Rect(20, WINDOW_HEIGHT - 200, 200, 140)
        pygame.draw.rect(screen, (40, 40, 40), options_area)
        pygame.draw.rect(screen, WHITE, options_area, 2)

        for i, option in enumerate(self.predefined_options):
            color = RED if i == self.selected_option else WHITE
            option_text = self.font.render(option, True, color)
            screen.blit(option_text, (30, WINDOW_HEIGHT - 190 + i * 40))

        # Draw input field (bottom)
        input_rect = pygame.Rect(30, WINDOW_HEIGHT - 50, WINDOW_WIDTH - 60, 40)
        pygame.draw.rect(screen, (40, 40, 40), input_rect)
        pygame.draw.rect(screen, WHITE, input_rect, 2)

        # Draw input text
        if self.input_text:
            text_surface = self.font.render(self.input_text, True, WHITE)
            screen.blit(text_surface, (40, WINDOW_HEIGHT - 45))

        # Draw cursor
        if pygame.time.get_ticks() % 1000 < 500:  # Blinking cursor
            cursor_pos = self.font.size(self.input_text)[0] + 40
            pygame.draw.line(screen, WHITE,
                             (cursor_pos, WINDOW_HEIGHT - 45),
                             (cursor_pos, WINDOW_HEIGHT - 15))