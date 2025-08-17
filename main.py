from ursina import *
from player import Player
from GameTile import GameTile

#This creates a window
app = Ursina()

#Game Constants
GRID_SIZE = 8
TILE_SIZE = 1
GRID_COLOR = color.gray

#Now we create a GameObject, these are called entities in ursina

playerCharacter = Player()

#update function is called every frame
def update():
    playerCharacter.x += held_keys['d'] * time.dt
    playerCharacter.x -= held_keys['a'] * time.dt

#this makes playerCharacter move left or right with input
#we can check pressed keys using the held_keys dictionary
#time.dt is time since last frame

def input(key):
    if key == 'space':
        playerCharacter.y += 1
        invoke(setattr, playerCharacter, 'y', playerCharacter.y-1, delay=.25)

#run game
app.run()