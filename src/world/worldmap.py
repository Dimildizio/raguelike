import random
import math
from queue import PriorityQueue

from .tile import Tile
from constants import *
from entities.character import Character
from entities.monster import Monster, KoboldTeacher, Dryad, GreenTroll, WillowWhisper, HellBard
from entities.npc import NPC
from entities.entity import Entity, Remains, House, Tree
from utils.sprite_loader import SpriteLoader
from systems.combat_animation import CombatAnimation


ENTITY_KEYS = {cls.__name__: cls for cls in [Entity, Character, NPC, House, Tree, Monster, KoboldTeacher, Dryad,
                                             GreenTroll, WillowWhisper, HellBard,]}


class WorldMap:
    def __init__(self, state_manager, width=MAP_WIDTH, height=MAP_HEIGHT):
        self.state_manager = state_manager
        self.width = width
        self.height = height
        self.tile_size = DISPLAY_TILE_SIZE
        self.combat_animation = CombatAnimation(self.state_manager.sound_manager)

        self.sprite_loader = SpriteLoader(
            ORIGINAL_SPRITE_SIZE,
            PREPROCESSED_TILE_SIZE,
            DISPLAY_TILE_SIZE
        )
        
        # Initialize empty tiles list
        self.tiles = [[None for _ in range(width)] for _ in range(height)]
        self.entities = []

    def save_map(self):
        idict = {'width': self.width, 'height': self.height, 'tile_size': self.tile_size,
                 'tiles': [[tile.save_tile() for tile in row] for row in self.tiles],
                 'entities': [entity.save_entity() for entity in self.get_all_entities()]
                 }
        return idict

    def load_map(self, data, game_state):
        game_state.increment_loading_progress(0)
        if 'tiles' in data:
            self.tiles = [[None for _ in range(self.width)] for _ in range(self.height)]
            for y, row in enumerate(data['tiles']):
                game_state.increment_loading_progress(30 / len(self.tiles))
                for x, tile_data in enumerate(row):
                    new_tile = Tile(tile_data['x'], tile_data['y'], tile_data['sprite_path'], loading=True)
                    new_tile.load_tile(tile_data)
                    self.tiles[y][x] = new_tile

        for key, value in data.items():
            try:
                if key == 'tiles':
                    continue
                if key == 'entities':
                    self.entities = []
                    for entity_data in value:
                        game_state.increment_loading_progress(30 / len(value))
                        new_creature = ENTITY_KEYS[entity_data['entity_class']]
                        entity = new_creature(entity_data['x'], entity_data['y'],
                                              sprite_path=entity_data['sprite_path'],
                                              game_state=self.state_manager, loading=True)
                        entity.load_entity(entity_data, self.state_manager)
                        self.add_on_load(entity)
                        if new_creature == Character:
                            self.state_manager.player = entity
                else:
                    setattr(self, key, value)

            except AssertionError as e:
                print('Error loading a tile in World Map:', e)
        game_state.increment_loading_progress(30)

    def generate_map(self):
        # Create a grid of tiles
        for y in range(self.height):
            for x in range(self.width):
                # Calculate pixel positions
                pixel_x = x * self.tile_size
                pixel_y = y * self.tile_size
                
                # Create tile with preprocessed sprite
                self.tiles[y][x] = Tile(pixel_x, pixel_y, SPRITES["FLOOR"])

    def update(self, camera_x, camera_y):
        if not camera_x or not camera_y:
            return
        start_tile_x = max(0, camera_x // self.tile_size + 1)
        start_tile_y = max(0, camera_y // self.tile_size + 1)
        end_tile_x = min(self.width, (camera_x + WINDOW_WIDTH) // self.tile_size - 1)
        end_tile_y = min(self.height, (camera_y + WINDOW_HEIGHT) // self.tile_size - 1)

        # Update only entities within visible range
        self.entities = [entity for entity in self.entities if entity.is_alive]
        for entity in self.entities:
            # Calculate entity's tile position
            entity_tile_x = entity.x // self.tile_size
            entity_tile_y = entity.y // self.tile_size

            # Only update if entity is in visible range
            if (start_tile_x <= entity_tile_x < end_tile_x) and (start_tile_y <= entity_tile_y < end_tile_y):
                entity.update()

        # Combat animation should still update regardless of visibility
        if hasattr(self, 'combat_animation'):
            self.combat_animation.update()

    def draw(self, screen, camera_x=0, camera_y=0):
        # Calculate visible tile range
        start_tile_x = max(0, camera_x // self.tile_size - 1)
        start_tile_y = max(0, camera_y // self.tile_size - 1)
        end_tile_x = min(self.width, (camera_x + screen.get_width()) // self.tile_size + 2)
        end_tile_y = min(self.height, (camera_y + screen.get_height()) // self.tile_size + 2)

        # Draw only visible tiles
        for y in range(int(start_tile_y), int(end_tile_y)):
            for x in range(int(start_tile_x), int(end_tile_x)):
                self.tiles[y][x].draw(screen, -camera_x, -camera_y)

        # Draw only visible entities
        for entity in self.entities:
            # Calculate entity's tile position
            entity_tile_x = entity.x // self.tile_size
            entity_tile_y = entity.y // self.tile_size

            # Check if entity is in visible range
            if (start_tile_x - 1 <= entity_tile_x <= end_tile_x + 1 and
                    start_tile_y - 1 <= entity_tile_y <= end_tile_y + 1):

                draw_x = entity.x
                draw_y = entity.y

                # Apply shake offset if this is the target entity
                if (hasattr(self, 'combat_animation') and
                        self.combat_animation.is_playing and
                        entity == self.combat_animation.target):
                    draw_x += self.combat_animation.shake_offset[0]
                    draw_y += self.combat_animation.shake_offset[1]

                # Draw the entity at the calculated position
                entity.draw(screen, -camera_x + (draw_x - entity.x), -camera_y + (draw_y - entity.y))

        # Draw combat animation effects
        if hasattr(self, 'combat_animation'):
            self.combat_animation.draw(screen, camera_x, camera_y)

    def get_facing_tile_position(self, player):
        """Get the tile position that the player is facing"""
        player_tile_x = int(player.x // self.tile_size)
        player_tile_y = int(player.y // self.tile_size)
        if player.facing == DIRECTION_UP:
            return player_tile_x, player_tile_y - 1
        elif player.facing == DIRECTION_DOWN:
            return player_tile_x, player_tile_y + 1
        elif player.facing == DIRECTION_LEFT:
            return player_tile_x - 1, player_tile_y
        elif player.facing == DIRECTION_RIGHT:
            return player_tile_x + 1, player_tile_y
        return None

    def get_tile_at(self, tile_x, tile_y):
        if 0 <= tile_x < self.width and 0 <= tile_y < self.height:
            return self.tiles[tile_y][tile_x]
        return None

    def move_entity(self, entity, new_tile_x, new_tile_y):
        new_tile_x = int(new_tile_x)
        new_tile_y = int(new_tile_y)
        if hasattr(self, 'combat_animation') and self.combat_animation.is_playing:
            return False

        # Check if movement is valid
        if not (0 <= new_tile_x < self.width and 0 <= new_tile_y < self.height) or (
                not self.tiles[new_tile_y][new_tile_x].passable):
            return False

        # Get destination tile and blocking entity
        destination_tile = self.tiles[new_tile_y][new_tile_x]
        blocking_entity = destination_tile.get_blocking_entity()

        if blocking_entity:
            if not blocking_entity.is_alive:
                # Remove dead entity and allow movement
                destination_tile.remove_entity(blocking_entity)
                if blocking_entity in self.entities:
                    self.entities.remove(blocking_entity)
                return self.move_entity(entity, new_tile_x, new_tile_y)

            elif isinstance(entity, Character) and isinstance(blocking_entity, Monster):
                if entity.can_do_action(ATTACK_ACTION_COST):
                    # Handle combat
                    entity.spend_action_points(ATTACK_ACTION_COST)
                    damage = blocking_entity.take_damage(entity.combat_stats.damage)

                    if hasattr(self, 'combat_animation'):
                        self.combat_animation.start_attack(entity, blocking_entity)

                    if not blocking_entity.is_alive:
                        destination_tile.remove_entity(blocking_entity)
                        self.state_manager.achievement_manager.check_achievements(self.state_manager.stats)
                        if blocking_entity in self.entities:
                            self.entities.remove(blocking_entity)
                    return True
            return False

        # Move entity logic
        old_tile_x = entity.x // self.tile_size
        old_tile_y = entity.y // self.tile_size
        movement_cost = self.get_movement_cost(old_tile_x, old_tile_y, new_tile_x, new_tile_y)
        if isinstance(entity, Character) and not entity.can_do_action(movement_cost):
            return False

        self.tiles[old_tile_y][old_tile_x].remove_entity(entity)
        destination_tile.add_entity(entity)

        # Update entity position
        entity.x = new_tile_x * self.tile_size
        entity.y = new_tile_y * self.tile_size
        if isinstance(entity, Character):
            entity.spend_action_points(movement_cost)
        return True

    def remove_entity(self, entity):
        if entity in self.entities:
            # Remove from tile's entity list
            tile_x = entity.x // self.tile_size
            tile_y = entity.y // self.tile_size
            self.tiles[tile_y][tile_x].remove_entity(entity)
            self.entities.remove(entity)

    def add_on_load(self, new_entity):
        t_size = self.tile_size
        self.add_entity(new_entity, new_entity.x // t_size, new_entity.y // t_size)

    def get_random_empty_position(self):
        """Find a random empty tile position"""
        while True:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)

            # Check if tile exists and has no blocking entities
            if (0 <= y < len(self.tiles) and
                    0 <= x < len(self.tiles[y]) and
                    self.tiles[y][x] is not None and
                    self.tiles[y][x].passable and
                    not self.tiles[y][x].get_blocking_entity()):
                return x, y

    def add_entity(self, entity, tile_x, tile_y):
        # Check if position is within bounds and no blocking entities
        print(f'Add {entity} to worldmap', tile_x, tile_y, type(self.tiles[tile_y]), type(self.tiles[tile_y][tile_x]))
        if 0 <= tile_x < self.width and 0 <= tile_y < self.height:
            if isinstance(entity, Remains):
                self.tiles[tile_y][tile_x].add_item(entity)
                return True
            if isinstance(entity, House):
                self.tiles[tile_y][tile_x].add_entity(entity)
                return True

            if self.tiles[tile_y][tile_x].passable and not self.tiles[tile_y][tile_x].get_blocking_entity():
                # Place entity
                self.tiles[tile_y][tile_x].add_entity(entity)
                entity.x = tile_x * self.tile_size
                entity.y = tile_y * self.tile_size
                self.entities.append(entity)
                return True
        return False

    def place_entities(self, player, monsters, npcs):
        # Place all entities (including player) at random empty tiles
        all_entities = [player] + monsters + npcs

        for entity in all_entities:
            placed = False
            while not placed:
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)

                if self.tiles[y][x].passable:
                    print('npc_place_entity', entity, 'x', x, 'y', y)
                    placed = self.add_entity(entity, x, y)

    def handle_monster_turn(self, monster):
        if not monster.is_alive:
            return False
        monster.count_dialogue_turns()

        # Get positions and calculate distance
        monster_tile_x = monster.x // self.tile_size
        monster_tile_y = monster.y // self.tile_size
        player = self.state_manager.player
        player_tile_x = player.x // self.tile_size
        player_tile_y = player.y // self.tile_size

        dx = player_tile_x - monster_tile_x
        dy = player_tile_y - monster_tile_y
        distance = abs(dx) + abs(dy)

        # DECISION-MAKING PHASE
        decision = monster.decide_monster_action(distance)

        # ACTION EXECUTION PHASE
        result = False
        if decision == "flee":
            result = self.execute_flee(monster, dx, dy, monster_tile_x, monster_tile_y)
        elif decision == "attack":
            result = self.execute_attack(monster, player)
        elif decision == "approach":
            result = self.execute_approach(monster, dx, dy, monster_tile_x, monster_tile_y)
        elif decision == 'moveto':
            dx, dy = monster.locate_target(self)
            result = self.execute_approach(monster, dx, dy, monster_tile_x, monster_tile_y)
        # If monster still has AP and made a successful action, it can act again next frame
        if monster.combat_stats.ap > 0 and result:
            return True
        # If monster couldn't act or is out of AP, it's done
        return False

    def execute_attack(self, monster, player):
        """Execute attack action"""
        animation = False
        if not monster.can_do_action(ATTACK_ACTION_COST):
            return False

        monster.spend_action_points(ATTACK_ACTION_COST)

        # Calculate and set rotation BEFORE starting animation
        dx = player.x - monster.x
        dy = player.y - monster.y
        angle = math.degrees(math.atan2(-dy, dx)) + 90
        monster.base_rotation = angle

        if hasattr(self, 'combat_animation'):
            animation = self.combat_animation.start_attack(monster, player)
        damage = monster.attack(player)
        return animation

    def get_neighbors(self, x, y):
        """Get valid neighboring tiles"""
        neighbors = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:  # Four directions (no diagonals)
            new_x, new_y = x + dx, y + dy
            if (0 <= new_x < self.width and
                    0 <= new_y < self.height and
                    self.is_tile_walkable(new_x, new_y)):
                neighbors.append((new_x, new_y))
        return neighbors

    def is_tile_walkable(self, x, y):
        """Check if a tile can be walked on"""
        if not (0 <= x < self.width and 0 <= y < self.height) or not self.tiles[y][x].passable:
            return False
        tile = self.tiles[y][x]

        return tile and (tile.get_blocking_entity() is None)

    @staticmethod
    def manhattan_distance(x1, y1, x2, y2):
        """Calculate Manhattan distance between two points"""
        return abs(x1 - x2) + abs(y1 - y2)

    def find_path_to_target(self, start_x, start_y, target_x, target_y):
        """A* pathfinding to find the best path to target"""
        frontier = PriorityQueue()
        frontier.put((0, (start_x, start_y)))
        came_from = {(start_x, start_y): None}
        cost_so_far = {(start_x, start_y): 0}
        current = None
        while not frontier.empty():
            current = frontier.get()[1]

            # If we found a tile adjacent to target, we're done
            if self.manhattan_distance(current[0], current[1], target_x, target_y) == 1:
                break

            # Check all neighbors
            for next_tile in self.get_neighbors(current[0], current[1]):
                # Skip if tile is not passable or has blocking entity
                if (not self.tiles[next_tile[1]][next_tile[0]].passable or
                        self.tiles[next_tile[1]][next_tile[0]].get_blocking_entity()):
                    continue

                new_cost = cost_so_far[current] + 1

                if next_tile not in cost_so_far or new_cost < cost_so_far[next_tile]:
                    cost_so_far[next_tile] = new_cost
                    priority = new_cost + self.manhattan_distance(next_tile[0], next_tile[1], target_x, target_y)
                    frontier.put((priority, next_tile))
                    came_from[next_tile] = current

        # Reconstruct path
        if current in came_from:
            path = []
            while current != (start_x, start_y):
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path
        return []

    def execute_approach(self, monster, dx, dy, monster_tile_x, monster_tile_y):
        """Execute approach movement using pathfinding"""
        if not monster.can_do_action(MOVE_ACTION_COST):
            return False

        player = self.state_manager.player
        player_tile_x = player.x // self.tile_size
        player_tile_y = player.y // self.tile_size

        # Find path to player
        path = self.find_path_to_target(
            monster_tile_x,
            monster_tile_y,
            player_tile_x,
            player_tile_y
        )

        if not path:
            return False

        # Get next step in path
        next_x, next_y = path[0]

        # Calculate facing direction
        dx = next_x - monster_tile_x
        dy = next_y - monster_tile_y

        if dx > 0:
            monster.base_rotation = DIRECTION_RIGHT
        elif dx < 0:
            monster.base_rotation = DIRECTION_LEFT
        elif dy > 0:
            monster.base_rotation = DIRECTION_DOWN
        elif dy < 0:
            monster.base_rotation = DIRECTION_UP

        # Move to next tile
        if self.move_entity(monster, next_x, next_y):
            monster.spend_action_points(MOVE_ACTION_COST)
            return True

        return False

    def execute_flee(self, monster, dx, dy, monster_tile_x, monster_tile_y):
        """Execute fleeing movement"""
        if not monster.can_do_action(MOVE_ACTION_COST):
            return False
        # Check if monster is next to edge tree
        if monster.is_at_edge_tree(self):
            self.state_manager.add_message(f"{monster.monster_type} {monster.name} ran away!", color=YELLOW)
            self.remove_entity(monster)
            monster.combat_stats.hp = 0
            monster.combat_stats.ap = 0
            return False
        # Find nearest edge tree
        target = monster.find_nearest_edge_tree(self)
        if not target:
            # No edge trees found, use old fleeing behavior
            move_x = monster_tile_x + (-1 if dx > 0 else 1) if abs(dx) > abs(dy) else monster_tile_x
            move_y = monster_tile_y + (-1 if dy > 0 else 1) if abs(dx) <= abs(dy) else monster_tile_y
        else:
            # Use pathfinding to get to edge tree
            target_x, target_y = target
            path = self.find_path_to_target(monster_tile_x, monster_tile_y, target_x, target_y)
            if not path:
                return False

            # Get next step in path
            move_x, move_y = path[0]

        # Calculate facing direction
        if abs(dx) > abs(dy):
            monster.base_rotation = DIRECTION_LEFT if dx > 0 else DIRECTION_RIGHT
        else:
            monster.base_rotation = DIRECTION_UP if dy > 0 else DIRECTION_DOWN

        # Only spend AP if movement was successful
        if self.move_entity(monster, move_x, move_y):
            monster.spend_action_points(MOVE_ACTION_COST)
            return True
        return False

    def get_valid_positions(self, count):
        """Get list of valid positions for entities"""
        valid_positions = []
        for y in range(self.height):
            for x in range(self.width):
                # Check if tile is walkable and doesn't have entities
                if not self.tiles[y][x].entities and self.tiles[y][x].passable:
                    valid_positions.append((x, y))

        # Shuffle and return requested number of positions
        random.shuffle(valid_positions)
        return valid_positions[:count]

    def is_valid_move(self, x, y):
        """Check if position is valid for movement"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x].passable
        return False

    def get_all_entities(self):
        """Get list of all entities on the map"""
        entities = []
        for row in self.tiles:
            for tile in row:
                entities.extend(tile.entities)
        return entities

    def get_random_nearby_tile(self, entity, radius=4):
        """Get a random free tile within specified radius of the entity

        Args:
            entity: The entity to find nearby tiles for
            radius: How far to look for free tiles (default 4)

        Returns:
            tuple: (x, y) tile coordinates or None if no free tiles found
        """
        # Get entity's current tile position
        current_x = entity.x // DISPLAY_TILE_SIZE
        current_y = entity.y // DISPLAY_TILE_SIZE

        # Get all possible tiles within radius
        possible_tiles = []
        for y in range(max(0, current_y - radius), min(self.height, current_y + radius + 1)):
            for x in range(max(0, current_x - radius), min(self.width, current_x + radius + 1)):
                # Skip current tile
                if x == current_x and y == current_y:
                    continue

                # Check if tile is passable and empty
                if (self.tiles[y][x].passable and
                        not any(isinstance(e, Monster) for e in self.tiles[y][x].entities)):
                    possible_tiles.append((x, y))

        # Return random tile if any found
        if possible_tiles:
            return random.choice(possible_tiles)
        return None

    def move_entity_to(self, entity, new_x, new_y):
        """Move entity to specific tile coordinates"""
        # Remove from current position
        old_x = entity.x // DISPLAY_TILE_SIZE
        old_y = entity.y // DISPLAY_TILE_SIZE
        self.tiles[old_y][old_x].remove_entity(entity)

        # Update entity position
        entity.x = new_x * DISPLAY_TILE_SIZE
        entity.y = new_y * DISPLAY_TILE_SIZE

        # Add to new position
        self.tiles[new_y][new_x].add_entity(entity)

    @staticmethod
    def get_movement_cost(from_x, from_y, to_x, to_y):
        dx = abs(to_x - from_x)
        dy = abs(to_y - from_y)
        if dx == 1 and dy == 1:
            return int(MOVE_ACTION_COST * 1.5)
        return MOVE_ACTION_COST
