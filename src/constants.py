import os

# Window settings
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
FPS = 60
GAME_TITLE = "RPG Game"

# Map settings
#TILE_SIZE = 32

# Sprite settings
ORIGINAL_SPRITE_SIZE = 512
PREPROCESSED_TILE_SIZE = 256
DISPLAY_TILE_SIZE = 128

# Map settings
MAP_WIDTH = 10  # in tiles
MAP_HEIGHT = 10  # in tiles

# Asset paths
ASSET_DIR = "assets"
SPRITES = {
    "PLAYER": os.path.join(ASSET_DIR, "player.png"),
    "FLOOR": os.path.join(ASSET_DIR, "floor_tile.png"),
    "NPC": os.path.join(ASSET_DIR, "npc.png"),
    "MONSTER": os.path.join(ASSET_DIR, "monster.png"),
    "OUTLINE_GREEN": os.path.join(ASSET_DIR, "outline_green.png"),
    "OUTLINE_YELLOW": os.path.join(ASSET_DIR, "outline_yellow.png"),
    "OUTLINE_RED": os.path.join(ASSET_DIR, "outline_red.png"),
}


COMBAT_TURN_TIMEOUT = 30  # seconds
COMBAT_MIN_DAMAGE_MULT = 0.8
COMBAT_MAX_DAMAGE_MULT = 1.2
COMBAT_CRIT_MULTIPLIER = 2.0

# UI settings
COMBAT_UI_HEIGHT = 150
COMBAT_UI_PADDING = 10
HEALTH_BAR_HEIGHT = 20
HEALTH_BAR_WIDTH = 200

# Entity settings
PLAYER_START_HP = 100
PLAYER_START_ARMOR = 10
PLAYER_BASE_DAMAGE = 10
BREATHING_SPEED = 0.03
BREATHING_AMPLITUDE = 3  # degrees

# Colors (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Combat settings
TURN_TIMEOUT = 30  # seconds
CRITICAL_HIT_CHANCE = 0.1
DODGE_CHANCE = 0.05

# Add these to your constants.py file

# NPC settings
NPC_BASE_HP = 50
NPC_BASE_ARMOR = 5

# Monster settings
MONSTER_BASE_HP = 50
MONSTER_BASE_ARMOR = 5
MONSTER_BASE_DAMAGE = 8
MONSTER_AGGRO_RANGE = 5  # in tiles

# Dialog settings
DIALOG_FONT_SIZE = 16
DIALOG_PADDING = 10
DIALOG_BG_COLOR = (50, 50, 50, 200)  # RGB + Alpha

# Inventory settings
MAX_INVENTORY_SLOTS = 20
MAX_STACK_SIZE = 99


# Menu settings
MENU_OPTIONS = ["New Game", "Load Game", "Settings", "Quit"]
MENU_FONT_SIZE = 36
MENU_SPACING = 50  # Pixels between menu items
MENU_START_Y = 200  # Starting Y position for menu items

# Direction constants
DIRECTION_DOWN = 270
DIRECTION_LEFT = 180
DIRECTION_UP = 90
DIRECTION_RIGHT = 0
DIRECTION_PLAYER_START = DIRECTION_LEFT