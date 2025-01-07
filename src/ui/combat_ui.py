import pygame

class CombatUI:
    def __init__(self):
        self.font = pygame.font.Font(None, 36)
        
    def draw(self, screen, combat_system):
        # Draw health bars
        for entity in combat_system.turn_order:
            self.draw_health_bar(screen, entity)
            
        # Draw turn indicator
        current = combat_system.turn_order[combat_system.current_turn]
        text = f"Current Turn: {current.name}"
        