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
from GameUI import CombatUI, InventoryScreen
from Pathfinding import MouseController

# Pause menu class - WITH FIXES (reduced alpha, z-ordering)
class PauseMenu:
    def __init__(self, on_open_inventory, on_quit_to_title):
        self.visible = False
        self.background = Entity(
            parent=camera.ui,
            model='quad',
            scale=(2, 2),
            color=color.rgba32(0, 0, 0, 100),  # Reduced alpha for better visibility
            position=(0, 0),
            z=1,  # camera.ui renders LOWER z in front - this must stay behind title/buttons at z=0
            enabled=False
        )

        self.title = Text(
            parent=camera.ui,
            text="PAUSED",
            position=(0, 0.3),
            scale=3,
            color=color.white,
            origin=(0, 0),
            enabled=False,
            z=0  # Ensure above background
        )

        self.resume_button = Button(
            parent=camera.ui,
            text="Resume",
            position=(0, 0.1),
            scale=(0.3, 0.1),
            color=color.gray,
            on_click=self.resume_game,
            enabled=False,
            z=0
        )

        self.inventory_button = Button(
            parent=camera.ui,
            text="Inventory",
            position=(0, -0.05),
            scale=(0.3, 0.1),
            color=color.gray,
            on_click=on_open_inventory,
            enabled=False,
            z=0
        )

        self.quit_button = Button(
            parent=camera.ui,
            text="Quit to Title",
            position=(0, -0.2),
            scale=(0.3, 0.1),
            color=color.gray,
            on_click=on_quit_to_title,
            enabled=False,
            z=0
        )

    def show(self):
        self.visible = True
        self.background.enabled = True
        self.title.enabled = True
        self.resume_button.enabled = True
        self.inventory_button.enabled = True
        self.quit_button.enabled = True

    def hide(self):
        self.visible = False
        self.background.enabled = False
        self.title.enabled = False
        self.resume_button.enabled = False
        self.inventory_button.enabled = False
        self.quit_button.enabled = False

    def resume_game(self):
        resume_from_pause()


class MainMenu:
    """Fully opaque -
    covers any leftover HUD from a previous session also hides combatuii, hopefully clean."""

    def __init__(self, on_new_game, on_quit):
        self.visible = True
        self.background = Entity(
            parent=camera.ui,
            model='quad',
            scale=(2, 2),
            color=color.rgba32(15, 15, 25),
            position=(0, 0),
            z=1  # you already know: z-fighting fix
        )
        self.title = Text(
            parent=camera.ui,
            text="ROBOT ROGUELIKE",
            position=(0, 0.25),
            scale=3,
            color=color.white,
            origin=(0, 0),
            z=0
        )
        self.new_game_button = Button(
            parent=camera.ui,
            text="New Game",
            position=(0, 0),
            scale=(0.3, 0.1),
            color=color.gray,
            on_click=on_new_game,
            z=0
        )
        self.quit_button = Button(
            parent=camera.ui,
            text="Quit",
            position=(0, -0.15),
            scale=(0.3, 0.1),
            color=color.gray,
            on_click=on_quit,
            z=0
        )

    def show(self):
        self.visible = True
        self.background.enabled = True
        self.title.enabled = True
        self.new_game_button.enabled = True
        self.quit_button.enabled = True

    def hide(self):
        self.visible = False
        self.background.enabled = False
        self.title.enabled = False
        self.new_game_button.enabled = False
        self.quit_button.enabled = False


class GameOverScreen:
    def __init__(self, on_return_to_title):
        self.visible = False
        self.background = Entity(
            parent=camera.ui,
            model='quad',
            scale=(2, 2),
            color=color.rgba32(0, 0, 0, 200),
            position=(0, 0),
            z=1,  # Who fixes the z-fighters?
            enabled=False
        )
        self.title = Text(
            parent=camera.ui,
            text="GAME OVER",
            position=(0, 0.15),
            scale=4,
            color=color.red,
            origin=(0, 0),
            enabled=False,
            z=0
        )
        self.subtitle = Text(
            parent=camera.ui,
            text="",
            position=(0, 0),
            scale=1.5,
            color=color.white,
            origin=(0, 0),
            enabled=False,
            z=0
        )
        self.return_button = Button(
            parent=camera.ui,
            text="Return to Title",
            position=(0, -0.15),
            scale=(0.35, 0.1),
            color=color.gray,
            on_click=on_return_to_title,
            enabled=False,
            z=0
        )

    def show(self, floor_reached=None, turns_survived=None):
        self.visible = True
        if floor_reached is not None:
            self.subtitle.text = f"Reached floor {floor_reached} in {turns_survived} turns"
        self.background.enabled = True
        self.title.enabled = True
        self.subtitle.enabled = True
        self.return_button.enabled = True

    def hide(self):
        self.visible = False
        self.background.enabled = False
        self.title.enabled = False
        self.subtitle.enabled = False
        self.return_button.enabled = False

