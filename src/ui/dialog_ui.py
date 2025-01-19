import pygame
from constants import *
from utils.dialogue_processor import DialogueProcessor
from entities.monster import Monster
from entities.entity import House
import json


class DialogUI:
    def __init__(self, game_state_manager):
        self.font = pygame.font.Font(None, 32)
        self.input_text = ""
        self.last_input_text = ""
        self.max_input_length = 100
        self.game_state_manager = game_state_manager
        #self.predefined_options = ["Got any quests?", "How are you?", "Bye"]
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

    @property
    def predefined_options(self):
        if isinstance(self.current_npc, Monster):
            return ['Wut you want?', 'Bye']
        elif isinstance(self.current_npc, House):
            return ['Rent a bed', 'Leave']
        else:
            return ["Got any quests?", "How are you?", "Bye"]

    def start_dialog(self, npc):
        """Call this when starting dialog with an NPC"""
        if self.current_npc == npc and self.is_streaming:
            return
        self.current_npc = npc
        self.input_text = ""
        self.should_exit = False
        self.streaming_response = ""
        self.is_streaming = False
        self.stream = None
        self.current_response = "Hello traveler! How can I help you today?" if not isinstance(
                                npc, Monster) else "Hey you! We need talk!"
        self.selected_option = 0  # Reset selection


    def clear_dialogue_state(self):
        """Reset all dialogue-related state"""
        self.current_response = None
        self.current_npc = None
        self.input_text = ""
        self.streaming_response = ""
        self.is_streaming = False
        self.stream = None
        self.should_exit = False
        if self.game_state_manager:
            self.game_state_manager.current_npc = None

    @staticmethod
    def is_valid_char(char):
        # Allow only letters, numbers, spaces and basic punctuation
        return (char.isalnum() or
                char.isspace() or
                char in ".,!?'-")

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.input_text:
                    if self.input_text.lower() in ["bye", "goodbye", "see you", "leave"]:
                        self.should_exit = True
                    else:
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
        """Process player input and get NPC response"""
        if text.lower() in ["bye", "goodbye", "see you", 'leave']:
            self.should_exit = True
            #self.clear_dialogue_state()
            return

        try:
            if isinstance(npc, House):
                if text.lower() in ['sleep', 'rent a bed']:
                    self.game_state_manager.pass_night(npc.fee)
                    return
            elif isinstance(npc, Monster):
                self.stream = self.dialogue_processor.process_monster_dialogue(text, npc, self.game_state_manager)
            else:

                # Get the response stream
                self.stream = self.dialogue_processor.process_dialogue(
                    player_input=text,
                    npc=npc,
                    player_reputation=npc.reputation,
                    game_state=self.game_state_manager,
                    interaction_history=npc.interaction_history
                )

            # Initialize streaming
            self.streaming_response = ""
            self.is_streaming = True
            self.current_response = ""  # Clear current response while streaming

        except Exception as e:
            print(f"Error in process_input: {e}")
            self.current_response = "Sorry, I didn't quite understand that."


    def update(self):
        """Update dialogue state"""
        if isinstance(self.current_npc, House):
            self.current_response = self.current_npc.description
        if self.is_streaming and self.stream:
            try:
                # Process next chunk of the stream
                chunk = next(self.dialogue_processor.handle_stream(self.stream))
                if chunk:  # Streaming chunk
                    self.streaming_response += chunk

                    # Extract text between markers, similar to update1
                    start_marker = '"text": "'
                    if start_marker in self.streaming_response:
                        start_idx = self.streaming_response.find(start_marker) + len(start_marker)
                        # Show everything after the start marker, cleaning up JSON artifacts
                        partial_response = self.streaming_response[start_idx:]
                        self.current_response = (partial_response.replace('```', '')
                                                 .replace('}', '')
                                                 .replace('"', '')
                                                 .replace('``', ''))
            except StopIteration:
                # Stream is complete
                try:
                    # Find the JSON part between ```json and ```
                    json_parts = self.streaming_response.split('```json')
                    if len(json_parts) > 1:
                        json_text = json_parts[1].split('```')[0]
                        final_response = json.loads(json_text)
                        print(final_response)

                        # Update NPC's last response
                        if self.current_npc:
                            self.current_npc.last_response = final_response.get('text', '')

                            # Handle quest-related actions
                            if self.current_npc.monster_type == 'npc':
                                if final_response.get('further_action') == 'give_quest':
                                    quest_id = final_response.get('quest_id')
                                    print('give quest', quest_id)
                                    if quest_id:
                                        if self.game_state_manager.accept_quest(quest_id):
                                            self.current_response += "\nQuest accepted!"
                                        else:
                                            self.current_response += "\nCouldn't accept the quest."

                                # Handle reward negotiation
                                elif final_response.get('further_action') == 'negotiate_reward':
                                    quest_id = final_response.get('quest_id')
                                    negotiated_amount = final_response.get('negotiated_amount')
                                    if quest_id and negotiated_amount:
                                        if self.current_npc.negotiate_reward(quest_id, negotiated_amount):
                                            self.current_response += f"\nAlright, I agree to pay you {negotiated_amount} gold upon completion."
                                        else:
                                            self.current_response += "\nI'm sorry, but I can't afford to pay that much."

                                # Handle quest completion and reward payment
                                elif final_response.get('further_action') == 'reward':
                                    quest_id = final_response.get('quest_id')
                                    if quest_id:
                                        rewards = self.game_state_manager.complete_quest(quest_id)
                                        if rewards:
                                            total_received = 0
                                            reward_texts = []
                                            for reward in rewards:
                                                if reward['type'] == 'gold':
                                                    amount = reward['amount']
                                                    # Add the gold to player's inventory
                                                    received = self.game_state_manager.player.add_gold(amount)
                                                    total_received += received
                                                    reward_texts.append(f"{received} gold")

                                            if total_received > 0:
                                                self.current_response += f"\nReceived: {', '.join(reward_texts)}"
                                                if total_received < sum(
                                                        r['amount'] for r in rewards if r['type'] == 'gold'):
                                                    self.current_response += "\n(That's all I could afford right now)"
                                            else:
                                                self.current_response += "\nI'm sorry, but I don't have any money to pay you right now."
                                        else:
                                            self.current_response += "\nI'm sorry, but I can't pay you right now."
                            else:
                                print('FINAL', final_response)
                                if int(final_response.get('give_money', 0)) > 0:
                                    give_money = final_response['give_money']
                                    if give_money > self.current_npc.money:
                                        self.current_response += (f"\nHere ya {give_money}...Ehh Me dont 'ave that many "
                                                                  f"gold, me give ya {self.current_npc.money}! "
                                                                  f"(Paid {self.current_npc.money} gold)")
                                        give_money = self.current_npc.money
                                        self.current_npc.set_hostility(False)

                                    else:
                                        self.current_response += f"(Paid {give_money} gold)"
                                    received = self.game_state_manager.player.add_gold(give_money)
                                if final_response.get('player_friendly'):
                                    self.current_npc.set_hostility(False)

                            # Update interaction history
                            self.current_npc.add_to_history(self.last_input_text, final_response.get('text', ''))

                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
                except Exception as e:
                    print(f"Error processing dialogue: {e}")

                self.is_streaming = False
                self.stream = None

    def draw(self, screen, npc):
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        if isinstance(npc, House):
            self.draw_house_dialogue(screen)
        else:

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

    def start_house_dialog(self, house):
        """Initialize dialogue UI for house interaction"""
        self.current_npc = house
        self.current_response = house.description
        self.selected_option = 0
        self.should_exit = False

    def draw_house_dialogue(self, screen):
        """Draw house dialogue in the same style as NPC dialogue"""
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

        # House section (top-left)
        house_panel = pygame.Rect(
            self.PADDING,
            top_margin,
            side_panel_width,
            portrait_size + self.PADDING * 2
        )
        pygame.draw.rect(screen, (70, 70, 70), house_panel)

        # House name
        name_text = self.font.render(self.current_npc.name, True, WHITE)
        screen.blit(name_text, (house_panel.x + self.PADDING, house_panel.y + self.PADDING))

        # House face/image
        if self.current_npc.face_surface:
            face_rect = self.current_npc.face_surface.get_rect(
                center=(house_panel.centerx, house_panel.centery + self.PADDING)
            )
            screen.blit(self.current_npc.face_surface, face_rect)

        # Dialog text area (description)
        dialog_text_area = pygame.Rect(
            side_panel_width + self.PADDING * 2,
            top_margin,
            text_area_width,
            text_area_height
        )
        pygame.draw.rect(screen, (40, 40, 40), dialog_text_area)
        pygame.draw.rect(screen, WHITE, dialog_text_area, 2)

        # Draw the wrapped text (description)
        self._draw_wrapped_text(screen, dialog_text_area)

        # Options panel at bottom
        options_panel = pygame.Rect(
            side_panel_width + self.PADDING * 2,
            screen_height - portrait_size - self.PADDING * 3,
            side_panel_width * 3,
            portrait_size + self.PADDING * 2
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