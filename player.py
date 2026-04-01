from ursina import *
import constants
from Actor import *
from SpriteSheet import *

class Player(Actor):
    def __init__(self, parent):
        # Position will be set by GameBoard after dungeon generation
        # We're overriding the Entity class to create a Player class
        super().__init__(
            game = parent,
            model='quad',
            texture = 'assets/Robot.png',
            # Position set by gameboard
            position=(0, 0, -0.1),  # Temporary position
            z=-0.1,  # Slightly above the grid
            team=0
            )
        self.health = 100
        self.grid_x = 0  # temp, will be set by gameboard (both x,y)
        self.grid_y = 0
        self.target_position = self.position
        self.move_speed = 50
        self.is_moving = False

        self.attack_shape = Entity(
            parent=self,
            movel=Circle(6, radius=0.4),
            color=color.clear,
            collider='mesh',
            visible=False
        )
    
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
        
        return True

    def try_attack(self):
        for entity in self.attack_shape.intersects().entities:
            if hasattr(entity, 'team') and entity.team != self.team:
                self.attack(entity)
                break

    def update(self):
        if self.is_moving:
            self.position = lerp(self.position, self.target_position, time.dt * self.move_speed)

            if (self.position - self.target_position).length() < 0.01:
                self.position = self.target_position
                self.is_moving = False
    
