class CombatStats:
    def __init__(self, base_hp, base_armor, base_damage):
        self.max_hp = base_hp
        self.current_hp = base_hp
        self.armor = base_armor
        self.damage = base_damage

    def get_healed(self, amount=0):
        amount = self.current_hp + amount if amount else self.max_hp
        self.current_hp = min(self.max_hp, amount)

    def take_damage(self, amount, armor=True):
        if self.current_hp <= 0:
            return 0
        actual_damage = int(max(1, amount - (self.armor if armor else 0)))  # Minimum 1 damage
        self.current_hp -= actual_damage
        if self.current_hp <= 0:
            self.current_hp = 0
        return actual_damage


    @property
    def get_hp_perc(self):
        return self.current_hp / self.max_hp if self.max_hp else 0


    @property
    def is_alive(self):
        return self.current_hp > 0

    def get_status(self):
        hperc = self.current_hp / self.max_hp
        if hperc > .99:
            return 'unharmed'
        elif hperc > .75:
            return 'light wounds'
        elif hperc > .50:
            return 'moderate wounds'
        elif hperc > .25:
            return 'heavy wounds'
        else:
            return 'mortal wounds'
