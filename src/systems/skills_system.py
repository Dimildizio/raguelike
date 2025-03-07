import pygame as pg
from constants import *


class Skill:
    def __init__(self, owner, name='', description='', ap_cost=5, value=10, cooldown=2, dist=1,
                 image_path=SPRITES['SKILL_1'], loading=False):
        self.owner = owner
        self.name = name
        self.dist = dist
        self.description = description
        self.ap_cost = ap_cost
        self.value = value
        self.cooldown = 0
        self.max_cooldown = cooldown

        self.skills_list = {'heal': self.skill_damage, 'damage': self.skill_damage, 'multiply': self.multiply,
                            'shout': self.shout, 'second_breath': self.second_breath}
        self.skill = self.skills_list.get(self.name.lower(), lambda x: None)

        self.image_path = image_path
        if not loading:
            self.skill_surface = pg.image.load(self.image_path).convert_alpha()
            self.skill_surface = pg.transform.scale(self.skill_surface, (SKILL_PANEL_SIZE, SKILL_PANEL_SIZE))

    def skill_activated(self, target=None):
        if self.cooldown <= 0:
            if not self.owner.combat_stats.spend_ap(self.ap_cost):
                self.owner.get_floating_nums(f"Not enough AP!", color=BLUE)
                return
            target = self.owner if target is None else target
            try:
                if self.skill(target):
                    self.cooldown = self.max_cooldown
                    return True

            except Exception as e:
                print(f"Skill error (handled): {e}")
                self.cooldown = self.max_cooldown
                return True
        return False

    def update(self):
        pass

    def update_cooldown(self):
        self.cooldown = max(0, self.cooldown-1)

    def reset_cooldown(self):
        self.cooldown = 0

    def draw(self, screen, pos):
        x, y = pos
        screen.blit(self.skill_surface, (x, y))

        # If on cooldown, draw red overlay with alpha
        if self.cooldown > 0:
            overlay = pg.Surface((64, 64), pg.SRCALPHA)
            overlay.fill((255, 0, 0, 64))  # Red with 50% transparency
            screen.blit(overlay, (x, y))

            # Draw cooldown number
            font = pg.font.Font(None, 36)
            text = font.render(str(self.cooldown), True, (255, 255, 255))
            text_rect = text.get_rect(center=(x + 32, y + 32))
            screen.blit(text, text_rect)

    def save_skill(self):
        idict = {}
        for key, value in self.__dict__.items():
            if key not in ('skill_surface', 'owner', 'skill', 'skills_list'):
                idict[key] = value
        return idict

    def load_skill(self, data):
        for key, value in data.items():
            setattr(self, key, value)
        self.skill = self.skills_list.get(self.name.lower(), lambda x: None)
        self.skill_surface = pg.image.load(self.image_path).convert_alpha()
        self.skill_surface = pg.transform.scale(self.skill_surface, (64, 64))
        return self

    def skill_damage(self, target):
        sign = '-' if self.value > 0 else '+'
        target.combat_stats.take_damage(self.value, armor=False) if self.value > 0 else (
                                                                    target.combat_stats.get_healed(-self.value))
        target.get_floating_nums(f"{sign}{int(self.value)}", color=GREEN)
        self.owner.game_state.add_message(f"{self.owner.name} does {target.name} {sign}{abs(self.value)} to hp", WHITE)
        return True

    def multiply(self, target):
        damage = self.value * self.owner.combat_stats.max_damage
        target.take_damage(damage)
        self.owner.game_state.add_message(f"{self.owner.name} casts {self.name} on {target.name} for {damage} dmg", RED)
        return True

    def shout(self, target):
        shouted = self.owner.game_state.stt.handle_record_button('intimidate')  # STT record logic handled in game_state
        if not shouted:
            self.owner.get_floating_nums('I... I.. will hurt you! Yes!', color=YELLOW)
            self.owner.shout_intimidate(1)  # Minimal value
        return True

    def second_breath(self, target):
        target.take_damage(self.value, armor=False)
        target.combat_stats.ap = target.combat_stats.max_ap
        target.get_floating_nums(f"Takes a deep breath", color=BLUE)
        self.owner.game_state.add_message(f"{self.owner.name} gets a second breath losing {self.value} hp", WHITE)
        return True

