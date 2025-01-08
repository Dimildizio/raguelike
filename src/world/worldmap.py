import pygame
from .tile import Tile
import random
import math
from constants import *
from entities.character import Character
from entities.monster import Monster
from entities.npc import NPC
from constants import SPRITES
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
        self.generate_map()
    
    def generate_map(self):
        # Create a grid of tiles
        for y in range(self.height):
            for x in range(self.width):
                # Calculate pixel positions
                pixel_x = x * self.tile_size
                pixel_y = y * self.tile_size
                
                # Create tile with preprocessed sprite
                self.tiles[y][x] = Tile(pixel_x, pixel_y, SPRITES["FLOOR"])

    def generate(self):
        """Generate a simple room-based map"""
        # Fill map with walls initially
        for y in range(self.height):
            for x in range(self.width):
                self.tiles[y][x].type = TILE_WALL

        # Create a main room in the center
        room_width = self.width // 2
        room_height = self.height // 2
        start_x = (self.width - room_width) // 2
        start_y = (self.height - room_height) // 2

        # Fill room with floor tiles
        for y in range(start_y, start_y + room_height):
            for x in range(start_x, start_x + room_width):
                self.tiles[y][x].type = TILE_FLOOR

        print(f"Generated map with dimensions {self.width}x{self.height}")
        print(f"Created room at {start_x},{start_y} with size {room_width}x{room_height}")

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

    
    def remove_entity(self, entity):
        if entity in self.entities:
            # Find and clear tile's entity reference
            tile_x = entity.x // self.tile_size
            tile_y = entity.y // self.tile_size
            self.tiles[tile_y][tile_x].entity = None
            self.entities.remove(entity)
    
    def get_tile_at(self, tile_x, tile_y):
        if 0 <= tile_x < self.width and 0 <= tile_y < self.height:
            return self.tiles[tile_y][tile_x]
        return None

    def move_entity(self, entity, new_tile_x, new_tile_y):
        new_tile_x = int(new_tile_x)
        new_tile_y = int(new_tile_y)
        if hasattr(self, 'combat_animation') and self.combat_animation.is_playing:
            return False  # Don't allow movement/attack during animation

        # Check if movement is valid
        if not (0 <= new_tile_x < self.width and 0 <= new_tile_y < self.height):
            return False

        # Get entity at destination tile
        destination_tile = self.tiles[new_tile_y][new_tile_x]
        destination_entity = destination_tile.entity

        # Debug prints
        if destination_entity:
            print(f"Found entity at destination: {type(destination_entity)}")
            print(f"Entity HP: {destination_entity.combat_stats.current_hp}")
            print(f"Is alive: {destination_entity.is_alive}")

        # Check if destination has a living entity
        if destination_entity is not None:
            if not destination_entity.is_alive:
                print(f"Removing dead entity from tile {new_tile_x}, {new_tile_y}")
                # Remove dead entity and allow movement to its tile
                destination_tile.entity = None
                if destination_entity in self.entities:
                    self.entities.remove(destination_entity)
                return self.move_entity(entity, new_tile_x, new_tile_y)  # Retry move after removing

            elif isinstance(entity, Character) and isinstance(destination_entity, Monster):
                if entity.can_do_action(ATTACK_ACTION_COST):
                    entity.spend_action_points(ATTACK_ACTION_COST)

                    print(f"Combat initiated")
                    # Player attacks monster
                    damage = destination_entity.combat_stats.take_damage(entity.combat_stats.damage)
                    print(f"Damage dealt: {damage}")
                    print(f"Monster HP after damage: {destination_entity.combat_stats.current_hp}")
                    print(f"Monster alive after damage: {destination_entity.is_alive}")

                    # Start combat animation
                    if hasattr(self, 'combat_animation'):
                        self.combat_animation.start_attack(entity, destination_entity)

                    # If monster died from this attack, remove it
                    if not destination_entity.is_alive:
                        print(f"Monster died, removing from game")
                        destination_tile.entity = None
                        if destination_entity in self.entities:
                            self.entities.remove(destination_entity)
                    return True
            return False  # Can't move into occupied tile
        if isinstance(entity, Character) and not entity.can_do_action(MOVE_ACTION_COST):
            return False
        # Move to empty tile
        old_tile_x = entity.x // self.tile_size
        old_tile_y = entity.y // self.tile_size

        # Update tiles
        self.tiles[old_tile_y][old_tile_x].entity = None
        destination_tile.entity = entity

        # Update entity position
        entity.x = new_tile_x * self.tile_size
        entity.y = new_tile_y * self.tile_size
        if isinstance(entity, Character):
            entity.spend_action_points(MOVE_ACTION_COST)
        return True


    def get_random_empty_position(self):
        """Find a random empty tile position"""
        while True:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            
            # Check if tile exists and is empty
            if (0 <= y < len(self.tiles) and 
                0 <= x < len(self.tiles[y]) and 
                self.tiles[y][x] is not None and 
                self.tiles[y][x].entity is None):
                return (x, y)

    def add_entity(self, entity, tile_x, tile_y):
        # Check if position is within bounds and tile is empty
        if (0 <= tile_x < self.width and
                0 <= tile_y < self.height and
                self.tiles[tile_y][tile_x].entity is None):
            # Place entity
            self.tiles[tile_y][tile_x].entity = entity
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
                placed = self.add_entity(entity, x, y)

    def handle_monster_turn(self, monster):
        if not monster.is_alive:
            return False

        # Get positions and calculate distance
        monster_tile_x = monster.x // self.tile_size
        monster_tile_y = monster.y // self.tile_size
        player = self.state_manager.player
        player_tile_x = player.x // self.tile_size
        player_tile_y = player.y // self.tile_size

        dx = player_tile_x - monster_tile_x
        dy = player_tile_y - monster_tile_y
        distance = abs(dx) + abs(dy)

        # DECISION MAKING PHASE
        decision = self.decide_monster_action(monster, distance)

        # ACTION EXECUTION PHASE
        if decision == "flee":
            return self.execute_flee(monster, dx, dy, monster_tile_x, monster_tile_y)
        elif decision == "attack":
            return self.execute_attack(monster, player)
        elif decision == "approach":
            return self.execute_approach(monster, dx, dy, monster_tile_x, monster_tile_y)

        return False


    def decide_monster_action(self, monster, distance):
        """Decide what action the monster should take based on its personality and situation"""
        # Check if player is too far
        if distance > MONSTER_AGGRO_RANGE:
            print('small aggro distance')
            return "none"

        # Get monster's current state
        health_percentage = monster.health / monster.max_health

        # Should we flee?
        if health_percentage < MONSTER_FLEE_HEALTH:
            # Brave monsters might still fight
            if random.random() > monster.bravery:
                print('flee')
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
        if not monster.can_do_action(ATTACK_ACTION_COST):
            return False

        monster.spend_action_points(ATTACK_ACTION_COST)
        damage = monster.attack(player)

        # Calculate angle to face target
        dx = player.x - monster.x
        dy = player.y - monster.y
        angle = math.degrees(math.atan2(-dy, dx)) + 90
        monster.base_rotation = angle

        if hasattr(self, 'combat_animation'):
            return self.combat_animation.start_attack(monster, player)
        return True

    def execute_approach(self, monster, dx, dy, monster_tile_x, monster_tile_y):
        """Execute approach movement"""
        if not monster.can_do_action(MOVE_ACTION_COST):
            return False

        # Calculate new position
        move_x = monster_tile_x + (1 if dx > 0 else -1) if abs(dx) > abs(dy) else monster_tile_x
        move_y = monster_tile_y + (1 if dy > 0 else -1) if abs(dx) <= abs(dy) else monster_tile_y

        # Calculate facing direction
        if abs(dx) > abs(dy):
            monster.base_rotation = DIRECTION_RIGHT if dx > 0 else DIRECTION_LEFT
        else:
            monster.base_rotation = DIRECTION_DOWN if dy > 0 else DIRECTION_UP

        monster.spend_action_points(MOVE_ACTION_COST)
        return self.move_entity(monster, move_x, move_y)

    def execute_flee(self, monster, dx, dy, monster_tile_x, monster_tile_y):
        """Execute fleeing movement"""
        if not monster.can_do_action(MOVE_ACTION_COST):
            return False

        # Calculate new position (away from player)
        move_x = monster_tile_x + (-1 if dx > 0 else 1) if abs(dx) > abs(dy) else monster_tile_x
        move_y = monster_tile_y + (-1 if dy > 0 else 1) if abs(dx) <= abs(dy) else monster_tile_y

        # Calculate facing direction (opposite to player)
        if abs(dx) > abs(dy):
            monster.base_rotation = DIRECTION_LEFT if dx > 0 else DIRECTION_RIGHT
        else:
            monster.base_rotation = DIRECTION_UP if dy > 0 else DIRECTION_DOWN

        monster.spend_action_points(MOVE_ACTION_COST)
        return self.move_entity(monster, move_x, move_y)