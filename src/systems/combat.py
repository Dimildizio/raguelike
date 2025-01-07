

class CombatSystem:
    def __init__(self):
        self.turn_order = []
        self.current_turn = 0
        self.is_combat_active = False
        self.current_target = None
        
    def start_combat(self, player, enemies):
        self.turn_order = [player] + enemies
        self.current_turn = 0
        self.is_combat_active = True
        
    def next_turn(self):
        if not self.is_combat_active:
            return None
        self.current_turn = (self.current_turn + 1) % len(self.turn_order)
        return self.turn_order[self.current_turn]
        
    def process_attack(self, attacker, defender):
        damage = attacker.attack(defender)
        if defender.health <= 0:
            self.handle_defeat(defender)
        return damage
        
    def handle_defeat(self, entity):
        if entity in self.turn_order:
            self.turn_order.remove(entity)
            if len(self.turn_order) <= 1:  # Combat ends if only one participant remains
                self.end_combat()
                
    def end_combat(self):
        self.is_combat_active = False
        self.turn_order = []
        self.current_turn = 0