import os
from enum import Enum
from pathlib import Path

# Window settings
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
FPS = 60
GAME_TITLE = "RAGuelike"

# Sprite settings
ORIGINAL_SPRITE_SIZE = 512
PREPROCESSED_TILE_SIZE = 256
DISPLAY_TILE_SIZE = 128

# Map settings
MAP_WIDTH = 20  # in tiles
MAP_HEIGHT = 20  # in tiles

DAY_GAME_ENDS = 2
NUM_MONSTERS = 3
NUM_NPCS = 2

# Asset paths
SOUND_DIR = Path("assets/sounds/music")
SOUNDS ={'HIT': os.path.join('assets/sounds/', 'sword.wav')}
VOICE_MAP = {
            'a': 'af_bella',  # default female
            'b': 'bm_lewis',  # default male
            'c': 'am_michael',
            'd': 'bf_emma',
            'e': 'af',
            'f': 'af_sarah',
            'g': 'am_adam',
            'h': 'bf_isabella',
            'i': 'bm_george',
            'j': 'af_nicole',
            'k': 'af_sky'
        }
WHOLE_DIALOG = False
STOP_SYMBOLS_SPEECH = '}' if WHOLE_DIALOG else '.!?'


ASSET_DIR = "assets/images"
SPRITES = {
    "PLAYER": os.path.join(ASSET_DIR, "creatures/character/player.png"),
    "HERO_FACE": os.path.join(ASSET_DIR, "creatures/character/hero_face.png"),
    "FLOOR": os.path.join(ASSET_DIR, "textures/floor_tile.png"),
    "NPC_1": os.path.join(ASSET_DIR, "creatures/npcs/npc_1.png"),
    "NPC_FACE_1": os.path.join(ASSET_DIR, "creatures/npcs/villager_face_1.png"),
    "NPC_2": os.path.join(ASSET_DIR, "creatures/npcs/npc_2.png"),
    "NPC_FACE_2": os.path.join(ASSET_DIR, "creatures/npcs/villager_face_2.png"),
    "NPC_3": os.path.join(ASSET_DIR, "creatures/npcs/npc_3.png"),
    "NPC_FACE_3": os.path.join(ASSET_DIR, "creatures/npcs/villager_face_2.png"),

    "OUTLINE_GREEN": os.path.join(ASSET_DIR, "textures/outline_green.png"),
    "OUTLINE_YELLOW": os.path.join(ASSET_DIR, "textures/outline_yellow.png"),
    "OUTLINE_RED": os.path.join(ASSET_DIR, "textures/outline_red.png"),

    "SLASH": os.path.join(ASSET_DIR, "effects/slash.png"),

    "GRASS_0": os.path.join(ASSET_DIR, "textures/grass_0.png"),
    "GRASS_1": os.path.join(ASSET_DIR, "textures/grass_1.png"),
    "GRASS_2": os.path.join(ASSET_DIR, "textures/grass_2.png"),

    "MONSTER": os.path.join(ASSET_DIR, "creatures/monsters/monster.png"),

    "GOBLIN_GIRL_1": os.path.join(ASSET_DIR, "creatures/monsters/smaller_goblin_girl_1.png"),
    "GOBLIN_GIRL_2": os.path.join(ASSET_DIR, "creatures/monsters/smaller_goblin_girl_2.png"),
    "DEAD_GOBLIN_GIRL_1": os.path.join(ASSET_DIR, "creatures/monsters/goblin_girl_f.png"),
    "DEAD_GOBLIN_GIRL_2": os.path.join(ASSET_DIR, "creatures/monsters/goblin_girl_f.png"),
    "GOBLIN_GIRL_FACE": os.path.join(ASSET_DIR, "creatures/monsters/goblin_girl_face.png"),

    "GOBLIN_1": os.path.join(ASSET_DIR, "creatures/monsters/smaller_goblin_1.png"),
    "DEAD_GOBLIN_1": os.path.join(ASSET_DIR, "creatures/monsters/goblin_dead_1.png"),
    "GOBLIN_FACE_1": os.path.join(ASSET_DIR, "creatures/monsters/goblin_face_1.png"),
    "GOBLIN_2": os.path.join(ASSET_DIR, "creatures/monsters/smaller_goblin_2.png"),
    "DEAD_GOBLIN_2": os.path.join(ASSET_DIR, "creatures/monsters/goblin_dead_1.png"),
    "GOBLIN_FACE_2": os.path.join(ASSET_DIR, "creatures/monsters/goblin_face_2.png"),
    "GOBLIN_3": os.path.join(ASSET_DIR, "creatures/monsters/smaller_goblin_3.png"),
    "DEAD_GOBLIN_3": os.path.join(ASSET_DIR, "creatures/monsters/goblin_dead_1.png"),
    "GOBLIN_FACE_3": os.path.join(ASSET_DIR, "creatures/monsters/goblin_face_3.png"),

    "BLUE_TROLL": os.path.join(ASSET_DIR, "creatures/monsters/sized_troll_1.png"),
    "BLUE_TROLL_FACE": os.path.join(ASSET_DIR, "creatures/monsters/blue_troll_face.png"),
    "DEAD_TROLL": os.path.join(ASSET_DIR, "creatures/monsters/sized_dead_troll_1.png"),

    "GREEN_TROLL": os.path.join(ASSET_DIR, "creatures/monsters/sized_troll_2.png"),
    "GREEN_TROLL_FACE": os.path.join(ASSET_DIR, "creatures/monsters/green_troll_face.png"),
    "DEAD_GREEN_TROLL": os.path.join(ASSET_DIR, "creatures/monsters/sized_dead_troll_2.png"),

    "DRYAD": os.path.join(ASSET_DIR, "creatures/monsters/sized_dryad_1.png"),
    "DRYAD_FACE": os.path.join(ASSET_DIR, "creatures/monsters/dryad_face.png"),
    "DEAD_DRYAD": os.path.join(ASSET_DIR, "creatures/monsters/sized_dead_dryad_1.png"),

    "KOBOLD": os.path.join(ASSET_DIR, "creatures/monsters/smaller_lizard.png"),
    "KOBOLD_FACE": os.path.join(ASSET_DIR, "creatures/monsters/lizard_face.png"),
    "DEAD_KOBOLD": os.path.join(ASSET_DIR, "creatures/monsters/dead_lizard.png"),

    "DEMON_BARD": os.path.join(ASSET_DIR, "creatures/monsters/bard.png"),
    "DEMON_BARD_FACE": os.path.join(ASSET_DIR, "creatures/monsters/bard_face.png"),
    "DEAD_DEMON_BARD": os.path.join(ASSET_DIR, "creatures/monsters/dead_bard.png"),

    "WILLOWHISPER": os.path.join(ASSET_DIR, "creatures/monsters/willow.png"),
    "WILLOWHISPER_FACE": os.path.join(ASSET_DIR, "creatures/monsters/willow_face.png"),
    "DEAD_WILLOWHISPER": os.path.join(ASSET_DIR, "creatures/monsters/dead_willow.png"),

    "TREE_1": os.path.join(ASSET_DIR, "textures/trees/tree_1.png"),
    "TREE_2": os.path.join(ASSET_DIR, "textures/trees/tree_2.png"),
    "TREE_3": os.path.join(ASSET_DIR, "textures/trees/tree_3.png"),
}

