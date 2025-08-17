from ursina import *
from constants import *

class Player(Entity):
    def __init__(self):
        # We're overriding the Entity class to create a Player class
        super().__init__(
            model='quad',
            #Our game is built around the tiles, our character should be slightly smaller than a tile
            scale=(TILE_SIZE*0.8, TILE_SIZE*0.8),
            color=color.azure,
            position=grid_to_world(GRID_SIZE // 2, GRID_SIZE // 2),  # Start in the center of the grid
            z=-0.1,  # Slightly above the grid
            )
        self.grid_x = GRID_SIZE//2  # Integer grid column
        self.grid_y = GRID_SIZE//2  # Integer grid row
        self.target_position = self.position
        self.move_speed = 5
        self.is_moving = False
    
    @property
    def grid_position(self):
        return (self.grid_x, self.grid_y)

    def move_to_grid_position(self, x, y):
        if not self.is_moving:
            self.grid_x = x
            self.grid_y = y
            self.target_position = grid_to_world(x, y)
            self.is_moving = True

    def update(self):
        if self.is_moving:
            self.position = lerp(self.position, self.target_position, time.dt * 10)

            if (self.position - self.target_position).length() < 0.01:
                self.position = self.target_position
                self.is_moving = False
    
