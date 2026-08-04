import sys
sys.path.insert(0, '.')

from ursina import *
from GameBoard import GameBoard
import random

# Test attack system with enemies placed close to player
app = Ursina()

print("Creating game board...")
game = GameBoard()

# Move player to a known position
player_x, player_y = 5, 5
game.player.grid_x = player_x
game.player.grid_y = player_y
game.player.position = game.player.target_position = (player_x - 3.5, player_y - 3.5, -0.1)

print(f"Player moved to position: ({player_x}, {player_y})")

# Clear existing enemies
for enemy in game.enemies:
    destroy(enemy)
game.enemies = []

# Create test enemies at different distances
test_positions = [
    (player_x + 1, player_y),      # Right, distance=1
    (player_x - 1, player_y),      # Left, distance=1  
    (player_x, player_y + 1),      # Up, distance=1
    (player_x, player_y - 1),      # Down, distance=1
    (player_x + 1, player_y + 1),  # Diagonal, distance=2
    (player_x + 2, player_y),      # Too far, distance=2
]

from Enemy import Enemy

for i, (ex, ey) in enumerate(test_positions):
    enemy = Enemy(ex, ey, game)
    game.enemies.append(enemy)
    distance = abs(player_x - ex) + abs(player_y - ey)
    print(f"Created enemy {i} at ({ex}, {ey}), distance={distance}")

print(f"\nTotal enemies: {len(game.enemies)}")

# Test attack
print("\n--- Testing attack ---")
print(f"Player attack_range: {game.player.attack_range}")
print(f"Constants.ATTACK_RANGE: {1.5}")

# Try attacking
game.player.try_attack()

# Check results
print(f"\nPlayer attack cooldown: {game.player.attack_cooldown}")
for i, enemy in enumerate(game.enemies):
    print(f"Enemy {i} at ({enemy.grid_x}, {enemy.grid_y}): health={enemy.health}")

print("\nTest complete. Press ESC to exit.")

def input(key):
    if key == 'escape':
        quit()

app.run()