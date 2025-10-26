from pygame import Rect

from ..level import tiles


def _tile_size():
    return getattr(tiles, "TILE_SIZE", 32)


def _hit_wall(room, x, y, w, h):
    ts = _tile_size()
    points = [(x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)]
    for px, py in points:
        gx = int(px // ts)
        gy = int(py // ts)
        if room._is_wall(gx, gy):
            return True
    return False


def _hit_obstacle(room, x, y, w, h):
    if _hit_wall(room, x, y, w, h):
        return True
    fn = getattr(room, "rect_hits_blocker", None)
    if fn:
        return bool(fn(Rect(int(x), int(y), int(w), int(h))))
    return False


class Enemy:
    def __init__(self, x, y, w=24, h=24, max_hp=5, speed=100, counts_for_clear=True):
        self.rect = Rect(x, y, w, h)
        self.max_hp = max_hp
        self.hp = max_hp
        self.alive = True
        self.speed = float(speed)
        self.counts_for_clear = counts_for_clear

        self.anim = None
        self.last_dir = "down"

        self._vx = 0.0
        self._vy = 0.0
        self.pushable = True

    def take_damage(self, dmg=1):
        if not self.alive:
            return
        self.hp -= int(dmg)
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def sense(self, dt, room, player_rect):
        pass

    def think(self, dt, room, player_rect):
        pass

    def move(self, dt, room):
        if not self.alive:
            return
        dx = self._vx * dt
        dy = self._vy * dt

        new_x = self.rect.x + dx
        if not _hit_wall(room, new_x, self.rect.y, self.rect.w, self.rect.h):
            self.rect.x = int(new_x)
        else:
            pass

        new_y = self.rect.y + dy
        if not _hit_wall(room, self.rect.x, new_y, self.rect.w, self.rect.h):
            self.rect.y = int(new_y)
        else:
            pass

        if abs(self._vx) > abs(self._vy):
            self.last_dir = "right" if self._vx > 0 else "left"
        elif abs(self._vy) > 0:
            self.last_dir = "down" if self._vy > 0 else "up"

    def act(self, dt, room, player_rect):
        return None

    def post_update(self, dt, room):
        pass

    def update(self, dt, room, player_rect):
        if not self.alive:
            return None

        self.sense(dt, room, player_rect)
        self.think(dt, room, player_rect)
        self.move(dt, room)
        evt = self.act(dt, room, player_rect)
        self.post_update(dt, room)

        if self.anim:
            moving = (abs(self._vx) + abs(self._vy)) > 1e-3
            self.anim.set_dir(self.last_dir)
            self.anim.update(dt, moving)

        return evt

    def _draw_hp_bar(self, ctx, cam_x, cam_y, color=(200, 50, 50)):
        bw = self.rect.w
        bh = 4
        pad = 1
        max_bar = Rect(self.rect.x, self.rect.y - (bh + 3), bw, bh).move(-cam_x, -cam_y)
        ctx.screen.draw.rect(max_bar, (10, 10, 10))
        if self.max_hp > 0:
            fill_w = int((bw - 2 * pad) * (self.hp / self.max_hp))
            if fill_w > 0:
                fill = Rect(max_bar.x + pad, max_bar.y + pad, fill_w, bh - 2 * pad)
                ctx.screen.draw.filled_rect(fill, color)

    def draw(self, ctx, cam_x, cam_y):
        if self.anim:
            img = self.anim.get()
            pos_x = self.rect.centerx - cam_x - img.get_width() // 2
            pos_y = self.rect.bottom - cam_y - img.get_height()
            ctx.screen.blit(img, (pos_x, pos_y))
        else:
            body = self.rect.move(-cam_x, -cam_y)
            ctx.screen.draw.filled_rect(body, (235, 235, 235))

        self._draw_hp_bar(ctx, cam_x, cam_y)