#This creates a window
app = Ursina()
print("Ursina app initialized")

DEBUG_MODE = True  # dev-only conveniences (e.g. full heal); flip off before shipping a build

# Game state: "menu" (no game object exists yet), "playing", "paused", or "game_over".
# Introduced to fix a real bug - player could move while paused
# also folds feath-freeze from player death fix into game over screen
GAME_STATE = "menu"

# Per-game-session objects - None until "New Game" is clicked; torn down and rebuilt per session
game = None
mouse_controller = None

_last_diag_turn = -1
DIAG_TURN_INTERVAL = 25  # DEBUG: auto-print diagnostics every N turns
_last_seen_floor = 0

def print_diagnostics(tag="[DEBUG]"):
    """Live entity/sequence counts, to track down long-session lag -
     gets real numbers since leak couldn't be found.
     Maybe I'm losing it lmao"""
    print(f"{tag} turn={game.current_turn} floor={game.floor_number} "
          f"scene.entities={len(scene.entities)} application.sequences={len(application.sequences)} "
          f"tiles={len(game.tiles)} obstacles={len(game.obstacle_spawner.obstacles)} "
          f"enemies={len(game.enemies)} pickups={len(game.pickups)}")

def start_new_game():
    """New Game (from the main menu, or after a fresh Quit to Title)."""
    global game, mouse_controller, GAME_STATE, _last_diag_turn, _last_seen_floor

    game = GameBoard()
    mouse_controller = MouseController(game)

    _last_diag_turn = -1
    _last_seen_floor = 0

    main_menu.hide()
    pause_menu.hide()
    game_over_screen.hide()
    inventory_screen.hide()
    ui.set_visible(True)

    GAME_STATE = "playing"
    print("Game started!")

def quit_to_title():
    """Quit to title or return to title, tears down game session"""
    global game, mouse_controller, GAME_STATE

    if game is not None:
        game._clear_floor_entities()
        # The player is preserved across floor transitions by design (advance_floor()
        # never destroys it), so it's the one thing this teardown has to do that floor
        # transitions don't. Skip it if already destroyed (a death already did this).
        # destroy_silently() (not die()/destroy() directly) - see Actor.py for why.
        if game.player is not None and not game.player_defeated:
            game.player.destroy_silently()

    game = None
    mouse_controller = None

    pause_menu.hide()
    inventory_screen.hide()
    game_over_screen.hide()
    ui.set_visible(False)

    GAME_STATE = "menu"
    main_menu.show()

def open_inventory():
    pause_menu.hide()
    inventory_screen.show(game.player)

def close_inventory():
    pause_menu.show()

def resume_from_pause():
    global GAME_STATE
    GAME_STATE = "playing"
    pause_menu.hide()

ui = CombatUI()
ui.set_visible(False)  # nothing to show until a game actually starts

main_menu = MainMenu(on_new_game=start_new_game, on_quit=lambda: application.quit())
pause_menu = PauseMenu(on_open_inventory=open_inventory, on_quit_to_title=quit_to_title)
inventory_screen = InventoryScreen(on_close=close_inventory)
game_over_screen = GameOverScreen(on_return_to_title=quit_to_title)

def input(key):
    global GAME_STATE

    if GAME_STATE == "paused":
        if key == 'escape':
            resume_from_pause()
        return  # all gameplay input blocked while paused - menu buttons handle themselves

    if GAME_STATE != "playing":
        return  # "menu" / "game_over" - menu buttons handle themselves

    if game.player_defeated:
        return  # died this frame, before update() has transitioned to "game_over" yet

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
        GAME_STATE = "paused"
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
    global _last_diag_turn, _last_seen_floor, GAME_STATE

    if GAME_STATE != "playing":
        return

    if game.player_defeated:
        GAME_STATE = "game_over"
        game_over_screen.show(game.floor_number, game.current_turn)
        return

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
                        color=color.rgba32(0, 255, 0, 50),
                        _vision_indicator=True
                    )

# Run game
app.run()