from ursina import *

#This creates a window
app = Ursina()

#Now we create a GameObject, these are called entities in ursina

player = Entity(model='cube', color=color.orange, scale_y=2)

#update function is called every frame
def update():
    player.x += held_keys['d'] * time.dt
    player.x -= held_keys['a'] * time.dt

#this makes player move left or right with input
#we can check pressed keys using the held_keys dictionary
#time.dt is time since last frame

def input(key):
    if key == 'space':
        player.y += 1
        invoke(setattr, player, 'y', player.y-1, delay=.25)

#run game
app.run()