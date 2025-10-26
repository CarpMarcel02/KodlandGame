from pygame import Rect
from .enemy import Enemy
from ..utils.animation import Animation, DirectionalAnimation
from ..entities.projectile import Projectile

class PlantEnemy(Enemy):
    SPIT_COOLDOWN = 1.25
    SPIT_FRAME    = 2     
    BULLET_SPEED  = 230.0
    BULLET_TTL    = 2.0
    BULLET_DMG    = 1
    
    CONTACT_DAMAGE   = 1        
    CONTACT_COOLDOWN = 0.40    

    def __init__(self, x, y, facing="down"):
        super().__init__(x, y, w=24, h=24, max_hp=6, speed=0, counts_for_clear=True)
        self.facing = facing
        self.last_dir = facing
        self._spit_cd = 0.0
        self._shoot_gate = False
        self._want_shoot = False
        self.pushable = False
        self._touch_cd = 0.0     
        self._seq_playing = False   
        self._shot_this_seq = False     
        self._prev_i = 0

        def frames_dir(dir_name):
            return [f"plant/plant_{i}_{dir_name}" for i in range(1, 9)]

        self.anim_idle = DirectionalAnimation({
            "down":  Animation(frames_dir("up"),  fps=8),
            "left":  Animation(frames_dir("right"),  fps=8),
            "up":    Animation(frames_dir("down"),    fps=8),
            "right": Animation(frames_dir("left"), fps=8),
        }, default_dir=facing)
        a0 = self.anim_idle.anims[self.facing]

        self.anim = self.anim_idle
        self._frames_count = len(getattr(a0, "frames", [])) or 8

    def sense(self, dt, room, player_rect):
        self._spit_cd = max(0.0, self._spit_cd - dt)
        self._touch_cd = max(0.0, self._touch_cd - dt)   
        self._vx = 0.0
        self._vy = 0.0
        self.last_dir = self.facing


    def _make_seed(self):
        if self.facing == "down":
            vx, vy = 0.0,  self.BULLET_SPEED
            sprite = "plant/projectiles/seed_projectile_down"
        elif self.facing == "up":
            vx, vy = 0.0, -self.BULLET_SPEED
            sprite = "plant/projectiles/seed_projectile_up"
        elif self.facing == "left":
            vx, vy = -self.BULLET_SPEED, 0.0
            sprite = "plant/projectiles/seed_projectile_left"
        else:
            vx, vy =  self.BULLET_SPEED, 0.0
            sprite = "plant/projectiles/seed_projectile_right"

        cx, cy = self.rect.centerx, self.rect.centery
        p = Projectile(cx, cy, w=8, h=8, vx=vx, vy=vy, ttl=self.BULLET_TTL, dmg=self.BULLET_DMG)
        p.team = "enemy"   
        p.sprite = sprite   
        p.owner = "plant"   
        return p

    def update(self, dt, room, player_rect):
            if not self.alive:
                return None

            self.sense(dt, room, player_rect)

            self.anim.set_dir(self.facing)
            a = self.anim_idle.anims[self.facing]

            if self._touch_cd <= 0.0 and self.rect.colliderect(player_rect):
                self._touch_cd = self.CONTACT_COOLDOWN
                return ("HIT_PLAYER", self.CONTACT_DAMAGE)
            
            if not self._seq_playing:
                try:
                    a.i = 0
                    a.t = 0.0
                except Exception:
                    pass

                if self._spit_cd <= 0.0:
                    self._seq_playing = True
                    self._shot_this_seq = False
                    self._prev_i = 0
                return None  

            prev_i = int(getattr(a, "i", 0))
            self.anim.update(dt, True)
            cur_i = int(getattr(a, "i", prev_i))

            evt = None
            if (not self._shot_this_seq) and (cur_i == self.SPIT_FRAME) and (cur_i != prev_i):
                evt = ("SPAWN_ENEMY_PROJECTILE", self._make_seed())
                self._shot_this_seq = True

            last_ix = self._frames_count - 1
            if (cur_i == last_ix) and (cur_i != prev_i):
                self._seq_playing = False
                self._spit_cd = self.SPIT_COOLDOWN
                try:
                    a.i = 0
                    a.t = 0.0
                except Exception:
                    pass

            self._prev_i = cur_i
            return evt