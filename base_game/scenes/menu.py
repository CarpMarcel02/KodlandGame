import sys

from pygame import Rect

from .. import config
from .base import BaseScene


class MenuScene(BaseScene):
    def on_enter(self):
        self.btn_w, self.btn_h = 240, 60
        self.color_btn = (70, 70, 70)
        self.color_hover = (110, 110, 110)
        self.color_text = (255, 255, 255)
        self.hovered = None

        self.center_x = config.WIDTH // 2
        self.center_y = config.HEIGHT // 2

        self.buttons = {
            "play": Rect(self.center_x - self.btn_w // 2, self.center_y, self.btn_w, self.btn_h),
            "exit": Rect(
                self.center_x - self.btn_w // 2, self.center_y + 80, self.btn_w, self.btn_h
            ),
        }

    def draw(self, ctx):
        ctx.screen.clear()
        ctx.screen.fill((20, 16, 12))

        ctx.screen.draw.text(
            "Marcel's Game",
            center=(self.center_x, self.center_y - 150),
            fontsize=72,
            color=(255, 255, 255),
            shadow=(2, 2),
        )

        mouse_x, mouse_y = getattr(ctx, "mouse_pos", (0, 0))
        self.hovered = None

        for name, rect in self.buttons.items():
            is_hover = rect.collidepoint(mouse_x, mouse_y)
            if is_hover:
                self.hovered = name
            ctx.screen.draw.filled_rect(rect, self.color_hover if is_hover else self.color_btn)

            label = "Play Game" if name == "play" else "Exit Game"
            ctx.screen.draw.text(label, center=rect.center, fontsize=32, color=self.color_text)

    def on_mouse_down(self, pos, button, ctx):
        if button != 1:
            return
        x, y = pos
        if self.buttons["play"].collidepoint(x, y):
            from pgzero import music

            music.stop()
            self._manager.change("play")
            return
        if self.buttons["exit"].collidepoint(x, y):
            sys.exit(0)

    def update(self, dt, ctx):
        ctx.mouse_pos = getattr(ctx, "mouse_pos", (0, 0))
