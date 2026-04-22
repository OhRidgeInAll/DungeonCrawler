from ursina import *
from player import *
from GameTile import GameTile
from constants import *
from Obstacle import *
from Room import RoomGenerator
from Enemy import Enemy

class GameBoard:
    def __init__(self):
        self.tiles = []
        self.obstacles = []
        self.rooms = []
        self.corridors = []
        self.enemies = []  # Will contain Enemy instances
        
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
        
        # enemies spawn in non starting rooms
        self._spawn_enemies()
        
        # player
        self.player = Player(self)
        self.current_turn = 0
        self.turn_in_progress = False
        self.action_queue = []
        
        # tiles (rooms + corridors) (Not obstacles)
        self.create_dungeon_tiles()
        
        # set start
        if self.rooms:
            start_room = self.rooms[0]
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

        # Turn counter moved to GameUI.py
    
    def _spawn_enemies(self):
        """Spawn enemies in non-starting rooms."""
        if len(self.rooms) < 2:
            return
            
        # Spawn 1-2 enemies per room (skip starting room)
        for room in self.rooms[1:]:  # Skip first room (starting room)
            room_tiles = list(room.get_tiles())
            room_size = len(room_tiles)
            
            # Determine how many enemies to spawn (1-2, fewer for small rooms)
            max_enemies = min(2, room_size // 15)
            if max_enemies < 1:
                max_enemies = 1
                
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
                    enemy = Enemy(tx, ty, self)
                    self.enemies.append(enemy)
                    placed += 1
                    print(f"Enemy spawned at ({tx}, {ty}) in room {room}")
                
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
        """Queue a player action for the next turn."""
        self.action_queue.append((action_type, *args))
    
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
    
    def get_room_at_position(self, x, y):
        for room in self.rooms:
            if room.is_position_in_room(x, y):
                return room
        return None