SPRITES.update({
    "HOUSE_FACE": os.path.join(ASSET_DIR, "textures/house/house_face.png"),
    # Top row
    "HOUSE_1_TOP_TOP": os.path.join(ASSET_DIR, "textures/house/house1_top_top.png"),
    "HOUSE_1_TOP_TOP2": os.path.join(ASSET_DIR, "textures/house/house1_top_top2.png"),
    "HOUSE_1_TOP_MID": os.path.join(ASSET_DIR, "textures/house/house1_top_mid.png"),
    "HOUSE_1_TOP_MID2": os.path.join(ASSET_DIR, "textures/house/house1_top_mid2.png"),
    "HOUSE_1_TOP_BOT": os.path.join(ASSET_DIR, "textures/house/house1_top_bot.png"),
    "HOUSE_1_TOP_BOT2": os.path.join(ASSET_DIR, "textures/house/house1_top_bot2.png"),

    # Top2 row
    "HOUSE_1_TOP2_TOP": os.path.join(ASSET_DIR, "textures/house/house1_top2_top.png"),
    "HOUSE_1_TOP2_TOP2": os.path.join(ASSET_DIR, "textures/house/house1_top2_top2.png"),
    "HOUSE_1_TOP2_MID": os.path.join(ASSET_DIR, "textures/house/house1_top2_mid.png"),
    "HOUSE_1_TOP2_MID2": os.path.join(ASSET_DIR, "textures/house/house1_top2_mid2.png"),
    "HOUSE_1_TOP2_BOT": os.path.join(ASSET_DIR, "textures/house/house1_top2_bot.png"),
    "HOUSE_1_TOP2_BOT2": os.path.join(ASSET_DIR, "textures/house/house1_top2_bot2.png"),

    # Mid row
    "HOUSE_1_MID_TOP": os.path.join(ASSET_DIR, "textures/house/house1_mid_top.png"),
    "HOUSE_1_MID_TOP2": os.path.join(ASSET_DIR, "textures/house/house1_mid_top2.png"),
    "HOUSE_1_MID_MID": os.path.join(ASSET_DIR, "textures/house/house1_mid_mid.png"),
    "HOUSE_1_MID_MID2": os.path.join(ASSET_DIR, "textures/house/house1_mid_mid2.png"),
    "HOUSE_1_MID_BOT": os.path.join(ASSET_DIR, "textures/house/house1_mid_bot.png"),
    "HOUSE_1_MID_BOT2": os.path.join(ASSET_DIR, "textures/house/house1_mid_bot2.png"),

    # Mid2 row
    "HOUSE_1_MID2_TOP": os.path.join(ASSET_DIR, "textures/house/house1_mid2_top.png"),
    "HOUSE_1_MID2_TOP2": os.path.join(ASSET_DIR, "textures/house/house1_mid2_top2.png"),
    "HOUSE_1_MID2_MID": os.path.join(ASSET_DIR, "textures/house/house1_mid2_mid.png"),
    "HOUSE_1_MID2_MID2": os.path.join(ASSET_DIR, "textures/house/house1_mid2_mid2.png"),
    "HOUSE_1_MID2_BOT": os.path.join(ASSET_DIR, "textures/house/house1_mid2_bot.png"),
    "HOUSE_1_MID2_BOT2": os.path.join(ASSET_DIR, "textures/house/house1_mid2_bot2.png"),

    # Bot row
    "HOUSE_1_BOT_TOP": os.path.join(ASSET_DIR, "textures/house/house1_bot_top.png"),
    "HOUSE_1_BOT_TOP2": os.path.join(ASSET_DIR, "textures/house/house1_bot_top2.png"),
    "HOUSE_1_BOT_MID": os.path.join(ASSET_DIR, "textures/house/house1_bot_mid.png"),
    "HOUSE_1_BOT_MID2": os.path.join(ASSET_DIR, "textures/house/house1_bot_mid2.png"),
    "HOUSE_1_BOT_BOT": os.path.join(ASSET_DIR, "textures/house/house1_bot_bot.png"),
    "HOUSE_1_BOT_BOT2": os.path.join(ASSET_DIR, "textures/house/house1_bot_bot2.png"),

    # Bot2 row
    "HOUSE_1_BOT2_TOP": os.path.join(ASSET_DIR, "textures/house/house1_bot2_top.png"),
    "HOUSE_1_BOT2_TOP2": os.path.join(ASSET_DIR, "textures/house/house1_bot2_top2.png"),
    "HOUSE_1_BOT2_MID": os.path.join(ASSET_DIR, "textures/house/house1_bot2_mid.png"),
    "HOUSE_1_BOT2_MID2": os.path.join(ASSET_DIR, "textures/house/house1_bot2_mid2.png"),
    "HOUSE_1_BOT2_BOT": os.path.join(ASSET_DIR, "textures/house/house1_bot2_bot.png"),
    "HOUSE_1_BOT2_BOT2": os.path.join(ASSET_DIR, "textures/house/house1_bot2_bot2.png"),
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
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Combat settings
TURN_TIMEOUT = 30  # seconds
CRITICAL_HIT_CHANCE = 0.1
DODGE_CHANCE = 0.05

# NPC settings
NPC_BASE_HP = 50
NPC_BASE_ARMOR = 5

NPC_MOOD = ['playful', 'drunk', 'happy', 'silly', 'friendly', 'neutral', 'greedy', 'vicious', 'unfriendly']

# Monster settings
MONSTER_BASE_HP = 35
MONSTER_BASE_ARMOR = 5
MONSTER_BASE_DAMAGE = 10
MONSTER_AGGRO_RANGE = 5
MONSTER_FLEE_HEALTH = 0.3      # Percentage of health when monster tries to flee
MONSTER_CHAT_CHANCE = 0.1
MONSTER_ATTACK_RANGE = 1
MONSTER_PERSONALITY_TYPES = [
    "aggressive",    # Attacks more often, flees less
    "cautious",      # Maintains distance, attacks when advantageous
    "cowardly",      # Flees at higher health, attacks less often
    "territorial"    # Only aggressive when player is very close
]
SHOUT_COOLDOWN = 3
MONSTER_DIALOG_CHANCE = {'goblin': 0.001}
DIALOGUE_COOLDOWN = 3
DIALOGUE_DISTANCE = 3
SPAWN_DISTANCE = 5
MONSTER_NAMES = {"orkoids": ['Skritch', 'Boggath', 'Snargle', 'Gribble', 'Shroomshriek', 'Grimfang', 'Muckbreath',
                             'Scuttle', 'Flitter', 'Twitchwarp', 'Grimnir', 'Blorf', 'Jukku', 'Skargath', 'Tarkon',
                             'Gronk', 'Cragtooth', 'Borin', 'Skrall', 'Uggr', 'Grotfang', 'Scourb', 'Snargle',
                             'Chittertooth', 'Skreesh', 'Craggoth', 'Rattlejaw', 'Grimskin', 'Festermaw', 'Whispclaw',
                              'Gorggoth', 'Grulk', 'Scrugg', 'Karkath', 'Grokk', 'Skarrk', 'Blorgh', 'Bogrim',
                              'Doomfist', "Crag'maw", 'Witheringfang', 'Fangsmoke', 'Mortifer', 'Shardshadow',
                             'Gloamfall', 'Whisperwind', 'Cinderheart', 'Silverskin', 'Thornwood', 'Moonsnare'],
                'dryad': ['Corvyl', 'Morwenna', 'Skara', 'Rixell', 'Aethel', 'Lyravan', 'Vanyel', 'Nyxys', 'Tristana',
                          'Whisperwind', 'Veridian Dusk', 'Lamentfang Briar', 'Whisperwood Vixen', 'Shadowsong Nymph',
                           "Ironbark's Bride", 'Nightshade Whisper', 'Oakblood Scion', 'Moonfall Corvus',
                          "Raven's Thorn", 'Wisteria Shade'],
                 'bard': ['Whisperbane', 'Grimlyre', 'Shadowmourn', 'Cinderblight', 'Mourningshadow', 'Dreadsong',
                          'Harbinger', 'Corruptedson', 'Festeringword', 'Nightblood', 'Khargoth the Frayed Tongue',
                          'Grimehammer Quillfang', 'Crimstone Balladbane', 'Rimewing Sorrowsong', 'Ironbark Gloomweaver',
                          'Duskwind Scarstrider', 'Sorrowborn Bardric', 'Shadowglass Whisperer', 'Bloodthorn Lyric',
                          'Whisper of Broken Dreams', 'Grimlyrdil', 'Shadowsong', 'Whisperingbane', 'Corvus the Faded',
                          'Nightsong', 'Ironheart', 'Blackmoon', 'Raventhorn', 'Mourningtide', 'Bloodrune'
                          ],
                 'spirit': ['Whispering Wraith', 'Crimson Shade', 'The Ashen Echo', 'Blackthorn Specter',
                            'Solstice Shadow', 'Bloodtide Phantom', "Morlock's Glimmer", 'Nightwalker Shriek',
                            "Ironheart's Lament", 'Ashfallen Vision', 'Whisperbane', 'Scourgewind', 'Duskmaw',
                            'Nightwraith', 'Corruptor', 'Wraithwalker', 'Spectreborn', 'Bleedtide', 'Shadowhand',
                            'The Silent One', 'Ashenveil Wraith', 'Gloomspeaker', 'Wailing Shadow', 'Corpseborn Echo',
                            'Drowned Sorrow', 'Whisperwind Revenant', 'Duskwalker Shade', 'Nightshadow Vowell',
                            'Bloodtide Spectre', 'Sorrowfall']
                 }

SLEEP_FEE = 5

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


# Forest generation settings
FOREST_EDGE_THICKNESS = 1
FOREST_EDGE_WIDTH = 4
RANDOM_TREE_CHANCE = 0.05


class GameState(Enum):
    MAIN_MENU = 1
    PLAYING = 2
    COMBAT = 3
    DIALOG = 4
    INVENTORY = 5
    DEAD = 6
    DEMO_COMPLETE = 7
