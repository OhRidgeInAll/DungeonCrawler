from ursina import *
from constants import *
from Actor import Actor
import random

class Enemy(Actor):
    """Base enemy: grid movement, vision, and melee-chase AI shared by all archetypes."""
    archetype_id = "enemy"

    def __init__(self, grid_x, grid_y, game_board, color=color.red):
        super().__init__(
            model='quad',
            color=color,
            scale=(TILE_SIZE * 0.8, TILE_SIZE * 0.8),
            position = grid_to_world(grid_x, grid_y),
            team = 1
        )
        self.grid_x = grid_x  # Integer grid column
        self.grid_y = grid_y  # Integer grid row
        self.game_board = game_board
        self.move_cooldown = 0
        self.move_speed = 30
        self.target_position = self.position
        self.is_moving = False
        self.vision_range = 5  # cells

        # Set up death callback to remove from game board
        self.on_death = self._on_death

    def update(self):
        super().update()
        if self.is_moving:
            self.position = lerp(self.position, self.target_position, time.dt * self.move_speed)
            if (self.position - self.target_position).length() < 0.01:
                self.position = self.target_position
                self.is_moving = False

    def take_turn(self):
        """Enemy takes a turn: attack if possible, otherwise close the distance to the player."""
        player = self.game_board.player
        if not player:
            return

        distance = abs(self.grid_x - player.grid_x) + abs(self.grid_y - player.grid_y)
        if distance <= self.vision_range:
            if self.can_attack(player):
                self.attack(player)
            else:
                self.move_toward_player(player.grid_x, player.grid_y)
        # else: player not in range, wait

    def move_toward_player(self, player_x, player_y):
        """Simple AI: move one step toward player if possible."""
        dx = player_x - self.grid_x
        dy = player_y - self.grid_y
        self._step_along_direction(dx, dy)

    def move_away_from_player(self, player_x, player_y):
        """Simple AI: move one step away from the player if possible."""
        dx = self.grid_x - player_x
        dy = self.grid_y - player_y
        self._step_along_direction(dx, dy)

    def _step_along_direction(self, dx, dy):
        """Take one grid step biased toward whichever axis has the larger delta,
        falling back to the other axis (or the opposite step) if that's blocked."""
        # Currently prefer the axis with greater distance, in future would like to handle paths determined by efficiency once tile types implemented.
        if abs(dx) > abs(dy):
            axis_order = [(1 if dx > 0 else -1, 0), (0, 1 if dy > 0 else -1)]
        else:
            axis_order = [(0, 1 if dy > 0 else -1), (1 if dx > 0 else -1, 0)]

        for step_x, step_y in axis_order:
            if step_x != 0 and self.can_move_to(self.grid_x + step_x, self.grid_y):
                self.move_to_grid_position(self.grid_x + step_x, self.grid_y)
                return
            if step_y != 0 and self.can_move_to(self.grid_x, self.grid_y + step_y):
                self.move_to_grid_position(self.grid_x, self.grid_y + step_y)
                return

    def move_to_grid_position(self, x, y):
        """Move enemy to grid position with animation."""
        if self.can_move_to(x, y):
            self.grid_x = x
            self.grid_y = y
            self.target_position = grid_to_world(x, y)
            self.is_moving = True
            return True
        return False

    def can_move_to(self, x, y):
        """Check if enemy can move to position."""
        if not self.game_board.is_position_in_dungeon(x, y):
            return False

        # Don't path into blocked tiles
        if self.game_board.is_position_blocked(x, y):
            return False

        # Don't overlap enemies
        for enemy in self.game_board.enemies:
            if enemy != self and enemy.grid_x == x and enemy.grid_y == y:
                return False

        # Don't overlap player
        player = self.game_board.player
        if player and x == player.grid_x and y == player.grid_y:
            return False

        return True

    @property
    def grid_position(self):
        return (self.grid_x, self.grid_y)

    def _on_death(self):
        """Callback when enemy dies - remove from game board and chance to drop part."""
        if hasattr(self, 'game_board') and self.game_board:
            if hasattr(self.game_board, 'spawn_loot_drop'):
                self.game_board.spawn_loot_drop(self.archetype_id, self.grid_x, self.grid_y)

            # Remove from enemies list
            if hasattr(self.game_board, 'enemies') and self in self.game_board.enemies:
                self.game_board.enemies.remove(self)
                print(f"{self.archetype_id} removed from game board at ({self.grid_x}, {self.grid_y})")


class GruntEnemy(Enemy):
    """Baseline melee chaser - the original enemy behavior."""
    archetype_id = "grunt"

    def __init__(self, grid_x, grid_y, game_board):
        super().__init__(grid_x, grid_y, game_board, color=color.red)
        self.health = random.randint(60, 100)
        self.attack_power = random.randint(6, 10)
        self.move_speed = 30
        self.vision_range = 5
        self.attack_range = ATTACK_RANGE


class TankEnemy(Enemy):
    """Slow, tough, hard-hitting melee brawler."""
    archetype_id = "tank"

    def __init__(self, grid_x, grid_y, game_board):
        super().__init__(grid_x, grid_y, game_board, color=color.gray)
        self.health = random.randint(130, 170)
        self.attack_power = random.randint(12, 18)
        self.move_speed = 15
        self.vision_range = 4
        self.attack_range = ATTACK_RANGE


class SniperEnemy(Enemy):
    """Fragile long-range attacker that tries to keep its distance."""
    archetype_id = "sniper"

    def __init__(self, grid_x, grid_y, game_board):
        super().__init__(grid_x, grid_y, game_board, color=color.orange)
        self.health = random.randint(35, 55)
        self.attack_power = random.randint(5, 9)
        self.move_speed = 25
        self.vision_range = 7
        self.attack_range = 4
        self.retreat_distance = 2  # back away if the player gets this close

    def take_turn(self):
        player = self.game_board.player
        if not player:
            return

        distance = abs(self.grid_x - player.grid_x) + abs(self.grid_y - player.grid_y)
        if distance > self.vision_range:
            return

        if self.can_attack(player):
            self.attack(player)
        elif distance < self.retreat_distance:
            self.move_away_from_player(player.grid_x, player.grid_y)
        else:
            self.move_toward_player(player.grid_x, player.grid_y)


# Archetypes and their relative spawn weights.
ENEMY_ARCHETYPES = [
    (GruntEnemy, 0.5),
    (SniperEnemy, 0.3),
    (TankEnemy, 0.2),
]

def spawn_random_enemy(grid_x, grid_y, game_board):
    """Instantiate a random enemy archetype, weighted by ENEMY_ARCHETYPES."""
    classes = [archetype for archetype, weight in ENEMY_ARCHETYPES]
    weights = [weight for archetype, weight in ENEMY_ARCHETYPES]
    enemy_class = random.choices(classes, weights=weights)[0]
    return enemy_class(grid_x, grid_y, game_board)
