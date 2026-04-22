from ursina import *
from constants import *
import math

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
    
    def can_attack(self, target):
        """Check if this actor can attack the target."""
        # Check cooldown
        if self.attack_cooldown > 0:
            return False
        
        # Check team (don't attack allies)
        if hasattr(target, 'team') and target.team == self.team:
            return False
        
        distance = self.distance(target)
        return distance <= ATTACK_RANGE
    
    def attack(self, target):
        if self.can_attack(target):
            target.take_damage(self.attack_power)
            self.attack_cooldown = ATTACK_COOLDOWN
            self.show_attack_effect(target)
            return True
        return False
    
    def show_attack_effect(self, target):
        """Visual effect for attacking with particle effects."""
        # Create particle effect at target position
        self.create_attack_particles(target.position)
        
        # Also show floating damage number
        self.show_damage_number(target, self.attack_power)
        
        # Keep the original line effect for visual connection
        attack_line = Entity(
            model='cube',
            scale=(0.1, 0.1, self.distance(target)),
            color=color.yellow,
            position=self.position,
            look_at=target.position
        )
        attack_line.animate('alpha', 0, duration=0.2)
        destroy(attack_line, delay=0.2)
    
    def create_attack_particles(self, position):
        """Create particle effect at given position."""
        num_particles = 8
        for i in range(num_particles):
            angle = (i / num_particles) * 360
            rad = math.radians(angle)
            direction = Vec3(math.cos(rad), math.sin(rad), 0)
            
            particle = Entity(
                model='circle',
                color=color.yellow,
                scale=0.1,
                position=position,
                alpha=0.8
            )
            
            # Animate particle outward
            target_pos = position + direction * 0.5
            particle.animate_position(target_pos, duration=0.3, curve=curve.linear)
            particle.animate('alpha', 0, duration=0.3)
            destroy(particle, delay=0.3)
    
    def show_damage_number(self, target, damage):
        """Show floating damage number above target."""
        damage_text = Text(
            text=f"-{damage}",
            position=target.position + (0, 0.5, 0),
            scale=2,
            color=color.red,
            background=True,
            background_color=color.black
        )
        
        # Animate floating up and fading out
        damage_text.animate_position(
            damage_text.position + (0, 1, 0),
            duration=1.0,
            curve=curve.out_expo
        )
        damage_text.animate('alpha', 0, duration=1.0)
        destroy(damage_text, delay=1.0)
    
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
