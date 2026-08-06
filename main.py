import sys
from pathlib import Path

from ursina import *
from ursina import application

if getattr(sys, 'frozen', False):
    _base = Path(sys._MEIPASS)
    application.asset_folder = _base
    application.textures_compressed_folder = _base / 'textures_compressed'
    application.models_compressed_folder = _base / 'models_compressed'
from GameBoard import *
from constants import *
from GameUI import CombatUI
from Pathfinding import MouseController

# Pause menu class - WITH FIXES (reduced alpha, z-ordering)
class PauseMenu:
    def __init__(self):
        self.visible = False
        self.background = Entity(
            parent=camera.ui,
            model='quad',
            scale=(2, 2),
            color=color.rgba(0, 0, 0, 100),  # Reduced alpha for better visibility
            position=(0, 0),
            z=-1,
            enabled=False
        )
        
        self.title = Text(
            parent=camera.ui,
            text="PAUSED",
            position=(0, 0.2),
            scale=3,
            color=color.white,
            origin=(0, 0),
            enabled=False,
            z=0  # Ensure above background
        )
        
        self.resume_button = Button(
            parent=camera.ui,
            text="Resume",
            position=(0, 0),
            scale=(0.3, 0.1),
            color=color.gray,
            on_click=self.resume_game,
            enabled=False,
            z=0
        )
        
        self.quit_button = Button(
            parent=camera.ui,
            text="Quit",
            position=(0, -0.15),
            scale=(0.3, 0.1),
            color=color.gray,
            on_click=self.quit_game,
            enabled=False,
            z=0
        )
    
    def show(self):
        self.visible = True
        self.background.enabled = True
        self.title.enabled = True
        self.resume_button.enabled = True
        self.quit_button.enabled = True
    
    def hide(self):
        self.visible = False
        self.background.enabled = False
        self.title.enabled = False
        self.resume_button.enabled = False
        self.quit_button.enabled = False
    
    def resume_game(self):
        self.hide()
    
    def quit_game(self):
        application.quit()

#This creates a window
app = Ursina()
print("Ursina app initialized")

DEBUG_MODE = True  # dev-only conveniences (e.g. full heal); flip off before shipping a build

#Create our gameboard (A matrix of GameTiles)
game = GameBoard()
ui = CombatUI()
mouse_controller = MouseController(game)
pause_menu = PauseMenu()

print("Game started!")

_last_diag_turn = -1
DIAG_TURN_INTERVAL = 25  # auto-print diagnostics every N turns
_last_seen_floor = 0  # 0 so the very first update() call builds the initial floor's minimap

def print_diagnostics(tag="[DEBUG]"):
    """Live entity/sequence counts, to track down long-session lag -
     gets real numbers since leak couldn't be found.
     Maybe I'm losing it lmao"""
    print(f"{tag} turn={game.current_turn} floor={game.floor_number} "
          f"scene.entities={len(scene.entities)} application.sequences={len(application.sequences)} "
          f"tiles={len(game.tiles)} obstacles={len(game.obstacle_spawner.obstacles)} "
          f"enemies={len(game.enemies)} pickups={len(game.pickups)}")

def input(key):
    if game.player_defeated:
        return  # player entity is destroyed - stop here rather than crash on it

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
    
    # ESC for pause menu
    elif key == 'escape':
        if pause_menu.visible:
            pause_menu.hide()
        else:
            pause_menu.show()

    # Number keys equip the corresponding inventory item
    elif key in ('1', '2', '3', '4', '5', '6', '7', '8', '9'):
        idx = int(key) - 1
        if idx < len(game.player.inventory):
            game.player.equip(game.player.inventory[idx])

    # DEBUG: full heal
    elif key == 'h' and DEBUG_MODE:
        game.player.health = game.player.max_health
        print(f"[DEBUG] Healed to {game.player.health}/{game.player.max_health}")

    # DEBUG: print live entity/sequence counts
    elif key == 'p' and DEBUG_MODE:
        print_diagnostics(tag="[DEBUG]")

    # Right mouse button: click-to-move via pathfinding
    elif key == 'right mouse down':
        if mouse.world_point:
            mouse_controller.on_right_click(mouse.world_point)

    # Any manual movement key cancels an in-progress auto-walk
    if key in ('w', 'a', 's', 'd'):
        mouse_controller.stop()

def update():
    global _last_diag_turn, _last_seen_floor

    if game.player_defeated:
        return  # player entity is destroyed - stop here rather than crash on it

    # Update game state
    game.update()
    mouse_controller.update()

    if DEBUG_MODE and game.current_turn != _last_diag_turn and game.current_turn % DIAG_TURN_INTERVAL == 0:
        _last_diag_turn = game.current_turn
        print_diagnostics(tag="[DIAG]")

    if game.floor_number != _last_seen_floor:
        _last_seen_floor = game.floor_number
        ui.rebuild_minimap(game.rooms, game.room_generator.get_bounds())

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