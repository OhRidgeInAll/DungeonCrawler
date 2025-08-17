from ursina import *
from player import *
from GameTile import GameTile
from constants import *

class GameBoard:
    def __init__(self):
        self.tiles = []
        self.obstacles = []
        self.player = Player()
        self.current_turn = 0

        self.create_grid()

        self.turn_text = Text(
            text=f"Turn: {self.current_turn}",
            position=(-0.8, 0.45),
            scale=2,
            color=color.white
        )
    
    def create_grid(self):
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                tile = GameTile(position=(x - GRID_SIZE//2 + 0.5, y - GRID_SIZE//2 + 0.5, 0))
                self.tiles.append(tile)

        self.player.move_to_grid_position(GRID_SIZE//2, GRID_SIZE//2)  # Start player in the center
