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
MAP_WIDTH = 20  # in tiles
MAP_HEIGHT = 20  # in tiles

NUM_MONSTERS = 3
NUM_NPCS = 2

# Asset paths
ASSET_DIR = "assets"
SPRITES = {
    "PLAYER": os.path.join(ASSET_DIR, "player.png"),
    "HERO_FACE": os.path.join(ASSET_DIR, "hero_face.png"),
    "FLOOR": os.path.join(ASSET_DIR, "floor_tile.png"),
    "NPC_1": os.path.join(ASSET_DIR, "npc_1.png"),
    "NPC_FACE_1": os.path.join(ASSET_DIR, "villager_face_1.png"),
    "NPC_2": os.path.join(ASSET_DIR, "npc_2.png"),
    "NPC_FACE_2": os.path.join(ASSET_DIR, "villager_face_2.png"),
    "NPC_3": os.path.join(ASSET_DIR, "npc_3.png"),
    "NPC_FACE_3": os.path.join(ASSET_DIR, "villager_face_3.png"),
    "MONSTER": os.path.join(ASSET_DIR, "monster.png"),
    "OUTLINE_GREEN": os.path.join(ASSET_DIR, "outline_green.png"),
    "OUTLINE_YELLOW": os.path.join(ASSET_DIR, "outline_yellow.png"),
    "OUTLINE_RED": os.path.join(ASSET_DIR, "outline_red.png"),
    "SLASH": os.path.join(ASSET_DIR, "slash.png"),
    "GRASS_0": os.path.join(ASSET_DIR, "grass_0.png"),
    "GRASS_1": os.path.join(ASSET_DIR, "grass_1.png"),
    "GRASS_2": os.path.join(ASSET_DIR, "grass_2.png"),
}

