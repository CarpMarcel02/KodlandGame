# base_game/scenes/menu.py
from .base import BaseScene
from .. import config

class MenuScene(BaseScene):
    def draw(self, ctx):
        ctx.screen.clear()
        ctx.screen.fill((20, 16, 12))
        ctx.screen.draw.text(
            "MENU",
            center=(config.WIDTH // 2, config.HEIGHT // 2 - 30),
            fontsize=64, color="white"
        )
        ctx.screen.draw.text(
            "Press ENTER to Play",
            center=(config.WIDTH // 2, config.HEIGHT // 2 + 20),
            fontsize=32, color="gray"
        )

    def update(self, dt, ctx):
        if ctx.keyboard[ctx.keys.RETURN]:
            self.goto("play")
