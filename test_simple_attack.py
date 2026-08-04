import sys
sys.path.insert(0, '.')

from ursina import *
from GameBoard import GameBoard
from Enemy import Enemy

# Simple test
app = Ursina()

print("Creating game board...")
game = GameBoard()

# Clear enemies
for e in game.enemies:
    destroy(e)
game.enemies = []

# Create one enemy right next to player
player_x, player_y = game.player.grid_x, game.player.grid_y
enemy_x, enemy_y = player_x + 1, player_y  # Right next to player

enemy = Enemy(enemy_x, enemy_y, game)
game.enemies.append(enemy)

print(f"Player at ({player_x}, {player_y}), enemy at ({enemy_x}, {enemy_y})")
print(f"Enemy starting health: {enemy.health}")

# Try attacking
print("\n--- First attack attempt ---")
result = game.player.attack(enemy)
print(f"Attack result: {result}")
print(f"Player attack_cooldown: {game.player.attack_cooldown}")
print(f"Enemy health after attack: {enemy.health}")

# Try attacking again (should fail due to cooldown)
print("\n--- Second attack attempt (should fail due to cooldown) ---")
result2 = game.player.attack(enemy)
print(f"Attack result: {result2}")
print(f"Player attack_cooldown: {game.player.attack_cooldown}")
print(f"Enemy health after second attempt: {enemy.health}")

print("\nTest complete. Press ESC to exit.")

def input(key):
    if key == 'escape':
        quit()

app.run()