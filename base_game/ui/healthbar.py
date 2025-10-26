from pygame import Rect

class HealthBar:
    def __init__(self, x=10, y_anchor="bottom", margin=10,
                 width=160, height=12,
                 bg=(40, 40, 40), fg=(60, 200, 80), border=(15, 15, 15)):
        self.x, self.margin = x, margin
        self.width, self.height = width, height
        self.y_anchor = y_anchor
        self.bg, self.fg, self.border = bg, fg, border

    def draw(self, ctx, hp, max_hp):
        if max_hp <= 0:
            return
        y = ctx.screen.height - self.height - self.margin if self.y_anchor == "bottom" else self.margin
        x = self.x
        ctx.screen.draw.rect(Rect(x-1, y-1, self.width+2, self.height+2), self.border)
        ctx.screen.draw.filled_rect(Rect(x, y, self.width, self.height), self.bg)
        p = max(0.0, min(1.0, hp / max_hp))
        fill_w = max(0, int((self.width - 2) * p))
        ctx.screen.draw.filled_rect(Rect(x+1, y+1, fill_w, self.height-2), self.fg)
