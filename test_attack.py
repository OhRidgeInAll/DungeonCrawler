import sys
sys.path.insert(0, '.')

from ursina import *
from GameBoard import GameBoard

# Minimal test to check attack system
app = Ursina()

print("Creating game board...")
game = GameBoard()

print(f"Player position: {game.player.grid_position}")
print(f"Number of enemies: {len(game.enemies)}")
if game.enemies:
    print(f"First enemy position: {game.enemies[0].grid_position}")
    
    # Test attack distance calculation
    player_x, player_y = game.player.grid_position
    enemy_x, enemy_y = game.enemies[0].grid_position
    distance = abs(player_x - enemy_x) + abs(player_y - enemy_y)
    print(f"Distance to first enemy: {distance}")
    print(f"Attack range (constants.ATTACK_RANGE): {1.5}")
    print(f"Player attack_range attribute: {game.player.attack_range}")
    
    # Try attacking
    print("\nTrying to attack...")
    game.player.try_attack()
    
    # Check if attack happened
    print(f"\nPlayer attack cooldown: {game.player.attack_cooldown}")
    if game.enemies:
        print(f"First enemy health: {game.enemies[0].health}")

print("\nTest complete. Press ESC to exit.")

def input(key):
    if key == 'escape':
        quit()

app.run()