from ursina import *

#Game Constants
GRID_SIZE = 8
TILE_SIZE = 1
GRID_COLOR = color.gray
ATTACK_RANGE = 1.5 #Grid Units
ATTACK_COOLDOWN = 0.5 #seconds

def grid_to_world(grid_x, grid_y):
    """Convert grid coordinates (0-7) to world space (-3.5 to 3.5)"""
    return Vec3(
        grid_x - (GRID_SIZE - 1)/2,  # -3.5 to 3.5
        grid_y - (GRID_SIZE - 1)/2,
        -0.1  # Z position above grid
    )

def world_to_grid(world_pos):
    """Convert world position back to grid coordinates"""
    return (
    int(round(world_pos.x + (GRID_SIZE - 1)/2)),
    int(round(world_pos.y + (GRID_SIZE - 1)/2))
    )