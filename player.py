from ursina import *

class Player(Entity):
    def __init__(self):
        # We're overriding the Entity class to create a Player class
        super().__init__(
            model='quad',
            color=color.azure,
            position=(0, 0, -0.1)
            )
        self.grid_position = (0, 0)
        self.target_position = self.position
        self.move_speed = 0.2
        self.is_moving = False
    
    def update(self):
        if self.position != self.target_position:
            self.position = lerp(self.position, self.target_position, time.dt * 10)
        else:
            self.is_moving = False