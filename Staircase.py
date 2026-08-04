from ursina import *
from constants import *

class Staircase(Entity):
    """Marks the exit room's tile the player must reach to advance to the next floor. Likely a staircase or elevator"""
    def __init__(self, grid_x, grid_y):
        world_pos = grid_to_world(grid_x, grid_y)
        super().__init__(
            model='quad',
            scale=(TILE_SIZE * 0.7, TILE_SIZE * 0.7),
            color=color.cyan,
            position=(world_pos.x, world_pos.y, -0.12)
        )
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.animate('rotation_z', 360, duration=2, loop=True, curve=curve.linear)
