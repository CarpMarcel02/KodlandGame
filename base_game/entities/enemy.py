# base_game/entities/enemy.py
from pygame import Rect
from ..level import tiles

class Enemy:
    def __init__(self, x, y, w=24, h=24, max_hp=5):
        self.rect = Rect(x, y, w, h)
        self.max_hp = max_hp
        self.hp = max_hp
        self.alive = True

    def take_damage(self, dmg=1):
        if not self.alive:
            return
        self.hp -= int(dmg)
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def update(self, dt, room, player_rect):
        pass

    def draw(self, ctx, cam_x, cam_y):
        body = self.rect.move(-cam_x, -cam_y)
        ctx.screen.draw.filled_rect(body, (235, 235, 235))

        bw = self.rect.w
        bh = 4
        pad = 1
        max_bar = Rect(self.rect.x, self.rect.y - (bh + 3), bw, bh).move(-cam_x, -cam_y)

        ctx.screen.draw.rect(max_bar, (10, 10, 10))
        if self.max_hp > 0:
            fill_w = int((bw - 2*pad) * (self.hp / self.max_hp))
            fill = Rect(max_bar.x + pad, max_bar.y + pad, max(0, fill_w), bh - 2*pad)
            ctx.screen.draw.filled_rect(fill, (200, 50, 50))
