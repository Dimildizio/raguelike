class CombatStats:
    def __init__(self, base_hp, base_armor, base_damage):
        self.max_hp = base_hp
        self.current_hp = base_hp
        self.armor = base_armor
        self.damage = base_damage

    def take_damage(self, amount):
        if self.current_hp <= 0:
            return 0
        actual_damage = max(1, amount - self.armor)  # Minimum 1 damage
        self.current_hp -= actual_damage
        if self.current_hp <= 0:
            self.current_hp = 0
        return actual_damage

    @property
    def is_alive(self):
        return self.current_hp > 0