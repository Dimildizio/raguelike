import pygame
from constants import DIALOG_FONT_SIZE

class DialogSystem:
    def __init__(self):
        self.current_dialog = None
        self.font = pygame.font.Font(None, DIALOG_FONT_SIZE)
        
    def start_dialog(self, npc):
        self.current_dialog = npc.get_next_dialog()
        
    def draw(self, screen):
        if self.current_dialog:
            pass