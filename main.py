from ursina import *
from GameBoard import *
from constants import *
from GameUI import CombatUI

#This creates a window
app = Ursina()

#Create our gameboard (A matrix of GameTiles)
game = GameBoard()
ui = CombatUI()

def input(key):
    # Handle movement keys - queue actions instead of immediate movement
    x, y = game.player.grid_position
    
    if key == 'w':
        game.queue_player_action('move', x, y + 1)
        game.process_turn()
    elif key == 's':
        game.queue_player_action('move', x, y - 1)
        game.process_turn()
    elif key == 'a':
        game.queue_player_action('move', x - 1, y)
        game.process_turn()
    elif key == 'd':
        game.queue_player_action('move', x + 1, y)
        game.process_turn()
    
    # Space for attack
    elif key == 'space':
        game.player.try_attack()
        game.process_turn()
    
def update():
    # Update game state
    game.update()
    
    # Tile highlighting
    if mouse.hovered_entity and isinstance(mouse.hovered_entity, GameTile):
        mouse.hovered_entity.highlight()
        for tile in game.tiles:
            if tile != mouse.hovered_entity:
                tile.remove_highlight()
    
    # Update UI
    ui.update(game.player)


#run game
app.run()
