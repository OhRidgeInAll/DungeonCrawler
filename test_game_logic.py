"""Automated regression tests for core game logic.

Runs fully headless via Ursina's window_type='none' (no GPU/display needed - safe for
CI runners), and tests the real game classes directly rather than duplicated mock logic.
Replaces the older test_*.py/debug_*.py scripts, which were interactive, called
app.run() (which blocks forever waiting for a window), and had no assertions - pytest
would pick them up by filename convention and hang/fail on every push.
"""
from pathlib import Path
from ursina import Ursina, application

app = Ursina(window_type='none')
# Ursina defaults asset_folder to Path(sys.argv[0]).parent, which under `pytest` points at
# pytest's own launcher rather than this file - point it at the actual project directory
# (same fix main.py already applies for PyInstaller's frozen-build asset path).
application.asset_folder = Path(__file__).parent

from GameBoard import GameBoard
from Enemy import GruntEnemy, TankEnemy, SniperEnemy, spawn_random_enemy
from Part import LOOT_TABLE, roll_loot
from Pathfinding import MouseController
from GameUI import CombatUI, InventoryScreen
from constants import grid_to_world


def clear_tile(game, x, y):
    """Guarantee a tile is walkable, regardless of the dungeon's random obstacle placement."""
    game.obstacle_spawner.obstacle_positions.discard((x, y))
    game.obstacle_spawner.obstacles = [
        o for o in game.obstacle_spawner.obstacles if not (o.grid_x == x and o.grid_y == y)
    ]


def test_dungeon_has_exactly_one_start_and_exit_room():
    game = GameBoard()
    roles = [room.role for room in game.rooms]
    assert roles.count("start") == 1
    assert roles.count("exit") == 1

    start_room = game._get_room_by_role("start")
    exit_room = game._get_room_by_role("exit")
    assert game.player.grid_position in start_room.get_tiles()
    assert (game.staircase.grid_x, game.staircase.grid_y) in exit_room.get_tiles()


def test_enemies_only_spawn_in_normal_rooms():
    game = GameBoard()
    for enemy in game.enemies:
        room = game.get_room_at_position(enemy.grid_x, enemy.grid_y)
        assert room is not None and room.role == "normal"


def test_advance_floor_regenerates_dungeon_and_keeps_player():
    game = GameBoard()
    player = game.player
    old_floor = game.floor_number

    game.advance_floor()

    assert game.floor_number == old_floor + 1
    assert game.player is player  # same player instance carries over
    new_start = game._get_room_by_role("start")
    assert player.grid_position in new_start.get_tiles()
    assert game.staircase is not None


def test_enemy_dealing_damage_does_not_crash_on_player_death():
    """Regression test: Actor.die() used to crash inside Ursina's destroy() because
    SpriteSheetAnimation.animations is a dict, not a list of killable objects."""
    game = GameBoard()
    player = game.player
    player.health = 1
    player.take_damage(9999)
    assert player.health <= 0


def test_actor_attack_does_not_crash_on_lethal_hit():
    """Regression test: the base Actor.attack() (used by every enemy) used to read
    target.position for the visual effect AFTER take_damage() already dealt damage -
    if that hit was lethal, take_damage() -> die() destroys the target synchronously,
    so a killing blow would try to read position off an already-destroyed entity.
    
    Yet another instance of a missing "is this entity still alive?" check, which is why the player has a
    `game.player_defeated` flag to let enemies know not to attack it again this turn.
    (Dodging crashes)"""
    game = GameBoard()
    player = game.player
    enemy = GruntEnemy(player.grid_x, player.grid_y + 1, game)
    game.enemies.append(enemy)

    player.health = 1
    enemy.attack_cooldown = 0

    attacked = enemy.attack(player)

    assert attacked
    assert player.health <= 0


