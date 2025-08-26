from ursina import *

class SpriteSheet(Entity):
    def __init__(self, parent, animation_frames, txt_path, grid_size=(8, 8), sprite_index=0, **kwargs):
        super().__init__(model='quad', **kwargs)
        
        self.fps = 10
        
        self.animation_frames = animation_frames
        self.texture = load_texture(txt_path)
        self.grid_size = grid_size
        self.set_sprite(sprite_index)
        self.current_frame_index = 0
        self.animating = False

    def set_sprite(self, sprite_index):
        cols, rows = self.grid_size
        frame_width = 1.0 / cols
        frame_height = 1.0 / rows

        col = sprite_index % cols
        row = rows - 1 - (sprite_index // cols)  # Invert row for UV mapping

        self.texture_offset = (col * frame_width, row * frame_height)
        self.texture_scale = (frame_width, frame_height)

    def start_animation(self):
        self.animating = True
        self.animate_next_frame()

    def animate_next_frame(self):
        if not self.animating:
            return
        
        #Set current frame
        frame_index = self.animation_frames[self.current_frame_index]
        self.set_sprite(frame_index)
        parent.texture = load_texture('assets/Robot.png')

        self.current_frame_index = (self.current_frame_index + 1) % len(self.animation_frames)

        invoke(self.animate_next_frame, delay=1.0/self.fps)  # Adjust delay for animation speed