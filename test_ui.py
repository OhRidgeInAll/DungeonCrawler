from ursina import *

app = Ursina()
print("App created")

# Simple UI test - should be visible immediately
Text(text="TEST TEXT - RED", position=(0, 0), scale=3, color=color.red)
Button(text="TEST BUTTON", position=(0, -0.2), scale=(0.3, 0.1), color=color.blue)

# Also add a 3D cube to see if 3D works
cube = Entity(model='cube', color=color.green, position=(0,0,0), scale=(1,1,1))
camera.position = (0, 0, -5)

def update():
    cube.rotation_y += time.dt * 50

app.run()