def test_enemy_archetypes_have_distinct_stats():
    game = GameBoard()
    grunt = GruntEnemy(0, 0, game)
    tank = TankEnemy(0, 0, game)
    sniper = SniperEnemy(0, 0, game)

    assert tank.health > grunt.health
    assert tank.move_speed < grunt.move_speed
    assert sniper.attack_range > grunt.attack_range
    assert sniper.health < grunt.health


def test_loot_table_parts_match_their_archetype():
    for archetype_id, parts in LOOT_TABLE.items():
        for part in parts:
            assert part.source_archetype == archetype_id
            assert part.slot in ("arm", "legs", "core")


def test_player_equip_and_unequip_recompute_stats():
    game = GameBoard()
    player = game.player
    base_attack_power = player.attack_power

    sniper_arm = LOOT_TABLE["sniper"][0]
    player.inventory.append(sniper_arm)
    assert player.equip(sniper_arm)
    assert player.attack_power == base_attack_power + sniper_arm.modifiers.get('attack_power', 0)

    assert player.unequip("arm")
    assert player.attack_power == base_attack_power
    assert sniper_arm in player.inventory


def test_player_max_health_clamps_down_when_it_shrinks():
    game = GameBoard()
    player = game.player
    tank_core = LOOT_TABLE["tank"][2]  # max_health modifier

    player.health = player.max_health
    health_before_equip = player.health
    player.inventory.append(tank_core)
    player.equip(tank_core)
    assert player.health == health_before_equip  # unchanged, no free heal
    assert player.max_health > health_before_equip

    boosted_max = player.max_health
    player.health = boosted_max
    player.unequip("core")
    assert player.health == player.max_health  # clamped down, never above the new max
    assert player.max_health < boosted_max


def test_movement_queue_replaces_stale_action_instead_of_piling_up():
    """Regression test: queue_player_action used to append to a FIFO queue. If a
    second key was pressed while a turn was still resolving, its action would sit
    unprocessed until some later, unrelated keypress fired it instead."""
    game = GameBoard()
    player = game.player
    start_room = game._get_room_by_role("start")
    sx, sy = start_room.get_center()
    for tx, ty in [(sx, sy), (sx, sy + 1), (sx + 1, sy + 1)]:
        clear_tile(game, tx, ty)

    player.grid_x, player.grid_y = sx, sy
    player.position = grid_to_world(sx, sy)
    player.is_moving = False

    game.queue_player_action('move', sx, sy + 1)
    game.process_turn()
    assert game.turn_in_progress

    # A second action queued mid-turn must replace the first, not queue alongside it.
    game.queue_player_action('move', sx + 1, sy + 1)
    game.process_turn()  # no-op: a turn is already in progress
    assert game.action_queue == [('move', sx + 1, sy + 1)]


def test_mouse_controller_schedules_at_most_one_step_per_burst():
    """Regression test: MouseController.update() used to call invoke() every frame
    with no guard, so dozens could stack up while waiting on one turn to resolve -
    each popping another waypoint regardless of whether a move had actually landed."""
    game = GameBoard()
    player = game.player
    mc = MouseController(game)
    start_room = game._get_room_by_role("start")
    sx, sy = start_room.get_center()
    clear_tile(game, sx, sy + 1)

    player.grid_x, player.grid_y = sx, sy
    player.position = grid_to_world(sx, sy)
    player.is_moving = False
    game.enemies.clear()  # isolate from randomly-spawned enemies wandering into the way

    mc.path = [(sx, sy + 1)]
    mc.active = True
    mc._advance()
    assert player.grid_position == (sx, sy + 1)
    assert not mc.active  # path exhausted, stops itself

    # Resolve the turn, then hammer update() as if many frames passed before it resolved.
    player.position = player.target_position
    player.is_moving = False
    game._process_enemy_turns()

    mc.path = [(sx, sy)]
    mc.active = True
    for _ in range(50):
        mc.update()
    assert mc._step_scheduled  # exactly one pending step, not fifty


