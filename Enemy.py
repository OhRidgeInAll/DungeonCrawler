from ursina import *
from constants import *
from Actor import Actor

class Enemy(Actor):
    def __init__(self, grid_x, grid_y):
        super().__init__(
            model='quad',
            color=color.red,
            scale=(TILE_SIZE * 0.8, TILE_SIZE * 0.8),
            position = grid_to_world(grid_x, grid_y),
            team = 1
        )
        self.grid_x = grid_x  # Integer grid column
        self.grid_y = grid_y  # Integer grid row
        self.move_cooldown = 1.0
        self.attack_power = 8
        #self.on_death = Death Behaviour Goes Here