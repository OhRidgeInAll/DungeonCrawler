import sys
sys.path.insert(0, '.')

# Test attack logic without Ursina window
from constants import ATTACK_RANGE, ATTACK_COOLDOWN

print(f"ATTACK_RANGE from constants: {ATTACK_RANGE}")
print(f"ATTACK_COOLDOWN from constants: {ATTACK_COOLDOWN}")

# Create mock Actor classes to test logic
class MockEntity:
    def __init__(self):
        self.position = (0, 0, 0)
        self.health = 100
        self.team = 1  # enemy team
        self.grid_x = 5
        self.grid_y = 5

class MockActor:
    def __init__(self):
        self.health = 100
        self.attack_power = 10
        self.attack_cooldown = 0
        self.team = 0  # player team
        self.grid_x = 5
        self.grid_y = 4  # adjacent to enemy (distance=1)
        
    def can_attack(self, target):
        """Check if this actor can attack the target."""
        # Check cooldown
        if self.attack_cooldown > 0:
            print(f"  can_attack: failed cooldown ({self.attack_cooldown})")
            return False
        
        # Check team (don't attack allies)
        if hasattr(target, 'team') and target.team == self.team:
            print(f"  can_attack: failed same team ({target.team})")
            return False
        
        # Use grid distance for consistency with player's try_attack
        if hasattr(self, 'grid_x') and hasattr(target, 'grid_x'):
            # Calculate Manhattan distance (grid units)
            distance = abs(self.grid_x - target.grid_x) + abs(self.grid_y - target.grid_y)
            in_range = distance <= ATTACK_RANGE
            print(f"  can_attack: distance={distance}, ATTACK_RANGE={ATTACK_RANGE}, in_range={in_range}")
            if not in_range:
                print(f"  can_attack: failed distance {distance} > {ATTACK_RANGE}")
            return in_range
        else:
            # Fallback to 3D distance
            distance = 1.0  # mock
            in_range = distance <= ATTACK_RANGE
            if not in_range:
                print(f"  can_attack: failed 3D distance {distance} > {ATTACK_RANGE}")
            return in_range
    
    def attack(self, target):
        print(f"  attack: called on target at ({target.grid_x}, {target.grid_y})")
        if self.can_attack(target):
            print(f"  attack: can_attack returned True, dealing {self.attack_power} damage")
            target.health -= self.attack_power
            self.attack_cooldown = ATTACK_COOLDOWN
            return True
        else:
            print(f"  attack: can_attack returned False")
            return False

# Test
player = MockActor()
enemy = MockEntity()

print(f"\nPlayer at ({player.grid_x}, {player.grid_y}), enemy at ({enemy.grid_x}, {enemy.grid_y})")
print(f"Distance: {abs(player.grid_x - enemy.grid_x) + abs(player.grid_y - enemy.grid_y)}")

print("\nTesting attack...")
result = player.attack(enemy)
print(f"Attack result: {result}")
print(f"Player cooldown: {player.attack_cooldown}")
print(f"Enemy health: {enemy.health}")

# Test with enemy at distance 2 (should fail)
print("\n--- Testing enemy at distance 2 ---")
player2 = MockActor()
player2.grid_y = 3  # distance = |5-5| + |3-5| = 0 + 2 = 2
enemy2 = MockEntity()

print(f"Player at ({player2.grid_x}, {player2.grid_y}), enemy at ({enemy2.grid_x}, {enemy2.grid_y})")
print(f"Distance: {abs(player2.grid_x - enemy2.grid_x) + abs(player2.grid_y - enemy2.grid_y)}")

result2 = player2.attack(enemy2)
print(f"Attack result: {result2}")