from ursina import *
from constants import *
from Actor import *
from SpriteSheet import *

class Player(Actor):
    def __init__(self, parent):
        # We're overriding the Entity class to create a Player class
        super().__init__(
            game = parent,
            model='quad',
            texture = 'assets/Robot.png',
            #Our game is built around the tiles, our character should be slightly smaller than a tile
            position=grid_to_world(GRID_SIZE // 2, GRID_SIZE // 2),  # Start in the center of the grid
            z=-0.1,  # Slightly above the grid
            team=0
            )
        self.health = 100
        self.grid_x = GRID_SIZE//2  # Integer grid column
        self.grid_y = GRID_SIZE//2  # Integer grid row
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
            x = clamp(x, 0, GRID_SIZE - 1)
            y = clamp(y, 0, GRID_SIZE - 1)

            if (x, y) != (self.grid_x, self.grid_y):
                # Convert grid coordinates to world position
                self.grid_x = x
                self.grid_y = y
                self.target_position = grid_to_world(x, y)
                self.is_moving = True

    def can_move_to(self, x, y):
        return (0 <= x < GRID_SIZE and
                0 <= y < GRID_SIZE and
                not self.game.obstacle_spawner.is_position_blocked(x, y))

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
    
