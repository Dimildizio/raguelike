import pygame
from constants import *


class DialogUI:
    def __init__(self):
        self.font = pygame.font.Font(None, 32)
        self.input_text = ""
        self.max_input_length = 100
        self.predefined_options = ["Got any quests?", "How are you?", "Bye"]
        self.selected_option = 0
        self.should_exit = False  # Add flag to track if dialog should end

    def is_valid_char(self, char):
        # Allow only letters, numbers, spaces and basic punctuation
        return (char.isalnum() or
                char.isspace() or
                char in ".,!?'-")

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.input_text:
                    # Check if player typed "bye" (case-insensitive)
                    if self.input_text.lower() in ["bye", 'exit', 'goodbye', 'see you']:
                        self.should_exit = True
                    else:
                        print(f"Player said: {self.input_text}")
                    self.input_text = ""
                else:
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

        # Draw dialog text area (top-middle)
        dialog_text = "Hello traveler! How can I help you today?"  # Example text
        text_surface = self.font.render(dialog_text, True, WHITE)
        screen.blit(text_surface, (250, 50))

        # Draw predefined options (bottom-left)
        for i, option in enumerate(self.predefined_options):
            color = RED if i == self.selected_option else WHITE
            option_text = self.font.render(option, True, color)
            screen.blit(option_text, (30, WINDOW_HEIGHT - 200 + i * 40))

        # Draw input field (bottom)
        input_rect = pygame.Rect(30, WINDOW_HEIGHT - 50, WINDOW_WIDTH - 60, 40)
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