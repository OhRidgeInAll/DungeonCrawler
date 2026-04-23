from ursina import *
from ursina.prefabs.sprite_sheet_animation import SpriteSheetAnimation
import constants
from Actor import *

class Player(Actor):
    def __init__(self, parent):
        # Position will be set by GameBoard after dungeon generation
        # We're overriding the Entity class to create a Player class
        super().__init__(
            game = parent,
            model=None,  # We'll use sprite sheet instead
            # Position set by gameboard
            position=(0, 0, -0.1),  # Temporary position
            z=-0.1,  # Slightly above the grid
            team=0
            )
        
        # Fixed implementation I thought texture loading was correct
        # SpriteAnimation setup for player character
        self.sprite = SpriteSheetAnimation(
            'assets/Robot.png',
            tileset_size=(2, 1),  # 2 frames horizontally, 1 row
            fps=6,
            animations={
                'idle': ((0, 0), (1, 0)),  # Frame 0 to frame 1
            },
            parent=self,
            position=(0, 0, 0),
            scale=(constants.TILE_SIZE * 0.8, constants.TILE_SIZE * 0.8)
        )
        self.sprite.play_animation('idle')
        self.health = 100
        self.grid_x = 0  # temp, will be set by gameboard (both x,y)
        self.grid_y = 0
        self.target_position = self.position
        self.move_speed = 50
        self.is_moving = False

        # Attack range checking will use distance instead of collider
        self.attack_range = constants.ATTACK_RANGE
        self.has_attacked_this_turn = False
    
    @property
    def grid_position(self):
        return (self.grid_x, self.grid_y)

    def move_to_grid_position(self, x, y):
        if not self.is_moving and self.can_move_to(x, y):
            # Get bounds for clamp
            if constants.DUNGEON_BOUNDS is not None:
                min_x, min_y, max_x, max_y = constants.DUNGEON_BOUNDS
                x = clamp(x, min_x, max_x)
                y = clamp(y, min_y, max_y)
            else:
                # Fallback to def
                x = clamp(x, 0, constants.DEFAULT_GRID_SIZE - 1)
                y = clamp(y, 0, constants.DEFAULT_GRID_SIZE - 1)

            if (x, y) != (self.grid_x, self.grid_y):
                # Convert grid coordinates to world position
                self.grid_x = x
                self.grid_y = y
                self.target_position = constants.grid_to_world(x, y)
                self.is_moving = True

    def can_move_to(self, x, y):
        if not self.game.is_position_in_dungeon(x, y):
            return False
        
        if self.game.is_position_blocked(x, y):
            return False
        
        # Check if there's an enemy at the target position
        enemy_at_target = self.game.get_enemy_at_position(x, y)
        if enemy_at_target:
            return False  # Can't move into enemy tile
        
        return True

    def can_attack(self, target):
        # There was an attempt to implement cooldowns, shortsighted as they were timebased initially
        """Override Actor.can_attack to include turn-based check."""
        # Check if already attacked this turn
        if hasattr(self, 'has_attacked_this_turn') and self.has_attacked_this_turn:
            return False
        
        # Use parent's can_attack for other checks (distance, team, etc.)
        return super().can_attack(target)
    
    def attack(self, target):
        """Override Actor.attack to set turn-based flag instead of cooldown."""
        if self.can_attack(target):
            # Get target position before potentially destroying it
            target_position = target.position if hasattr(target, 'position') else None
            target.take_damage(self.attack_power)
            self.has_attacked_this_turn = True
            self.show_attack_effect(target, target_position)
            return True
        return False
    
    def try_attack(self):
        if not hasattr(self, 'game') or not self.game.enemies:
            return False
            
        attacked = False
        for enemy in self.game.enemies:
            # Calculate Manhattan distance (grid units)
            distance = abs(self.grid_x - enemy.grid_x) + abs(self.grid_y - enemy.grid_y)
            if distance <= self.attack_range:  # Use actual attack range
                if self.attack(enemy):
                    attacked = True
                    break
        
        return attacked
    
    def try_attack_enemy_at(self, x, y):
        """Try to attack enemy at specific grid position."""
        if not hasattr(self, 'game') or not self.game.enemies:
            return False
            
        # Find enemy at the specified position
        for enemy in self.game.enemies:
            if enemy.grid_x == x and enemy.grid_y == y:
                # Check if enemy is in attack range
                distance = abs(self.grid_x - x) + abs(self.grid_y - y)
                if distance <= self.attack_range:
                    return self.attack(enemy)
        return False

    def update(self):
        if self.is_moving:
            self.position = lerp(self.position, self.target_position, time.dt * self.move_speed)

            if (self.position - self.target_position).length() < 0.01:
                self.position = self.target_position
                self.is_moving = False
    
