from ursina import *
from player import *
from GameTile import GameTile
from constants import *
from Obstacle import *
from Room import RoomGenerator

class GameBoard:
    def __init__(self):
        self.tiles = []
        self.obstacles = []
        self.rooms = []
        self.corridors = []
        self.enemies = []  #Placeholder for implementation
        
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
        
        # player
        self.player = Player(self)
        self.current_turn = 0
        
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

        self.turn_text = Text(
            text=f"Turn: {self.current_turn}",
            position=(-0.8, 0.45),
            scale=2,
            color=color.white
        )
    
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
