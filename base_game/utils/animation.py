from pgzero.loaders import images as pgz_images

class Animation:
    def __init__(self, frame_names, fps=8):
        self.frames = [pgz_images.load(name) for name in frame_names]
        self.fps = fps
        self.t = 0.0
        self.i = 0

    def update(self, dt, playing=True):
        if not playing or len(self.frames) <= 1:
            return
        self.t += dt
        step = 1.0 / max(1, self.fps)
        while self.t >= step:
            self.t -= step
            self.i = (self.i + 1) % len(self.frames)

    def get(self):
        return self.frames[self.i]

class DirectionalAnimation:
    def __init__(self, anims, default_dir="down"):
        self.anims = anims
        self.dir = default_dir

    def set_dir(self, d):
        if d in self.anims:
            self.dir = d

    def update(self, dt, moving):
        self.anims[self.dir].update(dt, playing=moving)

    def get(self):
        return self.anims[self.dir].get()
