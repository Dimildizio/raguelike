class CombatStats:
    def __init__(self, base_hp, base_armor, base_damage, max_damage, ap):
        self.max_hp = base_hp
        self.current_hp = base_hp
        self.armor = base_armor
        self.damage = base_damage
        self.max_damage = max_damage
        self.max_ap = ap
        self.ap = ap

    def save_stats(self):
        return self.__dict__

    def load_stats(self, stats):
        self.max_hp = stats['max_hp']
        self.current_hp = stats['current_hp']
        self.armor = stats['armor']
        self.damage = stats['damage']
        self.max_damage = stats['max_damage']
        self.max_ap = stats['max_ap']
        self.ap = stats['ap']

    def spend_ap(self, ap_cost):
        if self.ap >= ap_cost:
            self.ap = max(0, self.ap - ap_cost)
            return True

    def reset_ap(self):
        self.ap = self.max_ap

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

    @property
    def get_ap_perc(self):
        return self.ap / self.max_ap

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
