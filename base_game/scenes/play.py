from pygame import Rect
from .base import BaseScene
from ..level.room import Room
from ..level import tiles

class PlayScene(BaseScene):
    SPEED = 160.0

    def on_enter(self):
        self.room = Room.from_ascii("room01")
        sx, sy = self.room.spawn_xy
        size = max(tiles.TILE - 4, 8)  # un pătrat puțin mai mic decât tile-ul
        self.player = Rect(sx + (tiles.TILE - size) // 2,
                           sy + (tiles.TILE - size) // 2, size, size)
        self.bullets = []
        self.fire_timer = 0.0

    def update(self, dt, ctx):
        vx = (-self.SPEED if ctx.keyboard.left  or ctx.keyboard[ctx.keys.A] else 0.0) \
           + ( self.SPEED if ctx.keyboard.right or ctx.keyboard[ctx.keys.D] else 0.0)
        vy = (-self.SPEED if ctx.keyboard.up    or ctx.keyboard[ctx.keys.W] else 0.0) \
           + ( self.SPEED if ctx.keyboard.down  or ctx.keyboard[ctx.keys.S] else 0.0)
        self.player.x += int(round(vx * dt))
        self.player.y += int(round(vy * dt))

        shoot_x = int(ctx.keyboard[ctx.keys.RIGHT]) - int(ctx.keyboard[ctx.keys.LEFT])
        shoot_y = int(ctx.keyboard[ctx.keys.DOWN]) - int(ctx.keyboard[ctx.keys.UP])
        if shoot_x or shoot_y:
            self._shoot(shoot_x, shoot_y)

        self._update_bullets(dt)
        self._clamp_to_floor()

        hit = None
        for tag, door_rect in self.room.doors.items():
            if self.player.colliderect(door_rect):
                hit = tag; break
        if hit:
            pass

    def _shoot(self, dx, dy):
        speed = 300.0
        if dx and dy:
            k = (2**0.5)/2
            vx = speed * (dx * k)
            vy = speed * (dy * k)
        else:
            vx = speed * dx
            vy = speed * dy
        r = Rect(self.player.centerx-3, self.player.centery-3, 6, 6)
        self.bullets.append([r, vx, vy, 1.2])  # ttl=1.2s

    def _update_bullets(self, dt):
        new_list = []
        for r, vx, vy, ttl in self.bullets:
            r.x += int(round(vx * dt)); r.y += int(round(vy * dt))
            ttl -= dt
            if ttl <= 0:
                continue
            # coliziune glonț cu ziduri
            if self._rect_hits_wall(r):
                continue
            new_list.append([r, vx, vy, ttl])
        self.bullets = new_list

    def _rect_hits_wall(self, rect: Rect) -> bool:
        ts = tiles.TILE
        gy0, gy1 = rect.top // ts, rect.bottom // ts
        gx0, gx1 = rect.left // ts, rect.right // ts
        for gy in range(gy0, gy1+1):
            if gy < 0 or gy >= len(self.room.grid): return True
            row = self.room.grid[gy]
            for gx in range(gx0, gx1+1):
                if gx < 0 or gx >= len(row): return True
                tid = row[gx]
                if tiles.is_solid(tid):
                    return True
        return False

    def _clamp_to_floor(self):
        # opțional: împiedică ieșirea din ecran
        w = len(self.room.grid[0]) * tiles.TILE
        h = len(self.room.grid)    * tiles.TILE
        if self.player.left < 0: self.player.left = 0
        if self.player.top < 0: self.player.top = 0
        if self.player.right > w: self.player.right = w
        if self.player.bottom > h: self.player.bottom = h

    def draw(self, ctx):
        ctx.screen.clear()
        self.room.draw(ctx)  # <— aici era self.level.draw(...)
        for r, *_ in self.bullets:
            ctx.screen.draw.filled_rect(r, (220, 220, 60))
        ctx.screen.draw.filled_rect(self.player, (230, 230, 240))
