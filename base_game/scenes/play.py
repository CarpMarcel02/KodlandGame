from pygame import Rect
from .base import BaseScene
from ..level.room import Room
from ..level import tiles
from ..level.procgen import generate_world


class PlayScene(BaseScene):
    SPEED = 160.0

    def on_enter(self):
        self.room = generate_world(seed=None,      
                                target_rooms=6, 
                                first_size=(20,15),
                                min_size=15, max_size=30)

        sx, sy = self.room.spawn_xy
        size = max(tiles.TILE - 4, 8)
        self.player = Rect(sx + (tiles.TILE - size)//2,
                        sy + (tiles.TILE - size)//2, size, size)
        self._half_player = size // 2
        self.room._half_player = self._half_player
        self.bullets = []
        self.fire_timer = 0.0

    def update(self, dt, ctx):
        vx = (-self.SPEED if ctx.keyboard.left  or ctx.keyboard[ctx.keys.A] else 0.0) \
        + ( self.SPEED if ctx.keyboard.right or ctx.keyboard[ctx.keys.D] else 0.0)
        vy = (-self.SPEED if ctx.keyboard.up    or ctx.keyboard[ctx.keys.W] else 0.0) \
        + ( self.SPEED if ctx.keyboard.down  or ctx.keyboard[ctx.keys.S] else 0.0)

        dx = int(round(vx * dt))
        dy = int(round(vy * dt))

        self._move_and_collide(self.player, dx, dy)

        shoot_x = int(ctx.keyboard[ctx.keys.RIGHT]) - int(ctx.keyboard[ctx.keys.LEFT])
        shoot_y = int(ctx.keyboard[ctx.keys.DOWN])  - int(ctx.keyboard[ctx.keys.UP])
        if shoot_x or shoot_y:
            self._shoot(shoot_x, shoot_y)

        self._update_bullets(dt)
        self._clamp_to_floor()  
    def _solid_at(self, gx: int, gy: int) -> bool:
        if gy < 0 or gy >= len(self.room.grid): return True
        row = self.room.grid[gy]
        if gx < 0 or gx >= len(row): return True
        return tiles.is_solid(row[gx])

    def _move_and_collide(self, r, dx: int, dy: int):
        ts = tiles.TILE

        if dx != 0:
            r.x += dx
            gy0 = r.top // ts
            gy1 = (r.bottom - 1) // ts  
            if dx > 0:  
                gx = (r.right - 1) // ts
                hit = any(self._solid_at(gx, gy) for gy in range(gy0, gy1 + 1))
                if hit:
                    r.right = gx * ts
            else:      
                gx = r.left // ts
                hit = any(self._solid_at(gx, gy) for gy in range(gy0, gy1 + 1))
                if hit:
                    r.left = (gx + 1) * ts

        if dy != 0:
            r.y += dy
            gx0 = r.left // ts
            gx1 = (r.right - 1) // ts
            if dy > 0: 
                gy = (r.bottom - 1) // ts
                hit = any(self._solid_at(gx, gy) for gx in range(gx0, gx1 + 1))
                if hit:
                    r.bottom = gy * ts
            else:       
                gy = r.top // ts
                hit = any(self._solid_at(gx, gy) for gx in range(gx0, gx1 + 1))
                if hit:
                    r.top = (gy + 1) * ts
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
        self.bullets.append([r, vx, vy, 1.2]) 

    def _update_bullets(self, dt):
        new_list = []
        for r, vx, vy, ttl in self.bullets:
            r.x += int(round(vx * dt)); r.y += int(round(vy * dt))
            ttl -= dt
            if ttl <= 0:
                continue
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
        w = len(self.room.grid[0]) * tiles.TILE
        h = len(self.room.grid)    * tiles.TILE
        if self.player.left < 0: self.player.left = 0
        if self.player.top < 0: self.player.top = 0
        if self.player.right > w: self.player.right = w
        if self.player.bottom > h: self.player.bottom = h

    def draw(self, ctx):
        ctx.screen.clear()
        sw, sh = ctx.screen.width, ctx.screen.height
        world_w = len(self.room.grid[0]) * tiles.TILE
        world_h = len(self.room.grid)    * tiles.TILE

        cam_x = max(0, min(self.player.centerx - sw // 2, world_w - sw))
        cam_y = max(0, min(self.player.centery - sh // 2, world_h - sh))

        self.room.draw(ctx, cam_offset=(-cam_x, -cam_y))

        for r, *_ in self.bullets:
            ctx.screen.draw.filled_rect(r.move(-cam_x, -cam_y), (220, 220, 60))
        ctx.screen.draw.filled_rect(self.player.move(-cam_x, -cam_y), (230, 230, 240))

        gx = self.player.centerx // tiles.TILE
        gy = self.player.centery // tiles.TILE
        try:
            tid = self.room.grid[gy][gx]
            tname = tiles.Tile(tid).name
            spr = tiles.PROPS.get(tiles.Tile(tid), {}).get("sprite")
            ctx.screen.draw.text(f"cam=({cam_x},{cam_y}) tile=({gx},{gy}) id={tid} {tname} spr='{spr}'",
                                (8, 8), fontsize=18, color=(220,220,220))
        except Exception:
            pass