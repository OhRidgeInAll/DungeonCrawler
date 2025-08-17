from ursina import *
from constants import *

class GameTile(Entity):
    def __init__(self, position=(0,0,0)):
        super().__init__(
            model='quad',
            #It may seem counterintuitive to make the tile slightly smaller than TILE_SIZE but we want tile borders to be visible to the player
            scale=(TILE_SIZE*0.95, TILE_SIZE*0.95),
            position=position,
            color=GRID_COLOR,
            collider='box',
            texture='white_cube',
            texture_scale=(1,1)
        )
        self.original_color = GRID_COLOR
        self.highlight_color = color.lime
        self.border = Entity(
            parent=self,
            model=Quad(segments=0, mode='line'),
            scale=(1.05, 1.05),
            color=color.black,
            z=-0.01
        )
    
    def highlight(self):
        self.color = self.highlight_color
    
    def remove_highlight(self):
        self.color = self.original_color