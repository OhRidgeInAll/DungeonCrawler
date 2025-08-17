from ursina import *

class GameTile(Entity):
    def __init__(self, position=(0,0,0)):
        super().__init__(
            model='quad',
            scale=(TILE_SIZE, TILE_SIZE),
            position=position,
            color=GRID_COLOR,
            collider='box'
        )