from ursina import *
from player import *
from GameTile import GameTile
from constants import *
from Obstacle import *
from Room import RoomGenerator
from Enemy import spawn_random_enemy
from Staircase import Staircase
from Pickup import Pickup
from Part import roll_loot
from LineOfSight import has_line_of_sight

class GameBoard:
    def __init__(self):
        self.floor_number = 1
        self.tiles = []
        self.obstacles = []
        self.rooms = []
        self.corridors = []
        self.enemies = []  # Will contain Enemy instances
        self.pickups = []  # Robot drops
        self.staircase = None
        self.current_turn = 0
        self.turn_in_progress = False
        self.action_queue = []
        self.player_defeated = False

        self.player = None
        self._generate_floor()

    @property
    def difficulty(self):
        """Scales with floor_number so it can never go stale; consumers (enemy
        spawning, loot chance) each decide how strongly to react to it."""
        return self.floor_number

    def _generate_floor(self):
        """Generate the dungeon layout, obstacles, enemies, and staircase for the current floor."""
        # Rooms
        self.room_generator = RoomGenerator(max_grid_size=20)
        self.rooms, self.corridors = self.room_generator.generate(num_rooms=5)

        # bounds
        min_x, min_y, max_x, max_y = self.room_generator.get_bounds()
        set_dungeon_bounds(min_x, min_y, max_x, max_y)

        # obstacles
        dungeon_width = max_x - min_x + 1
        dungeon_height = max_y - min_y + 1
        self.obstacle_spawner = ObstacleSpawner(max(dungeon_width, dungeon_height))

        self._generate_room_obstacles()

        # enemies spawn in normal rooms only (not the start or exit room)
        self._spawn_enemies()

        # player persists across floors; only created once
        if self.player is None:
            self.player = Player(self)

        # tiles (rooms + corridors) (Not obstacles)
        self.create_dungeon_tiles()

        self._place_staircase()
        self._place_player_in_start_room()

    def advance_floor(self):
        """Tear down the current floor and generate the next one, keeping the player and their progress."""
        self.floor_number += 1
        self._clear_floor_entities()
        self._generate_floor()
        print(f"Advanced to floor {self.floor_number}")

    def _clear_floor_entities(self):
        """Destroy all entities belonging to the current floor before regenerating."""
        for tile in self.tiles:
            destroy(tile)
        self.tiles = []

        for obstacle in self.obstacle_spawner.obstacles:
            destroy(obstacle)

        for enemy in list(self.enemies):
            destroy(enemy)
        self.enemies = []

        for pickup in self.pickups:
            destroy(pickup)
        self.pickups = []

        if self.staircase:
            destroy(self.staircase)
            self.staircase = None

        self.action_queue = []
        self.turn_in_progress = False

    def _get_room_by_role(self, role):
        for room in self.rooms:
            if room.role == role:
                return room
        return None

    def _place_player_in_start_room(self):
        start_room = self._get_room_by_role("start")
        if not start_room:
            return

        start_x, start_y = start_room.get_center()
        # Ensure player pos valid
        # Try center first, if blocked try nearby positions
        positions_to_try = [
            (start_x, start_y),
            (start_x + 1, start_y),
            (start_x - 1, start_y),
            (start_x, start_y + 1),
            (start_x, start_y - 1)
        ]

        placed = False
        for px, py in positions_to_try:
            if (px, py) in start_room.get_tiles() and not self.is_position_blocked(px, py):
                # Set player position directly
                self.player.grid_x = px
                self.player.grid_y = py
                self.player.position = grid_to_world(px, py)
                self.player.target_position = self.player.position
                self.player.is_moving = False
                print(f"Player placed at grid position: ({px}, {py})")
                placed = True
                break

        if not placed:
            # Fallback to any position in room
            for tx, ty in start_room.get_tiles():
                if not self.is_position_blocked(tx, ty):
                    self.player.grid_x = tx
                    self.player.grid_y = ty
                    self.player.position = grid_to_world(tx, ty)
                    self.player.target_position = self.player.position
                    self.player.is_moving = False
                    print(f"Player placed at fallback grid position: ({tx}, {ty})")
                    break

    def _place_staircase(self):
        exit_room = self._get_room_by_role("exit")
        if not exit_room:
            return

        exit_x, exit_y = exit_room.get_center()
        positions_to_try = [
            (exit_x, exit_y),
            (exit_x + 1, exit_y),
            (exit_x - 1, exit_y),
            (exit_x, exit_y + 1),
            (exit_x, exit_y - 1)
        ]

        for sx, sy in positions_to_try:
            if (sx, sy) in exit_room.get_tiles() and not self.is_position_blocked(sx, sy):
                self.staircase = Staircase(sx, sy)
                return

        # Fallback to any position in the exit room
        for tx, ty in exit_room.get_tiles():
            if not self.is_position_blocked(tx, ty):
                self.staircase = Staircase(tx, ty)
                return

    def spawn_loot_drop(self, archetype_id, grid_x, grid_y):
        """Roll a chance to drop an enemy part where an enemy died."""
        part = roll_loot(archetype_id, difficulty=self.difficulty)
        if part is None:
            return
        self.pickups.append(Pickup(grid_x, grid_y, part))
        print(f"{part.name} dropped at ({grid_x}, {grid_y})")

    def _spawn_enemies(self):
        """Spawn enemies in normal rooms (skips the start room and the exit room)."""
        spawn_rooms = [room for room in self.rooms if room.role == "normal"]
        if not spawn_rooms:
            return

        difficulty = self.difficulty

        # Spawn 1-2 enemies per room, nudged up slightly on deeper floors
        for room in spawn_rooms:
            room_tiles = list(room.get_tiles())
            room_size = len(room_tiles)

            # Determine how many enemies to spawn (1-2, fewer for small rooms)
            max_enemies = min(2, room_size // 15)
            if max_enemies < 1:
                max_enemies = 1
            max_enemies = min(4, max_enemies + int((difficulty - 1) // 5))

            num_enemies = random.randint(1, max_enemies)
            placed = 0
            attempts = 0

            while placed < num_enemies and attempts < 50:
                tx, ty = random.choice(room_tiles)

                # Don't spawn on doors or obstacles
                if (tx, ty) in room.doors or self.is_position_blocked(tx, ty):
                    attempts += 1
                    continue

                position_occupied = False
                for enemy in self.enemies:
                    if enemy.grid_x == tx and enemy.grid_y == ty:
                        position_occupied = True
                        break

                if not position_occupied:
                    enemy = spawn_random_enemy(tx, ty, self, difficulty=difficulty)
                    self.enemies.append(enemy)
                    placed += 1
                    print(f"{enemy.archetype_id} spawned at ({tx}, {ty}) in room {room}")

                attempts += 1
    
    def process_turn(self):
        """Process a complete turn: player action, then enemy actions."""
        if self.turn_in_progress:
            return
            
        self.turn_in_progress = True
        
        self.current_turn += 1
        
        # Reset player's attack flag at start of turn
        if hasattr(self.player, 'has_attacked_this_turn'):
            self.player.has_attacked_this_turn = False
        
        # Process queued player action first
        if self.action_queue:
            action = self.action_queue.pop(0)
            action_type, *args = action
            
            if action_type == 'move':
                x, y = args
                # Check if there's an enemy at the target position
                enemy_at_target = self.get_enemy_at_position(x, y)
                if enemy_at_target:
                    # Attack the enemy instead of moving
                    self.player.try_attack_enemy_at(x, y)
                else:
                    # No enemy, proceed with movement
                    self.player.move_to_grid_position(x, y)
            # Could add other action types (attack, etc.)
        
        # Wait for player movement to complete before enemies move
        invoke(self._process_enemy_turns, delay=0.1)
    
    def _process_enemy_turns(self):
        """Process all enemy turns after player action."""
        # Let enemies take their turns
        for enemy in self.enemies:
            enemy.take_turn()
        
        self.turn_in_progress = False
    
    def queue_player_action(self, action_type, *args):
        """Queue the next player action, replacing any not-yet-processed one so a
        key pressed while a turn is still resolving can't go stale and fire later."""
        self.action_queue = [(action_type, *args)]
    
    def update(self):
        """Update game state - called every frame."""
        # Check if all entities are done moving
        all_done = not self.player.is_moving
        for enemy in self.enemies:
            if enemy.is_moving:
                all_done = False
                break
        
        #Turn complete if all done (wait for anims/actions to finish)
        if self.turn_in_progress and all_done:
            self.turn_in_progress = False

        # Pick up any parts the player has walked onto
        if all_done:
            for pickup in list(self.pickups):
                if pickup.grid_x == self.player.grid_x and pickup.grid_y == self.player.grid_y:
                    self.player.inventory.append(pickup.part)
                    print(f"Picked up {pickup.part.name}")
                    self.pickups.remove(pickup)
                    destroy(pickup)

        # Check for floor transition once the player has settled on a tile
        if (self.staircase and all_done and
                self.player.grid_x == self.staircase.grid_x and
                self.player.grid_y == self.staircase.grid_y):
            self.advance_floor()
    
    def create_dungeon_tiles(self):
        """Create tiles for all rooms and corridors in the dungeon."""
        all_tiles = self.room_generator.get_all_tiles()
        
        for tile_x, tile_y in all_tiles:
            world_pos = grid_to_world(tile_x, tile_y)
            # Adjust(tiles are positioned at their center)
            tile = GameTile(position=(world_pos.x, world_pos.y, 0))
            self.tiles.append(tile)
    
    def _generate_room_obstacles(self):
        """Generate obstacles within rooms using room-specific arrangements."""
        for room in self.rooms:
            # Generate 1-3 obstacles per room (fewer for smaller rooms)
            room_tiles = room.get_tiles()
            room_size = len(room_tiles)
            max_obstacles = min(3, room_size // 8)  # Approximate density
            
            if max_obstacles > 0:
                num_obstacles = random.randint(1, max_obstacles)
                placed = 0
                attempts = 0
                
                while placed < num_obstacles and attempts < 50:
                    tile_x, tile_y = random.choice(list(room_tiles))
                    
                    # Don't place on doors
                    if (tile_x, tile_y) in room.doors:
                        attempts += 1
                        continue
                    
                    if self.obstacle_spawner.add_obstacle(tile_x, tile_y):
                        placed += 1
                    attempts += 1
    
    def is_position_blocked(self, x, y):
        return self.obstacle_spawner.is_position_blocked(x, y)
    
    def is_position_in_dungeon(self, x, y):
        return (x, y) in self.room_generator.get_all_tiles()

    def has_line_of_sight(self, x0, y0, x1, y1):
        """Whether sight is clear between two grid cells - blocked by void/non-dungeon
        cells (walls) and by Obstacles. Single call site for LOS so consumers (attack
        legality, enemy vision, future fog-of-war) never reimplement this predicate."""
        blocks_los = lambda x, y: not self.is_position_in_dungeon(x, y) or self.is_position_blocked(x, y)
        return has_line_of_sight(x0, y0, x1, y1, blocks_los)
    
    def get_room_at_position(self, x, y):
        for room in self.rooms:
            if room.is_position_in_room(x, y):
                return room
        return None
    
    def get_enemy_at_position(self, x, y):
        """Get enemy at specified grid position, or None if no enemy there."""
        for enemy in self.enemies:
            if enemy.grid_x == x and enemy.grid_y == y:
                return enemy
        return None
