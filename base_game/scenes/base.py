class BaseScene:
    def __init__(self):
        self._manager = None

    def on_enter(self, *args, **kwargs):
        pass

    def on_exit(self):
        pass

    def update(self, dt, ctx):
        pass

    def draw(self, ctx):
        pass

    def on_key_down(self, key, ctx):
        pass

    def on_key_up(self, key, ctx):
        pass

    def on_mouse_down(self, pos, button, ctx):
        pass

    def goto(self, name, *args, **kwargs):
        self._manager.change(name, *args, **kwargs)
