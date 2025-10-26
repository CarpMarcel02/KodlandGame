from pygame import Rect
from .base import BaseScene
try:
    from pgzero import music
except Exception:
    music = None

class YouWinScene(BaseScene):
    def on_enter(self, muted=False):
        self.muted = bool(muted)
        self._btn_cache = None
        try:
            if music:
                music.stop()
        except Exception:
            pass

    def update(self, dt, ctx):
        pass

    def draw(self, ctx):
        sw, sh = ctx.screen.width, ctx.screen.height
        ctx.screen.clear()
        ctx.screen.draw.filled_rect(Rect(0, 0, sw, sh), (0, 0, 0))

        ctx.screen.draw.text("YOU WIN!",
                             center=(sw//2, sh//2 - 80),
                             fontsize=56, color=(90, 220, 90))

        btns = self._layout_buttons(ctx)
        self._draw_button(ctx, btns["again"], "Play Again")
        self._draw_button(ctx, btns["menu"],  "Main Menu")

    def on_mouse_down(self, pos, button, ctx):
        if button != 1:
            return
        btns = self._layout_buttons(ctx)
        if btns["again"].collidepoint(pos):
            self._play_again()
        elif btns["menu"].collidepoint(pos):
            self._to_menu()

    def on_key_down(self, key, *args):
        ctx = args[-1] if args else None
        if ctx is None:
            return
        K = ctx.keys
        if key == K.ESCAPE:
            self._to_menu()

    def _layout_buttons(self, ctx):
        if self._btn_cache:
            return self._btn_cache
        sw, sh = ctx.screen.width, ctx.screen.height
        W, H, GAP = 220, 48, 18
        x = (sw - W) // 2
        y0 = sh // 2 - H // 2
        again = Rect(x, y0, W, H)
        menu  = Rect(x, y0 + H + GAP, W, H)
        self._btn_cache = {"again": again, "menu": menu}
        return self._btn_cache

    def _draw_button(self, ctx, r, text):
        ctx.screen.draw.filled_rect(r, (38, 38, 38))
        ctx.screen.draw.rect(r, (220, 220, 220))
        ctx.screen.draw.text(text, center=(r.centerx, r.centery),
                             fontsize=28, color=(235, 235, 235))

    def _play_again(self):
        self._manager.change("play", muted=self.muted)

    def _to_menu(self):
        try:
            if music:
                music.stop()
        except Exception:
            pass
        self._manager.change("menu")
