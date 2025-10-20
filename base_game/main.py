from base_game import config
from base_game.app import SceneManager
from base_game.scenes.menu import MenuScene
from base_game.scenes.play import PlayScene
from types import SimpleNamespace

WIDTH, HEIGHT = config.WIDTH, config.HEIGHT
TITLE = config.TITLE

manager = SceneManager()
manager.register("menu", MenuScene())
manager.register("play", PlayScene())
manager.change("menu")

_ctx = None
def _ctx():
    global _ctx
    if _ctx is None:
        _ctx = SimpleNamespace(screen=screen, keyboard=keyboard, keys=keys, images=images)
    else:
        _ctx.screen = screen
        _ctx.keyboard = keyboard
        _ctx.keys = keys
        _ctx.images = images
    return _ctx

def update(dt):
    manager.update(dt, _ctx())

def draw():
    manager.draw(_ctx())

def on_key_down(key):
    manager.on_key_down(key, _ctx())

def on_key_up(key):
    manager.on_key_up(key, _ctx())

def on_mouse_down(pos, button):
    manager.on_mouse_down(pos, button, _ctx())

if __name__ == "__main__":
    import pgzrun
    pgzrun.go()
