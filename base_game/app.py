class SceneManager:
    def __init__(self):
        self._scenes = {}
        self.current = None

    def register(self, name, scene):
        scene._manager = self
        self._scenes[name] = scene

    def change(self, name, *args, **kwargs):
        if self.current and hasattr(self.current, "on_exit"):
            self.current.on_exit()
        self.current = self._scenes[name]
        if hasattr(self.current, "on_enter"):
            self.current.on_enter(*args, **kwargs)

    def update(self, dt, ctx):
        if self.current and hasattr(self.current, "update"):
            self.current.update(dt, ctx)

    def draw(self, ctx):
        if self.current and hasattr(self.current, "draw"):
            self.current.draw(ctx)

    def on_key_down(self, key, ctx):
        if self.current and hasattr(self.current, "on_key_down"):
            self.current.on_key_down(key, ctx)

    def on_key_up(self, key, ctx):
        if self.current and hasattr(self.current, "on_key_up"):
            self.current.on_key_up(key, ctx)

    def on_mouse_down(self, pos, button, ctx):
        if self.current and hasattr(self.current, "on_mouse_down"):
            self.current.on_mouse_down(pos, button, ctx)
