import os
from math import sqrt

from pgzero import loaders
from pgzero.loaders import images as pgz_images
from pygame import Rect

from ..entities.projectile import Projectile
from ..level import tiles

try:
    from pgzero.loaders import sounds as pgz_sounds
except Exception:
    pgz_sounds = None

loaders.set_root(os.path.dirname(__file__))


class Player:
    BULLET_SPEED = 300.0
    WALK_FRAMES = 9

    def __init__(self, spawn_x, spawn_y, size=28, speed=160.0):
        self.rect = Rect(
            spawn_x + (tiles.TILE - size) // 2, spawn_y + (tiles.TILE - size) // 2, size, size
        )
        self.speed = speed

        self.fire_cooldown = 0.15
        self.fire_timer = 0.0
        self._hurt_snd = None

        def _load_dir(base, n):
            return [pgz_images.load(f"{base}_{i}") for i in range(n)]

        frames_count = self.WALK_FRAMES

        self.anim_walk = {
            "UP": _load_dir("player/hero_walk_down", frames_count),
            "LEFT": _load_dir("player/hero_walk_left", frames_count),
            "DOWN": _load_dir("player/hero_walk_right", frames_count),
            "RIGHT": _load_dir("player/hero_walk_up", frames_count),
        }
        self.facing = "DOWN"
        self.anim_ix = 0
        self.anim_t = 0.0
        self.anim_speed = 0.10

        def _load_idle_try(base_prefix, fallback_frames):
            frames = []
            i = 0
            while True:
                name = f"{base_prefix}_{i}"
                try:
                    frames.append(pgz_images.load(name))
                    i += 1
                except Exception:
                    break
            if not frames:
                frames = [fallback_frames[0]]
            return frames

        self.anim_idle = {
            "UP": _load_idle_try("player/hero_idle_down", self.anim_walk["UP"]),
            "LEFT": _load_idle_try("player/hero_idle_left", self.anim_walk["LEFT"]),
            "DOWN": _load_idle_try("player/hero_idle_right", self.anim_walk["DOWN"]),
            "RIGHT": _load_idle_try("player/hero_idle_up", self.anim_walk["RIGHT"]),
        }

        self.facing = "DOWN"
        self.is_moving = False

        self.walk_ix = 0
        self.walk_t = 0.0
        self.walk_speed = 0.10

        self.idle_ix = 0
        self.idle_t = 0.0
        self.idle_speed = 0.25
        self.max_hp = 6
        self.hp = self.max_hp

        self.invuln_time = 0.60
        self.invuln = 0.0

        self.sfx_muted = False

    def _move_and_collide(self, dx, dy, solid_at, hits_blocker):
        ts = tiles.TILE
        r = self.rect

        if dx != 0:
            r.x += dx
            gy0 = r.top // ts
            gy1 = (r.bottom - 1) // ts
            if dx > 0:
                gx = (r.right - 1) // ts
                if any(solid_at(gx, gy) for gy in range(gy0, gy1 + 1)):
                    r.right = gx * ts
            else:
                gx = r.left // ts
                if any(solid_at(gx, gy) for gy in range(gy0, gy1 + 1)):
                    r.left = (gx + 1) * ts

            br = hits_blocker(r)
            if br:
                if dx > 0:
                    r.right = min(r.right, br.left)
                else:
                    r.left = max(r.left, br.right)

        if dy != 0:
            r.y += dy
            gx0 = r.left // ts
            gx1 = (r.right - 1) // ts
            if dy > 0:
                gy = (r.bottom - 1) // ts
                if any(solid_at(gx, gy) for gx in range(gx0, gx1 + 1)):
                    r.bottom = gy * ts
            else:
                gy = r.top // ts
                if any(solid_at(gx, gy) for gx in range(gx0, gx1 + 1)):
                    r.top = (gy + 1) * ts

            br = hits_blocker(r)
            if br:
                if dy > 0:
                    r.bottom = min(r.bottom, br.top)
                else:
                    r.top = max(r.top, br.bottom)

    def update(self, dt, input_vec, solid_at, hits_blocker):
        self.invuln = max(0.0, self.invuln - dt)

        dx, dy = input_vec
        self._move_and_collide(dx, dy, solid_at, hits_blocker)

        self.fire_timer = max(0.0, self.fire_timer - dt)

        if abs(dx) > abs(dy):
            if dx > 0:
                self.facing = "RIGHT"
            elif dx < 0:
                self.facing = "LEFT"
        else:
            if dy > 0:
                self.facing = "DOWN"
            elif dy < 0:
                self.facing = "UP"

        self.is_moving = dx != 0 or dy != 0

        if self.is_moving:
            self.walk_t += dt
            if self.walk_t >= self.walk_speed:
                self.walk_t = 0.0
                self.walk_ix = (self.walk_ix + 1) % len(self.anim_walk[self.facing])
            self.idle_t = 0.0
            self.idle_ix = 0
        else:
            self.idle_t += dt
            if self.idle_t >= self.idle_speed:
                self.idle_t = 0.0
                self.idle_ix = (self.idle_ix + 1) % len(self.anim_idle[self.facing])
            self.walk_ix = 0
            self.walk_t = 0.0

    def draw(self, ctx, cam_x, cam_y):
        if self.is_moving:
            frames = self.anim_walk[self.facing]
            ix = min(self.walk_ix, len(frames) - 1)
            frame = frames[ix]
        else:
            frames = self.anim_idle[self.facing]
            ix = min(self.idle_ix, len(frames) - 1)
            frame = frames[ix]

        draw_x = self.rect.centerx - frame.get_width() // 2 - cam_x
        draw_y = self.rect.bottom - frame.get_height() - cam_y
        ctx.screen.blit(frame, (draw_x, draw_y))

    def try_shoot(self, dir_x, dir_y):

        if (dir_x == 0 and dir_y == 0) or self.fire_timer > 0.0:
            return None

        if dir_x and dir_y:
            k = sqrt(0.5)
            vx = self.BULLET_SPEED * dir_x * k
            vy = self.BULLET_SPEED * dir_y * k
        else:
            vx = self.BULLET_SPEED * dir_x
            vy = self.BULLET_SPEED * dir_y

        cx, cy = self.rect.centerx, self.rect.centery
        p = Projectile(cx, cy, w=6, h=6, vx=vx, vy=vy, ttl=1.2, dmg=1)

        self.fire_timer = self.fire_cooldown
        return p

    def take_damage(self, dmg=1):
        if self.invuln > 0.0 or self.hp <= 0:
            return
        self.hp = max(0, self.hp - int(dmg))
        self.invuln = self.invuln_time
        self._play_hurt_sound()

    def _play_hurt_sound(self):
        if pgz_sounds is None or self.sfx_muted:
            return
        if self._hurt_snd is None:
            try:
                self._hurt_snd = pgz_sounds.load("roblox_sound")
                self._hurt_snd.set_volume(0.03)
            except Exception as e:
                print("HURT SFX missing:", e)
                return
        try:
            self._hurt_snd.play()
        except Exception as e:
            print("HURT SFX couldn't play:", e)

    def set_sfx_muted(self, flag: bool):
        self.sfx_muted = bool(flag)
