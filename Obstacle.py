from ursina import *
from constants import *

class Obstacle(Entity):
    def __init__(self, grid_x, grid_y):
        super().__init__(
            model='cube',
            scale=(TILE_SIZE * 0.9, TILE_SIZE * 0.9, TILE_SIZE * 0.5),
            color=color.black,
            position = grid_to_world(grid_x, grid_y),
            collider='box'
        )
        self.grid_x = grid_x
        self.grid_y = grid_y

class ObstacleSpawner:
    def __init__(self, grid_size):
        self.grid_size = grid_size
        self.obstacles = []
    
    def add_obstacle(self,x, y):
        if self.is_valid_position(x, y):
            obstacle = Obstacle(x, y)
            self.obstacles.append(obstacle)
            return True
        return False
    
    def is_valid_position(self, x, y):
        return (0 <= x < self.grid_size and
                0 <= y < self.grid_size and
                not any(obstacle.grid_x == x and obstacle.grid_y == y for obstacle in self.obstacles) and
                (x, y) != (GRID_SIZE // 2, GRID_SIZE // 2)) # Prevent placing on player start position
    
    def generate_obstacles(self, count):
        for _ in range(count):
            while True:
                x, y = random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1)
                if self.add_obstacle(x, y):
                    break