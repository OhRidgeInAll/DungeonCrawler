from ursina import *

#Game Constants
#Determined by dungeon generation now
DEFAULT_GRID_SIZE = 8
TILE_SIZE = 1
GRID_COLOR = color.gray
ATTACK_RANGE = 1.5 #Grid Units
ATTACK_COOLDOWN = 0.5 #seconds

# set by generator
DUNGEON_BOUNDS = None  # (min_x, min_y, max_x, max_y)

def set_dungeon_bounds(min_x, min_y, max_x, max_y):
    """Set the global dungeon bounds for coordinate conversion."""
    global DUNGEON_BOUNDS
    DUNGEON_BOUNDS = (min_x, min_y, max_x, max_y)

def get_dungeon_center():
    """Get the center of the dungeon bounds."""
    if DUNGEON_BOUNDS is None:
        return (DEFAULT_GRID_SIZE // 2, DEFAULT_GRID_SIZE // 2)
    min_x, min_y, max_x, max_y = DUNGEON_BOUNDS
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    return (center_x, center_y)

def get_dungeon_size():
    """Get width and height of dungeon bounds."""
    if DUNGEON_BOUNDS is None:
        return (DEFAULT_GRID_SIZE, DEFAULT_GRID_SIZE)
    min_x, min_y, max_x, max_y = DUNGEON_BOUNDS
    return (max_x - min_x + 1, max_y - min_y + 1)

def grid_to_world(grid_x, grid_y, grid_size=None):
    """
    If DUNGEON_BOUNDS is set, uses dungeon-relative positioning.
    Otherwise uses default grid size centered at origin.
    """
    if DUNGEON_BOUNDS is not None:
        min_x, min_y, max_x, max_y = DUNGEON_BOUNDS
        dungeon_width = max_x - min_x + 1
        dungeon_height = max_y - min_y + 1
        # Center the dungeon at world origin
        world_x = grid_x - min_x - (dungeon_width - 1)/2
        world_y = grid_y - min_y - (dungeon_height - 1)/2
    else:
        grid_size = grid_size or DEFAULT_GRID_SIZE
        world_x = grid_x - (grid_size - 1)/2
        world_y = grid_y - (grid_size - 1)/2
    
    return Vec3(world_x, world_y, -0.1)  # Z position above grid

def world_to_grid(world_pos, grid_size=None):
    """Convert world position back to grid coordinates."""
    if DUNGEON_BOUNDS is not None:
        min_x, min_y, max_x, max_y = DUNGEON_BOUNDS
        dungeon_width = max_x - min_x + 1
        dungeon_height = max_y - min_y + 1
        grid_x = int(round(world_pos.x + (dungeon_width - 1)/2 + min_x))
        grid_y = int(round(world_pos.y + (dungeon_height - 1)/2 + min_y))
    else:
        grid_size = grid_size or DEFAULT_GRID_SIZE
        grid_x = int(round(world_pos.x + (grid_size - 1)/2))
        grid_y = int(round(world_pos.y + (grid_size - 1)/2))
    
    return (grid_x, grid_y)
