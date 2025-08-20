from ursina import *
from constants import *

class Actor(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.health = 100
        self.attack_power = 10
        self.attack_cooldown = 0
        self.team = 0 # 0 for player, 1 for enemy
        self.hit_effect = Entity(parent=self, model='circle', scale = 1.2, color = color.red, alpha=0, z=-0.2)
    
    def update(self):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= time.dt
    
    def die(self):
        destroy(self)
        if hasattr(self, 'on_death'):
            self.on_death()
    
    def take_damage(self, amount):
        self.health -= amount
        self.hit_effect.animate('alpha', 0.8, duration=0.1)
        self.hit_effect.animate('alpha', 0, duration=0.3, delay=0.1)

        if self.health <= 0:
            self.die()
    
    def attack(self, target):
        if self.can_attack(target):
            target.take_damage(self.attack_power)
            self.attack_cooldown = ATTACK_COOLDOWN
            self.show_attack_effect(target)
            return True
        return False
    
    def render_attack(self):
        attack_indicator = Entity(
            parent = self,
            model = 'quad',
            scale = 1.5,
            color = color.yellow,
            alpha = 0.7,
            z = -0.3
        )
        attack_indicator.animate('scale', 0.5, duration=0.2)
        attack_indicator.animate('alpha', 0, duration=0.2, delay=0.2)
        destroy(attack_indicator, delay=0.3)