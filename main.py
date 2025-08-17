from ursina import *
from GameBoard import *
from constants import *

#This creates a window
app = Ursina()

#Create our gameboard (A matrix of GameTiles)
game = GameBoard()

def input(key):
    if not game.player.is_moving:
        x, y = game.player.grid_position

        if key == 'w':
            game.player.move_to_grid_position(x, y + 1)
        elif key == 's':
            game.player.move_to_grid_position(x, y - 1)
        elif key == 'a':
            game.player.move_to_grid_position(x - 1, y)
        elif key == 'd':
            game.player.move_to_grid_position(x + 1, y)
    
def update():
    if mouse.hovered_entity and isinstance(mouse.hovered_entity, GameTile):
        mouse.hovered_entity.highlight()
        for tile in game.tiles:
            if tile != mouse.hovered_entity:
                tile.remove_highlight()



#run game
app.run()