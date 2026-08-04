from ursina import *

app = Ursina()
print("App created")

# Simple UI test
Text(text="Hello World!", position=(0, 0), scale=2, color=color.white)
Button(text="Click me", position=(0, -0.1), scale=(0.3, 0.1), color=color.blue)

# 3D test
cube = Entity(model='cube', color=color.red, position=(0,0,0), scale=(1,1,1))
camera.position = (0, 0, -5)

def update():
    cube.rotation_y += time.dt * 50

app.run()