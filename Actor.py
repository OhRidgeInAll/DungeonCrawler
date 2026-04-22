from ursina import *
from constants import *
import math

class Actor(Entity):
    def __init__(self, **kwargs):
        # Extract team from kwargs if provided, default to 0 (player)
        self.team = kwargs.pop('team', 0)
        super().__init__(**kwargs)
        self.health = 100
        self.attack_power = 10
        self.attack_cooldown = 0
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
        
        # Use grid distance for consistency with player's try_attack
        if hasattr(self, 'grid_x') and hasattr(target, 'grid_x'):
            # Calculate Manhattan distance (grid units)
            distance = abs(self.grid_x - target.grid_x) + abs(self.grid_y - target.grid_y)
            return distance <= ATTACK_RANGE
        else:
            # Fallback to 3D distance (manual calculation)
            distance = (self.position - target.position).length()
            return distance <= ATTACK_RANGE
    
    def attack(self, target):
        if self.can_attack(target):
            target.take_damage(self.attack_power)
            self.attack_cooldown = ATTACK_COOLDOWN
            self.show_attack_effect(target)
            return True
        return False
    
    def show_attack_effect(self, target, position=None):
        """Visual effect for attacking with particle effects."""
        # Get target position in case  target might be destroyed)
        if position is None and hasattr(target, 'position'):
            position = target.position
        elif position is None:
            # Can't show effect without position
            return
        
        # Create particle effect at target position
        self.create_attack_particles(position)
        
        # Also show floating damage number
        self.show_damage_number(target, self.attack_power, position)
        
        # Keep the original line effect for visual connection
        # Calculate 3D distance manually
        distance_3d = (self.position - position).length()
        attack_line = Entity(
            model='cube',
            scale=(0.1, 0.1, distance_3d),
            color=color.yellow,
            position=self.position,
            look_at=position
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
            
            # Create particle at position with higher Z to be visible above tiles
            particle = Entity(
                model='circle',
                color=color.yellow,
                scale=0.1,
                position=Vec3(position.x, position.y, -0.5),  # Higher Z to be visible
                alpha=0.8
            )
            
            # Animate particle outward
            target_pos = Vec3(position.x + direction.x * 0.5, position.y + direction.y * 0.5, -0.5)
            particle.animate_position(target_pos, duration=0.3, curve=curve.linear)
            particle.animate('alpha', 0, duration=0.3)
            destroy(particle, delay=0.3)
    
    def show_damage_number(self, target, damage):
        """Show floating damage number above target."""
        # Ensure target has a valid position
        if not hasattr(target, 'position'):
            return
            
        # Position above target with higher Z to be visible
        # Use target's current world position
        damage_text = Text(
            text=f"-{damage}",
            position=Vec3(target.position.x, target.position.y + 0.3, -0.4),
            scale=1.2,  # Smaller size
            color=color.red,
            background=True,
            background_color=color.black
        )
        
        # Animate floating up and fading out
        damage_text.animate_position(
            Vec3(damage_text.position.x, damage_text.position.y + 0.7, -0.4),
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
