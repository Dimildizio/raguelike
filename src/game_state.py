from enum import Enum
from world.create_map import MapCreator
from world.worldmap import WorldMap
from entities.character import Character
from systems.quest import QuestManager
from entities.monster import Monster, GreenTroll, Dryad, KoboldTeacher, HellBard
from entities.entity import Tree, House
from entities.npc import NPC
from ui.log_ui import MessageLog
from ui.floating_text import FloatingTextManager
from utils.achievements import AchievementManager
from constants import *
import random


class GameStateManager:
    def __init__(self, sound_manager):
        self.current_state = GameState.MAIN_MENU
        self.sound_manager = sound_manager
        self.achievement_manager = AchievementManager()
        self.message_log = None
        self.selected_menu_item = 0  # Track which menu item is selected
        self.current_map = WorldMap(self)
        self.player = None  # Don't create player until game starts
        self.combat_system = None
        self.current_npc = None
        self.current_day = 1
        self.stats = {'quests_completed': 0, 'monsters_killed': {}, 'gold_collected': 0}
        self.quest_manager = QuestManager()
        self.floating_text_manager = FloatingTextManager()

    def start_new_game1(self):
        self.player = None
        self.current_map = None

        # Create player
        self.player = Character(0, 0, "PLAYER", game_state=self)

        # Create monsters
        monsters = [
            Monster(0, 0, "MONSTER", name=f'Monster_{n}', game_state=self) for n in range(NUM_MONSTERS)
        ]

        # Create NPCs
        npc_imgs = [{'name': 'Villager Amelia', 'sprite': 'NPC_1', 'face': 'NPC_FACE_1', 'description': 'young girl'},
                    {'name': 'Merchant Tom', 'sprite': 'NPC_2', 'face': 'NPC_FACE_2', 'description': 'old tired merchant'},
                    {'name': 'Elara the Elara', 'sprite': 'NPC_3', 'face': 'NPC_FACE_3', 'description': 'middle aged half ork woman'},]
        npcs = [
            NPC(0, 0, npc_imgs[n]['sprite'], face_path=npc_imgs[n]['face'], name=npc_imgs[n]['name'],
                mood=random.choice(NPC_MOOD), game_state=self, description=npc_imgs[n]['description'],
                ) for n in range(NUM_NPCS)]

        # Create and setup map
        self.current_map = WorldMap(self, MAP_WIDTH, MAP_HEIGHT)
        self.current_map.generate_map()


        # Place all entities
        self.current_map.place_entities(self.player, monsters, npcs)
        self.change_state(GameState.MAIN_MENU)

    def start_new_game(self):
        self.player = None
        self.current_map = None

        # Create player
        self.player = Character(0, 0, "PLAYER", game_state=self, voice='c')

        # Create monsters
        monsters = []
        for n in range(NUM_MONSTERS):
            monsters.append(self.create_goblin((0,0)))
        monsters.append(self.create_green_troll((0, 0)))
        monsters.append(self.create_blue_troll((0, 0)))
        monsters.append(self.create_dryad((0, 0)))
        monsters.append(self.create_kobold_teacher((0, 0)))
        monsters.append(self.create_hell_bard((0, 0)))

        # Create NPCs with specific attributes
        npc_data = [
            {
                'name': 'Villager Amelia',
                'sprite': 'NPC_1',
                'face': 'NPC_FACE_1',
                'description': 'young girl',
                'position': None,  # Will be set by MapCreator
                'voice': 'a',
            },
            {
                'name': 'Merchant Tom',
                'sprite': 'NPC_2',
                'face': 'NPC_FACE_2',
                'description': 'old tired merchant',
                'position': None,
                'voice': 'b',
            }
        ]
        moods = ['playful', 'happy', 'silly', 'friendly', 'neutral', 'greedy', 'vicious', 'unfriendly']
        npcs = [
            NPC(0, 0, npc['sprite'], face_path=npc['face'], name=npc['name'], voice=npc['voice'],
                mood=random.choice(moods), game_state=self, description=npc['description']
                ) for npc in npc_data
        ]

        # Create and setup map with MapCreator
        self.current_map = WorldMap(self, MAP_WIDTH, MAP_HEIGHT)
        if not self.message_log and self.current_map:
            self.message_log = MessageLog()
            self.message_log.add_message("Welcome to the game!", WHITE)
        map_creator = MapCreator(self.current_map.sprite_loader)
        tiles, house_pos, npc_positions, tree_positions = map_creator.create_map()
        self.current_map.tiles = tiles

        # Place house at random valid position from MapCreator
        for (h_x, h_y) in house_pos:
            self.current_map.add_entity(House(h_x, h_y, voice=random.choice([x for x in VOICE_MAP.keys()])), h_x, h_y)
        # Place NPCs at their designated positions from MapCreator
        for npc, position in zip(npcs, npc_positions):
            x, y = position
            print('npc_start', npc.name, 'x', x, 'y', y)
            self.current_map.add_entity(npc, x, y)
        for x, y in tree_positions:
            tree = Tree(x, y, random.choice([SPRITES["TREE_1"], SPRITES["TREE_2"], SPRITES["TREE_3"]]))
            self.current_map.add_entity(tree, x, y)

        # Place player and monsters in random valid positions
        valid_positions = self.current_map.get_valid_positions(len(monsters) + 1)

        # Place player
        player_pos = valid_positions.pop()
        print('npc', self.player, 'x', player_pos[0], 'y', player_pos[1])
        self.current_map.add_entity(self.player, player_pos[0], player_pos[1])

        # Place monsters
        for monster in monsters:
            if valid_positions:
                pos = valid_positions.pop()
                print('monster', monster, 'x', pos[0], 'y', [pos[1]])
                self.current_map.add_entity(monster, pos[0], pos[1])

        self.change_state(GameState.MAIN_MENU)

    def change_state(self, new_state):
        self.current_state = new_state

    def add_message(self, message, color=YELLOW):
        """Add a message to the log"""
        if self.message_log:
            self.message_log.add_message(message, color)

    def accept_quest(self, quest_id: str) -> bool:
        """Handle quest acceptance through the game state"""
        if self.player and self.quest_manager.start_quest(quest_id):
            return self.player.accept_quest(quest_id)
        return False

    def show_ending_stats(self):
        """Prepare final statistics for display"""
        self.stats['gold_collected'] = self.player.gold if self.player else 0
        print("\n=== Demo Complete! ===")
        print(f"Days Survived: {self.current_day}")
        print(f"Quests Completed: {self.stats['quests_completed']}")
        print(f"Monsters Slain: {self.stats['monsters_killed']}")
        print(f"Gold Collected: {self.stats['gold_collected']}")
        print("===================\n")

    def complete_quest(self, quest_id: str):
        """Handle quest completion through the game state"""
        if self.player:
            rewards = self.quest_manager.check_quest_completion(quest_id, self.player, self.current_npc)
            if rewards:
                self.stats['quests_completed'] += 1
                self.player.complete_quest(quest_id)
                self.achievement_manager.check_achievements(self.stats)
                return rewards
        return None

    def get_active_quests(self):
        """Get list of active quests for dialogue context"""
        if not self.player:
            return []
        return [self.quest_manager.quests[qid].to_dict()
                for qid in self.player.active_quests
                if qid in self.quest_manager.quests]

    def get_available_quests(self, npc_id: str):
        """Get available quests for specific NPC that player hasn't accepted/completed"""
        if not self.player:
            return []
        return [quest for quest in self.quest_manager.get_available_quests(npc_id)
                if quest.quest_id not in self.player.active_quests
                and quest.quest_id not in self.player.completed_quests]

    def update_quest_progress(self, condition_type: str, value: int = 1):
        """Update progress for all active quests"""
        if self.player:
            self.quest_manager.update_quest_progress(condition_type, value)

    def pass_night(self, fee=0):
        """Handle night passing effects"""
        # Check if player can afford lodging

        if not self.player or not self.player.spend_gold(fee):
            print('not enough money')
            return False
        print('night has passed')
        # Heal all entities with combat stats
        self.current_day += 1
        self.player.heal_self()
        self.player.action_points = self.player.max_action_points
        if self.current_day > DAY_GAME_ENDS:
            self.show_ending_stats()
            self.change_state(GameState.DEMO_COMPLETE)
            return True

        # Heal NPCs and change their moods
        for entity in self.current_map.get_all_entities():
            if hasattr(entity, 'combat_stats'):
                if isinstance(entity, NPC):
                    entity.mood = random.choice(NPC_MOOD)
                    entity.heal_self()
                elif isinstance(entity, Monster):
                    entity.heal_self()

        # Get player position
        player_x = self.player.x // DISPLAY_TILE_SIZE
        player_y = self.player.y // DISPLAY_TILE_SIZE

        # Get valid positions for monsters (5+ tiles away from player)
        valid_positions = []
        for y in range(self.current_map.height):
            for x in range(self.current_map.width):
                dist_to_player = abs(x - player_x) + abs(y - player_y)

                if (dist_to_player >= SPAWN_DISTANCE and self.current_map.tiles[y][x].passable and
                        not self.current_map.tiles[y][x].entities):
                    valid_positions.append((x, y))
        if not valid_positions:
            return True
        for entity in self.current_map.get_all_entities():
            if isinstance(entity, Monster):
                if valid_positions:
                    new_pos = random.choice(valid_positions)
                    valid_positions.remove(new_pos)
                    self.current_map.move_entity_to(entity, new_pos[0], new_pos[1])

        # Spawn new goblin if positions available
        for day in range(self.current_day):
            if valid_positions:
                self.spawn_monster(self.create_goblin, valid_positions)
            if self.current_day >= 2 and valid_positions:
                self.spawn_monster(self.create_green_troll, valid_positions)
            if self.current_day >= 3 and valid_positions:
                self.spawn_monster(self.create_blue_troll, valid_positions)

        return True

    def spawn_monster(self, spawn_func, valid_positions):
        spawn_pos = random.choice(valid_positions)
        monster = spawn_func(spawn_pos)
        self.current_map.add_entity(monster, spawn_pos[0], spawn_pos[1])
        valid_positions.remove(spawn_pos)
        return monster

    def create_goblin(self, spawn_pos):
        if random.random() > 0.7:
            voice = random.choice([x[0] for x in VOICE_MAP.values() if x[1] == 'f'])
            sprite = random.choice(['GOBLIN_GIRL_1', 'GOBLIN_GIRL_2'])
            return Monster(x=spawn_pos[0] * DISPLAY_TILE_SIZE, y=spawn_pos[1] * DISPLAY_TILE_SIZE, voice=voice,
                           sprite_path=sprite, name='Unknown Goblin', monster_type='goblin', game_state=self,
                           face_path=SPRITES['GOBLIN_GIRL_FACE'], description='small and vicious green female creature')
        else:

            voice = random.choice([x[0] for x in VOICE_MAP.values() if x[1] != 'f'])
            sprite = random.choice(['GOBLIN_1', 'GOBLIN_2', 'GOBLIN_3'])
            face = SPRITES[random.choice(['GOBLIN_FACE_1', 'GOBLIN_FACE_2', 'GOBLIN_FACE_3'])]
            return Monster(x=spawn_pos[0] * DISPLAY_TILE_SIZE, y=spawn_pos[1] * DISPLAY_TILE_SIZE, voice=voice,
                           sprite_path=sprite, name='Unknown Goblin', monster_type='goblin', game_state=self,
                           face_path=face, description='small, vile and hateful greenskin creature')

    def create_blue_troll(self, spawn_pos):
        return Monster(x=spawn_pos[0] * DISPLAY_TILE_SIZE, y=spawn_pos[1] * DISPLAY_TILE_SIZE, sprite_path="BLUE_TROLL",
                       name='Trolliddrr', game_state=self, voice='i', ap=70,
                       face_path=SPRITES["BLUE_TROLL_FACE"], monster_type='troll',
                       description='big blue ugly hulking creature that loves jokes and riddles',
                       hp=int(MONSTER_BASE_HP * 1.5), dmg=int(MONSTER_BASE_DAMAGE * 2),
                       armor=int(MONSTER_BASE_ARMOR * 2))

    def create_green_troll(self, spawn_pos):
        return GreenTroll(x=spawn_pos[0] * DISPLAY_TILE_SIZE, y=spawn_pos[1] * DISPLAY_TILE_SIZE,
                          sprite_path="GREEN_TROLL", name='Gubdakrr', game_state=self, voice='g', ap=65,
                          face_path=SPRITES["GREEN_TROLL_FACE"], monster_type='green_troll',
                          description='big green ugly hulking foul-mouthed creature',
                          hp=int(MONSTER_BASE_HP * 3), dmg=int(MONSTER_BASE_DAMAGE * 2),
                          armor=int(MONSTER_BASE_ARMOR * 2))

    def create_dryad(self, spawn_pos):
        return Dryad(x=spawn_pos[0] * DISPLAY_TILE_SIZE, y=spawn_pos[1] * DISPLAY_TILE_SIZE, monster_type='dryad',
                          sprite_path="DRYAD", name='Elindiara', game_state=self)

    def create_kobold_teacher(self, spawn_pos):
        return KoboldTeacher(x=spawn_pos[0] * DISPLAY_TILE_SIZE, y=spawn_pos[1] * DISPLAY_TILE_SIZE,
                             monster_type='kobold', sprite_path="KOBOLD", name='Teacherr', game_state=self)

    def create_hell_bard(self, spawn_pos):
        return HellBard(x=spawn_pos[0] * DISPLAY_TILE_SIZE, y=spawn_pos[1] * DISPLAY_TILE_SIZE,
                        sprite_path="DEMON_BARD", name='Versifer', game_state=self, voice='c')