SPRITES.update({
    # Top row
    "HOUSE_1_TOP_TOP": os.path.join(ASSET_DIR, "house/house1_top_top.png"),
    "HOUSE_1_TOP_TOP2": os.path.join(ASSET_DIR, "house/house1_top_top2.png"),
    "HOUSE_1_TOP_MID": os.path.join(ASSET_DIR, "house/house1_top_mid.png"),
    "HOUSE_1_TOP_MID2": os.path.join(ASSET_DIR, "house/house1_top_mid2.png"),
    "HOUSE_1_TOP_BOT": os.path.join(ASSET_DIR, "house/house1_top_bot.png"),
    "HOUSE_1_TOP_BOT2": os.path.join(ASSET_DIR, "house/house1_top_bot2.png"),

    # Top2 row
    "HOUSE_1_TOP2_TOP": os.path.join(ASSET_DIR, "house/house1_top2_top.png"),
    "HOUSE_1_TOP2_TOP2": os.path.join(ASSET_DIR, "house/house1_top2_top2.png"),
    "HOUSE_1_TOP2_MID": os.path.join(ASSET_DIR, "house/house1_top2_mid.png"),
    "HOUSE_1_TOP2_MID2": os.path.join(ASSET_DIR, "house/house1_top2_mid2.png"),
    "HOUSE_1_TOP2_BOT": os.path.join(ASSET_DIR, "house/house1_top2_bot.png"),
    "HOUSE_1_TOP2_BOT2": os.path.join(ASSET_DIR, "house/house1_top2_bot2.png"),

    # Mid row
    "HOUSE_1_MID_TOP": os.path.join(ASSET_DIR, "house/house1_mid_top.png"),
    "HOUSE_1_MID_TOP2": os.path.join(ASSET_DIR, "house/house1_mid_top2.png"),
    "HOUSE_1_MID_MID": os.path.join(ASSET_DIR, "house/house1_mid_mid.png"),
    "HOUSE_1_MID_MID2": os.path.join(ASSET_DIR, "house/house1_mid_mid2.png"),
    "HOUSE_1_MID_BOT": os.path.join(ASSET_DIR, "house/house1_mid_bot.png"),
    "HOUSE_1_MID_BOT2": os.path.join(ASSET_DIR, "house/house1_mid_bot2.png"),

    # Mid2 row
    "HOUSE_1_MID2_TOP": os.path.join(ASSET_DIR, "house/house1_mid2_top.png"),
    "HOUSE_1_MID2_TOP2": os.path.join(ASSET_DIR, "house/house1_mid2_top2.png"),
    "HOUSE_1_MID2_MID": os.path.join(ASSET_DIR, "house/house1_mid2_mid.png"),
    "HOUSE_1_MID2_MID2": os.path.join(ASSET_DIR, "house/house1_mid2_mid2.png"),
    "HOUSE_1_MID2_BOT": os.path.join(ASSET_DIR, "house/house1_mid2_bot.png"),
    "HOUSE_1_MID2_BOT2": os.path.join(ASSET_DIR, "house/house1_mid2_bot2.png"),

    # Bot row
    "HOUSE_1_BOT_TOP": os.path.join(ASSET_DIR, "house/house1_bot_top.png"),
    "HOUSE_1_BOT_TOP2": os.path.join(ASSET_DIR, "house/house1_bot_top2.png"),
    "HOUSE_1_BOT_MID": os.path.join(ASSET_DIR, "house/house1_bot_mid.png"),
    "HOUSE_1_BOT_MID2": os.path.join(ASSET_DIR, "house/house1_bot_mid2.png"),
    "HOUSE_1_BOT_BOT": os.path.join(ASSET_DIR, "house/house1_bot_bot.png"),
    "HOUSE_1_BOT_BOT2": os.path.join(ASSET_DIR, "house/house1_bot_bot2.png"),

    # Bot2 row
    "HOUSE_1_BOT2_TOP": os.path.join(ASSET_DIR, "house/house1_bot2_top.png"),
    "HOUSE_1_BOT2_TOP2": os.path.join(ASSET_DIR, "house/house1_bot2_top2.png"),
    "HOUSE_1_BOT2_MID": os.path.join(ASSET_DIR, "house/house1_bot2_mid.png"),
    "HOUSE_1_BOT2_MID2": os.path.join(ASSET_DIR, "house/house1_bot2_mid2.png"),
    "HOUSE_1_BOT2_BOT": os.path.join(ASSET_DIR, "house/house1_bot2_bot.png"),
    "HOUSE_1_BOT2_BOT2": os.path.join(ASSET_DIR, "house/house1_bot2_bot2.png"),
})


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
PLAYER_BASE_DAMAGE = 25
BREATHING_SPEED = 0.1
BREATHING_AMPLITUDE = 10  # degrees

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
MONSTER_BASE_DAMAGE = 15
MONSTER_AGGRO_RANGE = 5
MONSTER_FLEE_HEALTH = 0.3      # Percentage of health when monster tries to flee
MONSTER_ATTACK_RANGE = 1
MONSTER_PERSONALITY_TYPES = [
    "aggressive",    # Attacks more often, flees less
    "cautious",      # Maintains distance, attacks when advantageous
    "cowardly",      # Flees at higher health, attacks less often
    "territorial"    # Only aggressive when player is very close
]
DIALOGUE_COOLDOWN = 3
DIALOGUE_DISTANCE = 3

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
DIRECTION_DOWN = 0
DIRECTION_LEFT = 270
DIRECTION_UP = 180
DIRECTION_RIGHT = 90
DIRECTION_PLAYER_START = DIRECTION_DOWN


ATTACK_ANIMATION_DURATION = 0.5  # seconds
ATTACK_DISTANCE = 0.5
SHAKE_AMPLITUDE = 3  # pixels
SHAKE_FREQUENCY = 30
MOVEMENT_DELAY = 0.2

INITIAL_ACTION_POINTS = 100
MOVE_ACTION_COST = 10
ATTACK_ACTION_COST = 35