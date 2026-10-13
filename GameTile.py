from ursina import *
from constants import *

_floor_texture = None

def _get_floor_texture():
    global _floor_texture
    if _floor_texture is None:
        _floor_texture = load_texture(TILESET_NAME)
    return _floor_texture

class GameTile(Entity):
    def __init__(self, position=(0,0,0)):
        tile_index = random.choice(FLOOR_TILE_INDICES)
        super().__init__(
            model='quad',
            #It may seem counterintuitive to make the tile slightly smaller than TILE_SIZE but we want tile borders to be visible to the player
            scale=(TILE_SIZE*0.95, TILE_SIZE*0.95),
            position=position,
            color=color.white,
            collider='box',
            texture=_get_floor_texture(),
            texture_scale=(1/TILESET_COLS, 1/TILESET_ROWS),
            texture_offset=tile_uv(tile_index)
        )
        self.original_color = color.white
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