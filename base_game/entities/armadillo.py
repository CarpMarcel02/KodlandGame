import math, random
from pygame import Rect
from .enemy import Enemy, _hit_wall, _hit_obstacle
from ..utils.animation import Animation

class _NoDirAnim:
    def __init__(self, anim: Animation):
        self.anim = anim
    def set_dir(self, _): 
        pass
    def update(self, dt, playing=True):
        self.anim.update(dt, playing)
    def get(self):
        return self.anim.get()

class ArmadilloEnemy(Enemy):
    ROLL_TIME   = 15.0   
    REST_TIME   = 3.0   
    WINDUP_TIME = 0.30  

    ROLL_SPEED  = 240.0  
    CONTACT_DAMAGE = 1
    CONTACT_COOLDOWN = 0.35

    def __init__(self, x, y):
        super().__init__(x, y, w=22, h=22, max_hp=10, speed=self.ROLL_SPEED, counts_for_clear=True)

        windup_names = [f"enemies/armadillo/arm_roll_{i}" for i in range(0, 4)]
        roll_names   = [f"enemies/armadillo/arm_roll_{i}" for i in range(4, 8)]

        idle_names = [f"enemies/armadillo/arm_idle_{i}" for i in range(8)]

        self.anim_windup = _NoDirAnim(Animation(windup_names, fps=12))   
        self.anim_roll   = _NoDirAnim(Animation(roll_names,   fps=14))   
        self.anim_idle   = None
        try:

            self.anim_idle = _NoDirAnim(Animation(idle_names, fps=6))
        except Exception:
            self.anim_idle = None

        fallback_idle = _NoDirAnim(Animation([windup_names[0]], fps=1))
        self.anim = self.anim_idle or fallback_idle

        self.state = "REST"                 
        self._state_t = random.uniform(0.2, 0.6) 
        self._contact_cd = 0.0

        self._dirx, self._diry = self._random_dir()

    def _random_dir(self):
        ang = random.uniform(0.0, math.tau)
        return math.cos(ang), math.sin(ang)

    def _set_anim(self, which):
        if self.anim is which:  
            return
        self.anim = which
        try:
            self.anim.anim.i = 0
            self.anim.anim.t = 0.0
        except Exception:
            pass

    def sense(self, dt, room, player_rect):
        self._contact_cd = max(0.0, self._contact_cd - dt)

    def think(self, dt, room, player_rect):
        self._state_t -= dt

        if self.state == "REST":
            self._vx = self._vy = 0.0
            self._set_anim(self.anim_idle or self.anim_windup)  
            if self._state_t <= 0.0:
                self.state = "WINDUP"
                self._state_t = self.WINDUP_TIME
                self._set_anim(self.anim_windup)

        elif self.state == "WINDUP":
            self._vx = self._vy = 0.0
            if self._state_t <= 0.0:
                self.state = "ROLL"
                self._state_t = self.ROLL_TIME
                dx = player_rect.centerx - self.rect.centerx
                dy = player_rect.centery - self.rect.centery
                L = math.hypot(dx, dy)
                if L < 1e-6:
                    self._dirx, self._diry = self._random_dir()
                else:
                    nx, ny = dx / L, dy / L
                    jitter = random.uniform(-0.35, 0.35)
                    ca, sa = math.cos(jitter), math.sin(jitter)
                    self._dirx = nx * ca - ny * sa
                    self._diry = ny * ca + nx * sa
                self._vx = self._dirx * self.ROLL_SPEED
                self._vy = self._diry * self.ROLL_SPEED
                self._set_anim(self.anim_roll)

        elif self.state == "ROLL":
            self._vx = self._dirx * self.ROLL_SPEED
            self._vy = self._diry * self.ROLL_SPEED
            if self._state_t <= 0.0:
                self.state = "REST"
                self._state_t = self.REST_TIME
                self._set_anim(self.anim_idle or self.anim_windup)

    def move(self, dt, room):
        if not self.alive:
            return
        dx = int(round(self._vx * dt))
        dy = int(round(self._vy * dt))

        bounced = False

        if dx != 0:
            nx = self.rect.x + dx
            if not _hit_obstacle(room, nx, self.rect.y, self.rect.w, self.rect.h):  
                self.rect.x = nx
            else:
                self._dirx *= -1.0
                self._vx   *= -1.0
                bounced = True

        if dy != 0:
            ny = self.rect.y + dy
            if not _hit_obstacle(room, self.rect.x, ny, self.rect.w, self.rect.h): 
                self.rect.y = ny
            else:
                self._diry *= -1.0
                self._vy   *= -1.0
                bounced = True

        if bounced:
            ang = math.atan2(self._diry, self._dirx) + random.uniform(-0.25, 0.25)
            self._dirx, self._diry = math.cos(ang), math.sin(ang)

        if abs(self._vx) > abs(self._vy):
            self.last_dir = "right" if self._vx > 0 else "left"
        elif abs(self._vy) > 0:
            self.last_dir = "down" if self._vy > 0 else "up"

    def act(self, dt, room, player_rect):
        if self.state == "ROLL" and self._contact_cd <= 0.0:
            if self.rect.colliderect(player_rect):
                self._contact_cd = self.CONTACT_COOLDOWN
                return ("HIT_PLAYER", self.CONTACT_DAMAGE)
        return None

    def draw(self, ctx, cam_x, cam_y):
        super().draw(ctx, cam_x, cam_y)
