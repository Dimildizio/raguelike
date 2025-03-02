import uuid
import pygame as pg

from constants import *
from utils.sprite_loader import SpriteLoader


class Item:
    def __init__(self, name, sprite_path, item_type="misc", description="", price=0,
                 weight=1, equippable=False, slot=None, stats=None, game_state=None, inv_sprite=None):
        self.name = name
        self.uuid = str(uuid.uuid4())
        self.sprite_path = sprite_path
        self.inv_path = inv_sprite
        self.item_type = item_type  # weapon, armor, consumable, misc
        self.description = description
        self.price = price  # gold value
        self.weight = weight
        self.equippable = equippable
        self.slot = slot  # head, body, weapon, etc.
        self.stats = stats or {}  # damage, armor, healing, etc.
        self.game_state = game_state

        # Load sprite
        self.sprite_loader = SpriteLoader(
            ORIGINAL_SPRITE_SIZE,
            PREPROCESSED_TILE_SIZE,
            DISPLAY_TILE_SIZE
        )
        self.surface, self.pil_sprite = self.sprite_loader.load_sprite(sprite_path)
        self.surface = pg.transform.scale(self.surface, (DISPLAY_TILE_SIZE, DISPLAY_TILE_SIZE))

        self.inv_surface, self.inv_pil_sprite = self.sprite_loader.load_sprite(inv_sprite)

    def __repr__(self):
        return f"{self.name}, {self.description}, id: {self.uuid}"

    def use(self, character):
        """Use the item (for consumables)"""
        if self.item_type == "consumable":
            if "heal" in self.stats:
                character.combat_stats.get_healed(self.stats["heal"])
                character.get_floating_nums(f"+{int(self.stats['heal'])}", color=GREEN)
                self.game_state.add_message(f"Used {self.name} and healed for {self.stats['heal']}", GREEN)
                return True
        return False

    def get_stat_text(self):
        """Return formatted text of item stats"""
        lines = []
        if "damage" in self.stats:
            lines.append(f"Damage: {self.stats['damage']}")
        if "armor" in self.stats:
            lines.append(f"Armor: {self.stats['armor']}")
        if "heal" in self.stats:
            lines.append(f"Healing: {self.stats['heal']}")

        lines.append(f"Value: {self.price} gold")
        lines.append(f"Weight: {self.weight}")

        return "\n".join(lines)

    def draw(self, screen, x, y):
        """Draw the item at the specified position"""
        screen.blit(self.surface, (x, y))

    def draw_on_ground(self, screen, offset_x=0, offset_y=0):
        """Draw the item on the ground at its tile position"""
        screen.blit(self.surface, (offset_x, offset_y))

    def save_item(self):
        """Serialize item data for saving"""
        return {
            "name": self.name,
            "uuid": self.uuid,
            "sprite_path": self.sprite_path,
            'inv_path': self.inv_path,
            "item_type": self.item_type,
            "description": self.description,
            "price": self.price,
            "weight": self.weight,
            "equippable": self.equippable,
            "slot": self.slot,
            "stats": self.stats
        }

    @classmethod
    def load_item(cls, data, game_state=None):
        """Create an item from saved data"""
        return cls(
            name=data["name"],
            uuid=data['uuid'],
            sprite_path=data["sprite_path"],
            inv_path=data["inv_path"],
            item_type=data["item_type"],
            description=data["description"],
            price=data["price"],
            weight=data["weight"],
            equippable=data["equippable"],
            slot=data["slot"],
            stats=data["stats"],
            game_state=game_state
        )