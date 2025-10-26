from types import SimpleNamespace

from base_game import config
from base_game.app import SceneManager
from base_game.scenes.menu import MenuScene
from base_game.scenes.pause import PauseScene
from base_game.scenes.play import PlayScene
from base_game.scenes.you_win import YouWinScene

from .scenes.game_over import GameOverScene

WIDTH, HEIGHT = config.WIDTH, config.HEIGHT
TITLE = config.TITLE


manager = SceneManager()
manager.register("menu", MenuScene())
manager.register("play", PlayScene())
manager.register("pause", PauseScene())
manager.register("game_over", GameOverScene())
manager.register("you_win", YouWinScene())

manager.change("menu")

_ctx_cache = None


def get_ctx():
    global _ctx_cache
    try:
        s = screen
        kbd = keyboard
        ks = keys
        imgs = images
    except NameError:
        return SimpleNamespace(screen=None, keyboard=None, keys=None, images=None)

    if _ctx_cache is None:
        _ctx_cache = SimpleNamespace(screen=s, keyboard=kbd, keys=ks, images=imgs)
    else:
        _ctx_cache.screen = s
        _ctx_cache.keyboard = kbd
        _ctx_cache.keys = ks
        _ctx_cache.images = imgs
    return _ctx_cache


def update(dt):
    manager.update(dt, get_ctx())


def draw():
    manager.draw(get_ctx())


def on_key_down(key):
    manager.on_key_down(key, get_ctx())


def on_key_up(key):
    manager.on_key_up(key, get_ctx())


def on_mouse_down(pos, button):
    manager.on_mouse_down(pos, button, get_ctx())


if __name__ == "__main__":
    import pgzrun

    pgzrun.go()
