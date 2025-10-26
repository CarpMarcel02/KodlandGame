import math
from pygame import Rect
from .enemy import Enemy
from ..utils.animation import Animation, DirectionalAnimation
from pgzero.loaders import images as pgz_images
import random

def _norm(vx, vy):
    length = math.hypot(vx, vy)
    if length <= 1e-6:
        return 0.0, 0.0
    return vx / length, vy / length

class SkeletonEnemy(Enemy):
    ATTACK_RANGE     = 30
    ATTACK_COOLDOWN  = 0.80
    CONTACT_DAMAGE   = 1
    ATTACK_ANIM_TIME = 0.35  

    def __init__(self, x, y):
        super().__init__(x, y, w=24, h=24, max_hp=8, speed=110, counts_for_clear=True)
        self._atk_cd   = 0.0
        self._attack_t = 0.0
        self._attack_dir = "down"
        self._orbit_sign = 1 if random.random() < 0.5 else -1 
        self._side_t = 0.0       
        self._side_sign = 0    
        self._detour = None       
        self._detour_timer = 0.0   
        self._blocked_t = 0.0    
        def frames_fixed(prefix, n):
            return [f"enemies/skeleton/{prefix}_{i}" for i in range(n)]
       
        def frames_existing(prefix, max_frames=12):
            names = []
            for i in range(max_frames):
                name = f"enemies/skeleton/{prefix}_{i}"
                try:
                    pgz_images.load(name) 
                    names.append(name)
                except Exception:
                    break
            return names or [f"enemies/skeleton/{prefix}_0"]

        self.anim = DirectionalAnimation({
            "down":  Animation(frames_fixed("skel_walk_right", 6), fps=10),
            "up":    Animation(frames_fixed("skel_walk_down",  6), fps=10),
            "left":  Animation(frames_fixed("skel_walk_left",  6), fps=10),
            "right": Animation(frames_fixed("skel_walk_up",    6), fps=10),
        }, default_dir="down")

        self.anim_attack = DirectionalAnimation({
            "down":  Animation(frames_existing("skel_slash_right"), fps=12),
            "up":    Animation(frames_existing("skel_slash_down"),  fps=12),
            "left":  Animation(frames_existing("skel_slash_left"),  fps=12),
            "right": Animation(frames_existing("skel_slash_up"),    fps=12),
        }, default_dir="down")

        self._atk_cd = 0.0
        self._attack_t = 0.0   
    def act(self, dt, room, player_rect: Rect):
        if self._atk_cd <= 0.0 and self._edge_gap(self.rect, player_rect) <= 3.0:
            self._atk_cd = self.ATTACK_COOLDOWN
            self._attack_t = self.ATTACK_ANIM_TIME
            self._attack_dir = self.last_dir  

            try:
                a = self.anim_attack.anims[self._attack_dir]
                a.i = 0
                a.t = 0.0
            except Exception:
                pass

            return ("HIT_PLAYER", self.CONTACT_DAMAGE)

        return None
    
    def think(self, dt, room, player_rect: Rect):
        self._atk_cd = max(0.0, self._atk_cd - dt)

        if self._attack_t > 0.0 and self._edge_gap(self.rect, player_rect) > 6.0:
            self._attack_t = 0.0
            self._side_t = 0.0
            self._side_sign = 0

        prev = self._attack_t
        self._attack_t = max(0.0, self._attack_t - dt)
        if prev > 0.0 and self._attack_t == 0.0:
            self._side_t = 0.0
            self._side_sign = 0

        self._detour_timer = max(0.0, self._detour_timer - dt)
        if self._detour_timer == 0.0:
            self._detour = None

        self._blocked_t = max(0.0, self._blocked_t - dt*0.5)

    def _edge_gap(self, a: Rect, b: Rect) -> float:
        dx = 0
        if a.right < b.left: dx = b.left - a.right
        elif b.right < a.left: dx = a.left - b.right
        dy = 0
        if a.bottom < b.top: dy = b.top - a.bottom
        elif b.bottom < a.top: dy = a.top - b.bottom
        return (dx*dx + dy*dy) ** 0.5
    
    def _pick_detour_target(self, player_rect: Rect, nx: float, ny: float, others):
        import math
        px, py = player_rect.centerx, player_rect.centery
        R = max(24, self.ATTACK_RANGE + 6) 
        tx, ty = -ny, nx

        candidates = [
            ( px + (nx*math.cos(math.radians(45)) - ny*math.sin(math.radians(45))) * R,
            py + (ny*math.cos(math.radians(45)) + nx*math.sin(math.radians(45))) * R ),
            ( px + (nx*math.cos(math.radians(-45)) - ny*math.sin(math.radians(-45))) * R,
            py + (ny*math.cos(math.radians(-45)) + nx*math.sin(math.radians(-45))) * R ),
        ]

        best = None
        best_score = 1e9
        for cx, cy in candidates:
            probe = Rect(int(cx)-8, int(cy)-8, 16, 16)
            overlaps = sum(probe.colliderect(r) for r in others)
            d = (cx - self.rect.centerx)**2 + (cy - self.rect.centery)**2
            score = overlaps*1000 + d
            if score < best_score:
                best_score = score
                best = (cx, cy)
        return best
    
    def sense(self, dt, room, player_rect: Rect):
        dx = player_rect.centerx - self.rect.centerx
        dy = player_rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist > 1e-6:
            nx, ny = dx / dist, dy / dist
        else:
            nx, ny = 0.0, 0.0

        vx = vy = 0.0

        if self._attack_t > 0.0:
            gap = self._edge_gap(self.rect, player_rect)
            if gap > 0.5:
                vx += nx * 0.35
                vy += ny * 0.35
        else:
            ATTACK_ZONE = self.ATTACK_RANGE
            FLEX        = 4
            tx, ty = -ny, nx  

            others = [r for r in getattr(room, "_enemy_rects", []) if r is not self.rect]
            AHEAD = 16; PAD = 4
            ahead = self.rect.inflate(PAD, PAD).move(int(nx*AHEAD), int(ny*AHEAD))
            blocked = any(ahead.colliderect(r) for r in others)

            if blocked:
                self._blocked_t += dt
            else:
                self._blocked_t = max(0.0, self._blocked_t - dt*0.5)

            if self._detour and self._detour_timer > 0.0:
                txg = self._detour[0] - self.rect.centerx
                tyg = self._detour[1] - self.rect.centery
                Lg = math.hypot(txg, tyg)
                if Lg > 1e-6:
                    vx += (txg / Lg)
                    vy += (tyg / Lg)
                if Lg <= 6.0 or self._blocked_t <= 0.05:
                    self._detour = None
                    self._detour_timer = 0.0

            else:
                if dist > ATTACK_ZONE + FLEX:
                    vx += nx; vy += ny
                elif dist < ATTACK_ZONE - FLEX:
                    vx -= nx; vy -= ny
                else:
                    if self._edge_gap(self.rect, player_rect) > 0.5:
                        vx += nx * 0.5
                        vy += ny * 0.5

                if self._detour is None and self._blocked_t > 0.12:
                    tgt = self._pick_detour_target(player_rect, nx, ny, others)
                    if tgt:
                        self._detour = tgt
                        self._detour_timer = 0.40

            SEP_RADIUS = 30 if dist <= (self.ATTACK_RANGE + 6) else 28
            SEP_R2 = SEP_RADIUS * SEP_RADIUS
            for r in getattr(room, "_enemy_rects", []):
                if r is self.rect:
                    continue
                dx2 = self.rect.centerx - r.centerx
                dy2 = self.rect.centery - r.centery
                d2 = dx2*dx2 + dy2*dy2
                if 0 < d2 < SEP_R2:
                    inv = 1.0 / (math.sqrt(d2) + 1e-6)
                    push = 0.7 if dist <= (self.ATTACK_RANGE + 6) else 0.6
                    vx += dx2 * inv * push
                    vy += dy2 * inv * push

        L = math.hypot(vx, vy)
        if L > 1e-6:
            self._vx = (vx / L) * self.speed
            self._vy = (vy / L) * self.speed
        else:
            self._vx = self._vy = 0.0


    def draw(self, ctx, cam_x, cam_y):
        if self._attack_t > 0.0 and self.anim_attack:
            self.anim_attack.set_dir(self._attack_dir)  
            self.anim_attack.update(1/60.0, True)
            img = self.anim_attack.get()
        else:
            if self.anim:
                self.anim.set_dir(self.last_dir)
            img = self.anim.get() if self.anim else None

        if img:
            pos_x = self.rect.centerx - cam_x - img.get_width() // 2
            pos_y = self.rect.bottom  - cam_y - img.get_height()
            ctx.screen.blit(img, (pos_x, pos_y))
            self._draw_hp_bar(ctx, cam_x, cam_y)
        else:
            super().draw(ctx, cam_x, cam_y)
