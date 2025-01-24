import pygame as pg
from constants import *


class MessageLog:
    def __init__(self):
        # Calculate dimensions
        screen = pg.display.get_surface()
        screen_width, screen_height = screen.get_width(), screen.get_height()
        self.width = int(screen_width * 0.3)  # 1/5 of screen width
        self.height = int(screen_height * 0.2)  # Adjust as needed
        self.x = screen_width - self.width - 10  # 10px padding from right
        self.y = screen_height - self.height - 10  # 10px padding from bottom

        # Message storage
        self.messages = []
        self.max_messages = 100

        # Font
        self.font_size = max(14, int(screen_height * 0.03))
        self.font = pg.font.Font(None, self.font_size)
        self.line_height = int(self.font_size * 1.2)

        self.scroll_offset = 0
        self.max_scroll = 0
        self.scroll_speed = int(self.line_height * 0.8)
        self.is_mouse_over = False
        # Background
        self.background = pg.Surface((self.width, self.height), pg.SRCALPHA)
        self.background.fill((0, 0, 0, 180))  # Semi-transparent black


    def _wrap_text(self, text):
        """Wrap text to fit within the log width"""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            # Test if adding this word exceeds the width
            test_line = ' '.join(current_line + [word])
            if self.font.size(test_line)[0] <= self.width - 20:  # 20px padding
                current_line.append(word)
            else:
                if current_line:  # Add the current line if it's not empty
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:  # Add the last line
            lines.append(' '.join(current_line))

        return lines

    def _is_mouse_over(self, pos):
        """Check if mouse is over the log area"""
        return (self.x <= pos[0] <= self.x + self.width and
                self.y <= pos[1] <= self.y + self.height)

    def handle_event(self, event):
        """Handle mouse events for scrolling"""
        if event.type == pg.MOUSEMOTION:
            mouse_pos = pg.mouse.get_pos()
            self.is_mouse_over = self._is_mouse_over(mouse_pos)

        elif event.type == pg.MOUSEWHEEL and self.is_mouse_over:
            # Calculate total content height
            total_height = len(self.messages) * self.line_height
            self.max_scroll = max(0, total_height - self.height)

            # Update scroll offset
            self.scroll_offset -= event.y * self.scroll_speed

            # Clamp scroll offset between 0 and max_scroll
            self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))

    def add_message(self, message, color=YELLOW):
        """Add a new message to the log"""
        wrapped_lines = self._wrap_text(message)

        for line in wrapped_lines:
            self.messages.append((line, color))
            if len(self.messages) > self.max_messages:
                self.messages.pop(0)

        # Update max scroll value and scroll to bottom
        total_height = len(self.messages) * self.line_height
        self.max_scroll = max(0, total_height - self.height)
        self.scroll_offset = self.max_scroll  # Scroll to bottom for new messages

    def draw(self, screen):
        """Draw the message log"""
        # Draw background
        screen.blit(self.background, (self.x, self.y))

        # Create a surface for the text
        text_surface = pg.Surface((self.width - 10, self.height), pg.SRCALPHA)

        # Calculate visible range
        visible_start = self.scroll_offset // self.line_height
        visible_end = visible_start + (self.height // self.line_height) + 1
        visible_messages = self.messages[max(0, visible_start):visible_end]

        # Draw messages
        for i, (message, color) in enumerate(visible_messages):
            text = self.font.render(message, True, color)
            y_pos = i * self.line_height - (self.scroll_offset % self.line_height)

            # Only draw if within visible area
            if 0 <= y_pos <= self.height:
                text_surface.blit(text, (5, y_pos))

        # Draw the text surface
        screen.blit(text_surface, (self.x + 5, self.y))

        # Draw scroll indicator if needed
        if self.max_scroll > 0:
            scroll_height = max(20, int(self.height * (self.height / (len(self.messages) * self.line_height))))
            scroll_ratio = self.scroll_offset / self.max_scroll
            scroll_pos = self.y + int((self.height - scroll_height) * scroll_ratio)
            pg.draw.rect(screen, (200, 200, 200, 128),
                         (self.x + self.width - 5, scroll_pos, 3, scroll_height))