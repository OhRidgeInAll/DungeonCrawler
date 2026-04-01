from ursina import *
from constants import *
import random
from typing import List, Tuple, Set

class Room:
    
    def __init__(self, x: int, y: int, width: int, height: int, room_type: str = "rectangular"):
        """
        Rooms are bottom left oriented, as in their position (x, y) is the bottom-left corner of the room.
        room type includes rectangular, large, and L-shaped.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.room_type = room_type
        
        # Connection points
        self.doors: List[Tuple[int, int]] = []
        
        # L-room negative
        if room_type == "L-shaped":
            #width x height of missing corner
            self.l_corner = random.choice(["top-right", "top-left", "bottom-right", "bottom-left"])
        else:
            self.l_corner = None
    
    def get_bounds(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.x + self.width - 1, self.y + self.height - 1)
    
    def get_tiles(self) -> Set[Tuple[int, int]]:
        tiles = set()
        min_x, min_y, max_x, max_y = self.get_bounds()
        
        if self.room_type == "L-shaped":
            for tx in range(min_x, max_x + 1):
                for ty in range(min_y, max_y + 1):
                    # Check
                    if self.l_corner == "top-right" and tx == max_x and ty == max_y:
                        continue
                    elif self.l_corner == "top-left" and tx == min_x and ty == max_y:
                        continue
                    elif self.l_corner == "bottom-right" and tx == max_x and ty == min_y:
                        continue
                    elif self.l_corner == "bottom-left" and tx == min_x and ty == min_y:
                        continue
                    tiles.add((tx, ty))
        else:
            # Rectangular room
            for tx in range(min_x, max_x + 1):
                for ty in range(min_y, max_y + 1):
                    tiles.add((tx, ty))
        
        return tiles
    
    def is_position_in_room(self, x: int, y: int) -> bool:
        """Check if a grid position is inside this room."""
        min_x, min_y, max_x, max_y = self.get_bounds()
        
        if not (min_x <= x <= max_x and min_y <= y <= max_y):
            return False
            
        if self.room_type == "L-shaped":
            # Check
            if self.l_corner == "top-right" and x == max_x and y == max_y:
                return False
            elif self.l_corner == "top-left" and x == min_x and y == max_y:
                return False
            elif self.l_corner == "bottom-right" and x == max_x and y == min_y:
                return False
            elif self.l_corner == "bottom-left" and x == min_x and y == min_y:
                return False
        
        return True
    
    def get_wall_positions(self) -> Set[Tuple[int, int]]:
        """Get perimeter walls (not columns)"""
        walls = set()
        min_x, min_y, max_x, max_y = self.get_bounds()
        
        for tx in range(min_x, max_x + 1):
            walls.add((tx, min_y - 1))
            walls.add((tx, max_y + 1))
        
        for ty in range(min_y, max_y + 1):
            walls.add((min_x - 1, ty))
            walls.add((max_x + 1, ty))
        
        # L wall adjust
        if self.room_type == "L-shaped":
            if self.l_corner == "top-right":
                walls.discard((max_x, max_y + 1))
                walls.discard((max_x + 1, max_y))
            elif self.l_corner == "top-left":
                walls.discard((min_x - 1, max_y))
                walls.discard((min_x, max_y + 1))
            elif self.l_corner == "bottom-right":
                walls.discard((max_x, min_y - 1))
                walls.discard((max_x + 1, min_y))
            elif self.l_corner == "bottom-left":
                walls.discard((min_x - 1, min_y))
                walls.discard((min_x, min_y - 1))
        
        return walls
    
    def add_door(self, x: int, y: int):
        if self.is_position_in_room(x, y):
            self.doors.append((x, y))
    
    def get_center(self) -> Tuple[int, int]:
        """Get a valid position inside the room (preferably near center)."""
        if self.room_type != "L-shaped":
            return (self.x + self.width // 2, self.y + self.height // 2)
        
        # For L-shaped rooms, we need to avoid the missing corner
        min_x, min_y, max_x, max_y = self.get_bounds()
        
        # Try the geometric center first
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        
        # Check if center is in the missing corner
        if self.l_corner == "top-right" and center_x == max_x and center_y == max_y:
            # Move one tile left or down
            return (center_x - 1, center_y)
        elif self.l_corner == "top-left" and center_x == min_x and center_y == max_y:
            # Move one tile right or down
            return (center_x + 1, center_y)
        elif self.l_corner == "bottom-right" and center_x == max_x and center_y == min_y:
            # Move one tile left or up
            return (center_x - 1, center_y)
        elif self.l_corner == "bottom-left" and center_x == min_x and center_y == min_y:
            # Move one tile right or up
            return (center_x + 1, center_y)
        
        # Center is valid
        return (center_x, center_y)
    
    def __str__(self):
        return f"Room({self.x},{self.y},{self.width}x{self.height},{self.room_type})"


class RoomGenerator:
    
    def __init__(self, max_grid_size: int = 20):
        self.max_grid_size = max_grid_size
        self.rooms: List[Room] = []
        self.corridors: List[List[Tuple[int, int]]] = []
        self.all_tiles: Set[Tuple[int, int]] = set()
        
        # Room templates: (width, height, type)
        self.room_templates = [
            (3, 5, "rectangular"),
            (5, 3, "rectangular"),
            (5, 5, "rectangular"),
            (7, 7, "large"),
            (5, 5, "L-shaped")
        ]
    
    def generate(self, num_rooms: int = 5) -> Tuple[List[Room], List[List[Tuple[int, int]]]]:
        """
        Generate a dungeon with specified number of rooms.
        Returns: (rooms, corridors)
        """
        self.rooms.clear()
        self.corridors.clear()
        self.all_tiles.clear()
        
        #starting room
        start_room = self._create_starting_room()
        self.rooms.append(start_room)
        self.all_tiles.update(start_room.get_tiles())
        
        for _ in range(num_rooms - 1):
            room = self._try_add_room()
            if room:
                self.rooms.append(room)
                self.all_tiles.update(room.get_tiles())
        
        self._connect_rooms()
        
        self._add_doors()
        
        return self.rooms, self.corridors
    
    def _create_starting_room(self) -> Room:
        start_x = self.max_grid_size // 2 - 2
        start_y = self.max_grid_size // 2 - 2
        return Room(start_x, start_y, 5, 5, "rectangular")
    
    def _try_add_room(self, max_attempts: int = 50) -> Room:
        for _ in range(max_attempts):
            width, height, room_type = random.choice(self.room_templates)
            
            x = random.randint(0, self.max_grid_size - width - 1)
            y = random.randint(0, self.max_grid_size - height - 1)
            
            new_room = Room(x, y, width, height, room_type)
            new_tiles = new_room.get_tiles()
            
            if not self.all_tiles.intersection(new_tiles):
                if self._check_room_distance(new_room):
                    return new_room
        
        return None
    
    def _check_room_distance(self, room: Room, min_distance: int = 2) -> bool:
        #Room Space Check
        room_tiles = room.get_tiles()
        
        for existing_room in self.rooms:
            existing_tiles = existing_room.get_tiles()
            # Manhattan dist
            for tx1, ty1 in room_tiles:
                for tx2, ty2 in existing_tiles:
                    if abs(tx1 - tx2) + abs(ty1 - ty2) < min_distance:
                        return False
        
        return True
    
    def _connect_rooms(self):
        """Connect all rooms with corridors using minimum spanning tree approach."""
        if len(self.rooms) < 2:
            return
        
        room_centers = [room.get_center() for room in self.rooms]
        
        for i in range(len(self.rooms) - 1):
            start = room_centers[i]
            end = room_centers[i + 1]
            corridor = self._create_corridor(start, end)
            self.corridors.append(corridor)
            self.all_tiles.update(corridor)
    
    def _create_corridor(self, start: Tuple[int, int], end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Create an L-shaped corridor between two points."""
        corridor = []
        sx, sy = start
        ex, ey = end
        
        step_x = 1 if ex > sx else -1
        for x in range(sx, ex + step_x, step_x):
            corridor.append((x, sy))
        
        step_y = 1 if ey > sy else -1
        for y in range(sy, ey + step_y, step_y):
            corridor.append((ex, y))
        
        if (ex, sy) in corridor:
            corridor.remove((ex, sy))
        
        return corridor
    
    def _add_doors(self):
        for corridor in self.corridors:
            for x, y in corridor:
                # Check tile adjacent toroom wall
                for room in self.rooms:
                    if room.is_position_in_room(x, y):
                        continue
                    
                    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                        nx, ny = x + dx, y + dy
                        if room.is_position_in_room(nx, ny):
                            room.add_door(nx, ny)
    
    def get_all_tiles(self) -> Set[Tuple[int, int]]:
        return self.all_tiles
    
    def get_bounds(self) -> Tuple[int, int, int, int]:
        if not self.all_tiles:
            return (0, 0, 0, 0)
        
        min_x = min(t[0] for t in self.all_tiles)
        min_y = min(t[1] for t in self.all_tiles)
        max_x = max(t[0] for t in self.all_tiles)
        max_y = max(t[1] for t in self.all_tiles)
        
        return (min_x, min_y, max_x, max_y)