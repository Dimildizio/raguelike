import random
import math
import heapq
from queue import PriorityQueue

from .tile import Tile
from constants import *
from entities.character import Character
from entities.monster import Monster
from entities.entity import Remains, House
from utils.sprite_loader import SpriteLoader
from systems.combat_animation import CombatAnimation


class WorldMap:
    def __init__(self, state_manager, width=MAP_WIDTH, height=MAP_HEIGHT):
        self.state_manager = state_manager
        self.width = width
        self.height = height
        self.tile_size = DISPLAY_TILE_SIZE
        self.combat_animation = CombatAnimation()

        self.sprite_loader = SpriteLoader(
            ORIGINAL_SPRITE_SIZE,
            PREPROCESSED_TILE_SIZE,
            DISPLAY_TILE_SIZE
        )
        
        # Initialize empty tiles list
        self.tiles = [[None for _ in range(width)] for _ in range(height)]
        self.entities = []
        
        # Generate the map
        #self.generate_map()
    
    def generate_map(self):
        # Create a grid of tiles
        for y in range(self.height):
            for x in range(self.width):
                # Calculate pixel positions
                pixel_x = x * self.tile_size
                pixel_y = y * self.tile_size
                
                # Create tile with preprocessed sprite
                self.tiles[y][x] = Tile(pixel_x, pixel_y, SPRITES["FLOOR"])

    def update(self):
        self.entities = [entity for entity in self.entities if entity.is_alive]
        for entity in self.entities:
            entity.update()

        if hasattr(self, 'combat_animation'):
            self.combat_animation.update()

    def draw(self, screen, camera_x=0, camera_y=0):
        # Draw tiles
        for y in range(self.height):
            for x in range(self.width):
                self.tiles[y][x].draw(screen, -camera_x, -camera_y)

        # Draw entities with potential shake offset
        for entity in self.entities:
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
                        if blocking_entity in self.entities:
                            self.entities.remove(blocking_entity)
                    return True
            return False

        if isinstance(entity, Character) and not entity.can_do_action(MOVE_ACTION_COST):
            return False

        # Move to new tile
        old_tile_x = entity.x // self.tile_size
        old_tile_y = entity.y // self.tile_size

        # Update tiles
        self.tiles[old_tile_y][old_tile_x].remove_entity(entity)
        destination_tile.add_entity(entity)

        # Update entity position
        entity.x = new_tile_x * self.tile_size
        entity.y = new_tile_y * self.tile_size
        if isinstance(entity, Character):
            entity.spend_action_points(MOVE_ACTION_COST)
        return True

    def remove_entity(self, entity):
        if entity in self.entities:
            # Remove from tile's entity list
            tile_x = entity.x // self.tile_size
            tile_y = entity.y // self.tile_size
            self.tiles[tile_y][tile_x].remove_entity(entity)
            self.entities.remove(entity)


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
        print(f'adding {entity} to worldmap', tile_x, tile_y)
        if 0 <= tile_x < self.width and 0 <= tile_y < self.height:
            if isinstance(entity, Remains):
                self.tiles[tile_y][tile_x].add_item(entity)
                return True
            if isinstance(entity, House):
                self.tiles[tile_y][tile_x].add_entity(entity)
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
        decision = self.decide_monster_action(monster, distance)

        # ACTION EXECUTION PHASE
        result = False
        if decision == "flee":
            result = self.execute_flee(monster, dx, dy, monster_tile_x, monster_tile_y)
        elif decision == "attack":
            result = self.execute_attack(monster, player)
        elif decision == "approach":
            result = self.execute_approach(monster, dx, dy, monster_tile_x, monster_tile_y)

        # If monster still has AP and made a successful action, it can act again next frame
        if monster.action_points > 0 and result:
            return True

        # If monster couldn't act or is out of AP, it's done
        return False


    def decide_monster_action(self, monster, distance):
        """Decide what action the monster should take based on its personality and situation"""
        # Should we flee?
        if monster.lost_resolve():
                return "flee"
        # Should we attack?
        if distance == 1:  # Adjacent to player
            # Aggressive monsters are more likely to attack
            if random.random() < monster.aggression:
                return "attack"

        # Should we approach?
        if distance <= MONSTER_AGGRO_RANGE:
            # Aggressive monsters are more likely to approach
            result = random.random()
            print(f'Lets attack: {result} vs {monster.aggression}')
            if result < monster.aggression:
                return "approach"
        return "none"

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
            # Remove monster from game
            self.remove_entity(monster)
            return True

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