def test_on_right_click_defers_instead_of_dropping_step_mid_turn():
    """Regression test: on_right_click() used to call _advance() unconditionally, even
    while a turn was already resolving (e.g. from a recent WASD press). process_turn()
    silently no-ops in that case, but _advance() had already popped the step off the
    path - so the click was swallowed: no move happened, yet the controller believed
    the walk had finished."""
    game = GameBoard()
    player = game.player
    mc = MouseController(game)
    start_room = game._get_room_by_role("start")
    sx, sy = start_room.get_center()
    clear_tile(game, sx, sy + 1)
    game.enemies.clear()

    player.grid_x, player.grid_y = sx, sy
    player.position = grid_to_world(sx, sy)
    player.is_moving = False

    game.turn_in_progress = True  # simulate a turn already resolving
    mc.on_right_click(grid_to_world(sx, sy + 1))

    assert player.grid_position == (sx, sy)  # not dropped: simply not taken yet
    assert mc.path == [(sx, sy + 1)]
    assert mc.active

    # Once the turn clears, update()'s normal scheduling picks the deferred step up.
    game.turn_in_progress = False
    mc.update()
    assert mc._step_scheduled
    mc._scheduled_advance()
    assert player.grid_position == (sx, sy + 1)


def test_stop_cancels_a_pending_scheduled_step():
    """Regression test: stop() used to clear `active`/`path` but leave any already-
    scheduled invoke() callback alive. A WASD press mid-schedule followed by a fresh
    right-click within the delay window let the stale callback fire _advance() again
    against the new walk's state - an extra, unscheduled step."""
    from ursina import application as ursina_application

    game = GameBoard()
    player = game.player
    mc = MouseController(game)
    start_room = game._get_room_by_role("start")
    sx, sy = start_room.get_center()
    clear_tile(game, sx, sy + 1)
    game.enemies.clear()

    player.grid_x, player.grid_y = sx, sy
    player.position = grid_to_world(sx, sy)
    player.is_moving = False

    mc.active = True
    mc.path = [(sx, sy + 1)]
    mc.update()
    assert mc._pending_step is not None
    pending = mc._pending_step
    assert pending in ursina_application.sequences

    mc.stop()

    assert not mc._step_scheduled
    assert mc._pending_step is None
    assert pending not in ursina_application.sequences  # actually deregistered, not just forgotten


def test_gameboard_difficulty_tracks_floor_number():
    game = GameBoard()
    assert game.difficulty == game.floor_number == 1
    game.advance_floor()
    assert game.difficulty == game.floor_number == 2


def test_spawn_random_enemy_biases_toward_tougher_archetypes_at_high_difficulty():
    import random
    game = GameBoard()

    random.seed(42)
    low_counts = {"grunt": 0, "tank": 0, "sniper": 0}
    for _ in range(1000):
        enemy = spawn_random_enemy(0, 0, game, difficulty=1)
        low_counts[enemy.archetype_id] += 1

    random.seed(42)
    high_counts = {"grunt": 0, "tank": 0, "sniper": 0}
    for _ in range(1000):
        enemy = spawn_random_enemy(0, 0, game, difficulty=20)
        high_counts[enemy.archetype_id] += 1

    assert high_counts["grunt"] < low_counts["grunt"]
    assert high_counts["tank"] > low_counts["tank"]
    assert high_counts["sniper"] > low_counts["sniper"]


def test_roll_loot_drop_chance_rises_with_difficulty():
    import random
    random.seed(7)
    low_drops = sum(1 for _ in range(1000) if roll_loot("grunt", difficulty=1) is not None)

    random.seed(7)
    high_drops = sum(1 for _ in range(1000) if roll_loot("grunt", difficulty=25) is not None)

    assert high_drops > low_drops


def test_combat_ui_minimap_reflects_current_floor():
    game = GameBoard()
    ui = CombatUI()

    ui.rebuild_minimap(game.rooms, game.room_generator.get_bounds())
    assert len(ui.minimap_room_entities) == len(game.rooms)

    ui.update(game.player)
    assert ui.floor_text.text == f"Floor: {game.floor_number}"

    # Player marker should land inside the minimap's bounding box.
    half = ui.MINIMAP_SIZE / 2
    cx, cy = ui.MINIMAP_POSITION
    mx, my, _ = ui.minimap_player_marker.position
    assert cx - half <= mx <= cx + half
    assert cy - half <= my <= cy + half


