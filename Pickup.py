from ursina import *
from constants import *

class Pickup(Entity):
    """Robot part drops, analog to equipment drops in other games"""
    def __init__(self, grid_x, grid_y, part):
        world_pos = grid_to_world(grid_x, grid_y)
        super().__init__(
            model='cube',
            scale=(TILE_SIZE * 0.35, TILE_SIZE * 0.35, TILE_SIZE * 0.35),
            color=color.azure,
            position=(world_pos.x, world_pos.y, -0.13)
        )
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.part = part
        self.animate('rotation_y', 360, duration=3, loop=True, curve=curve.linear)
