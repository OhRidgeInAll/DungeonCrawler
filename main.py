from ursina import *
from GameBoard import *
from constants import *
from GameUI import CombatUI
from Pathfinding import MouseController

#This creates a window
app = Ursina()

#Create our gameboard (A matrix of GameTiles)
game = GameBoard()
ui = CombatUI()
mouse_controller = MouseController(game)

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
    
    # Right mouse button for pathfinding movement
    elif key == 'right mouse down':
        # Get world position from mouse
        if mouse.world_point:
            mouse_controller.on_right_click(mouse.world_point)

def update():
    # Update game state
    game.update()
    mouse_controller.update()
    
    # Tile highlighting
    if mouse.hovered_entity and isinstance(mouse.hovered_entity, GameTile):
        mouse.hovered_entity.highlight()
        for tile in game.tiles:
            if tile != mouse.hovered_entity:
                tile.remove_highlight()
    
    # Update UI with vision info
    ui.update(game.player)
    
    # Smooth camera following
    camera_target = Vec3(game.player.position.x, game.player.position.y, -20)
    camera.position = lerp(camera.position, camera_target, time.dt * 5)
    
    # Visualize vision radius (optional debugging)
    # visualize_vision_radius()

# Optional helper for debugging vision
def visualize_vision_radius():
    """Visualize player's vision radius for debugging."""
    # Clear previous vision indicators
    for entity in scene.entities:
        if hasattr(entity, '_vision_indicator'):
            destroy(entity)
    
    # Show player vision range
    player_x, player_y = game.player.grid_position
    vision_range = 5  # Default vision range
    
    for dx in range(-vision_range, vision_range + 1):
        for dy in range(-vision_range, vision_range + 1):
            if abs(dx) + abs(dy) <= vision_range:  # Diamond shape (Manhattan distance)
                tx, ty = player_x + dx, player_y + dy
                if game.is_position_in_dungeon(tx, ty):
                    world_pos = grid_to_world(tx, ty)
                    indicator = Entity(
                        model='quad',
                        position=(world_pos.x, world_pos.y, -0.05),
                        scale=(TILE_SIZE * 0.3, TILE_SIZE * 0.3),
                        color=color.rgba(0, 255, 0, 50),
                        _vision_indicator=True
                    )

# Run game
app.run()
