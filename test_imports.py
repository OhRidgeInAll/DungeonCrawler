from ursina import *
from GameBoard import *
from constants import *
from GameUI import CombatUI
from Pathfinding import MouseController

print("All imports successful")

app = Ursina()
print("App created")

# Simple test - should be visible
Text(text="IMPORT TEST", position=(0, 0), scale=3, color=color.red)

app.run()