def test_player_death_sets_flag_and_further_attacks_dont_crash():
    """Regression test: found via a real crash - Camera tries to follow
    player.position with no death check. Actor.die caused reliable crashes
    also covers second attacker batch trying to attack a now-dead player."""
    game = GameBoard()
    player = game.player
    assert game.player_defeated is False

    enemy1 = GruntEnemy(player.grid_x, player.grid_y + 1, game)
    enemy2 = GruntEnemy(player.grid_x, player.grid_y - 1, game)
    game.enemies.extend([enemy1, enemy2])

    player.health = 1
    enemy1.attack_cooldown = 0
    enemy2.attack_cooldown = 0

    enemy1.attack(player)  # lethal - destroys the player entity
    assert game.player_defeated is True

    # A second enemy taking its turn against the now-destroyed player must not crash.
    enemy2.take_turn()


def test_inventory_screen_shows_equipped_slots_and_inventory():
    game = GameBoard()
    player = game.player
    screen = InventoryScreen(on_close=lambda: None)

    sniper_arm = LOOT_TABLE["sniper"][0]
    player.inventory.append(sniper_arm)
    player.equip(sniper_arm)

    grunt_legs = LOOT_TABLE["grunt"][1]
    player.inventory.append(grunt_legs)

    screen.show(player)
    # Equipped rows: arm has a part (label + Unequip button) + 2 empty slots (label only),
    # plus an "Inventory:" header, plus one unequipped part (label + Equip button).
    assert len(screen.dynamic_entities) == 4 + 1 + 2

    screen.hide()
    assert screen.dynamic_entities == []
    assert not screen.background.enabled


def test_inventory_screen_equip_and_unequip_buttons_affect_player():
    game = GameBoard()
    player = game.player
    screen = InventoryScreen(on_close=lambda: None)

    sniper_arm = LOOT_TABLE["sniper"][0]
    player.inventory.append(sniper_arm)
    screen.show(player)

    screen._equip(sniper_arm)  # what the dynamically-built "Equip" button calls
    assert player.equipment["arm"] is sniper_arm
    assert sniper_arm not in player.inventory

    screen._unequip("arm")  # what the "Unequip" button calls
    assert player.equipment["arm"] is None
    assert sniper_arm in player.inventory


def test_inventory_screen_close_hides_and_calls_callback():
    closed = []
    screen = InventoryScreen(on_close=lambda: closed.append(True))
    game = GameBoard()
    screen.show(game.player)

    screen._handle_close()

    assert closed == [True]
    assert not screen.visible


def test_quit_to_title_teardown_leaves_a_clean_slate_for_a_new_game():
    """Regression test for the Quit to Title teardown pattern in main.py:
    game._clear_floor_entities() (already used by advance_floor()) plus
    player.destroy_silently(), since floor transitions deliberately preserve the
    player but quitting to title should not. Confirms a fresh GameBoard can be built
    right after, the same as clicking New Game a second time in the same process.

    Regression note: this used to call destroy(game.player) directly, which crashes -
    it bypasses Actor.die()'s _stop_sprite_animations() workaround for Ursina's
    destroy() choking on SpriteSheetAnimation.animations. destroy_silently() exists
    specifically to destroy an Actor outside of combat death without hitting that."""
    game = GameBoard()
    assert len(game.tiles) > 0
    assert game.player is not None

    game._clear_floor_entities()
    if game.player is not None and not game.player_defeated:
        game.player.destroy_silently()

    assert game.tiles == []
    assert game.enemies == []
    assert game.pickups == []

    # A brand new game must build cleanly afterward, in the same process.
    fresh_game = GameBoard()
    assert fresh_game.player is not None
    assert fresh_game.floor_number == 1
