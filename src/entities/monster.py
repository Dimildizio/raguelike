import math
from .entity import Entity
from constants import *
from systems.combat_stats import CombatStats
import random


class Monster(Entity):
    def __init__(self, x, y, sprite_path="MONSTER", name='Monster'):
        super().__init__(x, y, SPRITES[sprite_path], SPRITES["OUTLINE_RED"], ap=60)
        self.name = name
        # Choose a personality type
        self.personality = random.choice(MONSTER_PERSONALITY_TYPES)
        dmg = MONSTER_BASE_DAMAGE
        armor = MONSTER_BASE_ARMOR
        hp = MONSTER_BASE_HP

        # Set personality-based traits
        if self.personality == "aggressive":
            self.aggression = random.uniform(1.0, 1.6)  # Very likely to attack
            self.bravery = random.uniform(0.75, 1.0)  # Fights even when hurt
            dmg *= 1.2
        elif self.personality == "cautious":
            self.aggression = random.uniform(0.8, 1.4)  # Less likely to attack
            self.bravery = random.uniform(0.6, 0.8)  # Moderate flee threshold
            armor *= 1.2
        elif self.personality == "cowardly":
            self.aggression = random.uniform(0.7, 1.3)  # Rarely attacks
            self.bravery = random.uniform(0.4, 0.6)  # Flees easily
        elif self.personality == "territorial":
            self.aggression = random.uniform(1.2, 1.5)  # Very aggressive when close
            self.bravery = random.uniform(0.7, 0.9)  # Stands ground well
            hp *= 1.2

        self.combat_stats = CombatStats(base_hp=hp, base_armor=armor, base_damage=dmg)

    def attack(self, target):
        # Basic attack with random variation
        base_damage = self.combat_stats.damage * random.uniform(0.8, 1.2)

        # Personality affects critical hit chance
        crit_chance = CRITICAL_HIT_CHANCE
        if self.personality == "aggressive":
            crit_chance *= 1.5  # More likely to crit

        if random.random() < crit_chance:
            base_damage *= 2

        actual_damage = max(0, base_damage - target.combat_stats.armor)
        target.health -= actual_damage
        return actual_damage

    def should_flee(self):
        # More brave monsters will fight at lower health
        return (self.health / self.max_health) < self.bravery

    def wants_to_attack(self, distance):
        # More aggressive monsters will attack from further away
        return distance <= (MONSTER_AGGRO_RANGE * self.aggression)

    def update(self):
        self.update_breathing()
