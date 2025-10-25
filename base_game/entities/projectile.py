# base_game/entities/projectile.py
from pygame import Rect

class Projectile:
    __slots__ = ("rect", "vx", "vy", "ttl", "dmg", "alive")

    def __init__(self, x, y, w=6, h=6, vx=0.0, vy=0.0, ttl=1.2, dmg=1):
        self.rect = Rect(int(x - w//2), int(y - h//2), w, h)
        self.vx   = float(vx)
        self.vy   = float(vy)
        self.ttl  = float(ttl)
        self.dmg  = int(dmg)
        self.alive = True

    def update(self, dt):
        if not self.alive:
            return
        self.rect.x += int(round(self.vx * dt))
        self.rect.y += int(round(self.vy * dt))
        self.ttl -= dt
        if self.ttl <= 0:
            self.alive = False
