from pygame import Rect
from .base import BaseScene
from ..level.room import Room
from ..level import tiles
from pgzero.loaders import images as pgz_images
from ..entities.enemy import Enemy
from ..level.procgen import generate_world
from ..entities.player import Player
from pgzero import music
import os, random





class PlayScene(BaseScene):
    SPEED = 160.0

    def on_enter(self):
        self.room = generate_world(seed=None,      
                                target_rooms=6, 
                                first_size=(20,15),
                                min_size=15, max_size=30)

        rm = self.room

        print("\n=== WORLD META ===")
        print(f"[START] room_id = {getattr(rm, 'start_room_id', '?')}")
        print(f"[ROOMS] total = {len(getattr(rm, 'rooms_meta', []))}")
        print(f"[DOORS] total = {len(getattr(rm, 'door_meta', {}))}")

        if hasattr(rm, "adj"):
            print("[ADJ]")
            for rid, neigh in rm.adj.items():
                print(f"  room {rid} -> {neigh}")

        if hasattr(rm, "rooms_meta"):
            print("[ROOMS_META]")
            for r in rm.rooms_meta:
                rg = r["rect_g"]; ri = r["rect_inner_g"]
                print(f"  [room {r['id']}] state={r['state']} "
                    f"full=({rg.x},{rg.y},{rg.w},{rg.h}) "
                    f"inner=({ri.x},{ri.y},{ri.w},{ri.h}) "
                    f"doors={len(r['doors'])}")

        if hasattr(rm, "door_meta"):
            print("[DOOR_META]")
            for key, info in rm.door_meta.items():
                orient, gx, gy = key
                rp = info["rect_px"]
                a, b = info["rooms"]
                print(f"  door key={key} orient={orient} gx,gy=({gx},{gy}) "
                    f"px=({rp.x},{rp.y},{rp.w},{rp.h}) rooms=({a},{b})")
        print("=== END META ===\n")

        self.room_state = [m["state"] for m in self.room.rooms_meta]  
        self.current_room_id = None

        self.door_state = {}     
        self.door_blockers = {}  
        self.room.door_state = self.door_state

        self.active_enemies = []

        self.pending_lock = None          
        self.lock_delay_default = 0.15   
        self.lock_depth_px = 24          
        
        start_id = getattr(self.room, "start_room_id", 0)

        for key in self.room.rooms_meta[start_id]["doors"]:
            self._set_door_open(key, True)

        sx, sy = self.room.spawn_xy
        size = max(tiles.TILE - 4, 8)

        self.player_ent = Player(sx, sy, size=size, speed=self.SPEED)
        self.player = self.player_ent.rect



        self._half_player = size // 2
        self.room._half_player = self._half_player

        self.projectiles = []
        
        music_folder = os.path.join(os.path.dirname(__file__), "..", "music", "playtime")
        self.music_tracks = [f for f in os.listdir(music_folder) if f.lower().endswith((".ogg", ".mp3", ".wav"))]
        self.music_index = random.randrange(len(self.music_tracks)) if self.music_tracks else 0
        self.music_muted = False

        if self.music_tracks:
            try:
                music.play(os.path.join("playtime", self.music_tracks[self.music_index]))
                music.set_volume(0.5)
                self._loop_music = True
            except Exception as e:
                print("Music load failed:", e)
        self.btn_mute_img = pgz_images.load("ui/mute")
        self.btn_unmute_img = pgz_images.load("ui/unmute")
        self.btn_size = 36
        self.btn_margin = 35


    def _room_center_px(self, rid):
        cx_g, cy_g = self.room.rooms_meta[rid]["center_g"]
        return cx_g * tiles.TILE + tiles.TILE//2, cy_g * tiles.TILE + tiles.TILE//2

    def _room_entry_depth_px(self, rid, px, py):
        rcx, rcy = self._room_center_px(rid)
        depths = []
        for key in self.room.rooms_meta[rid]["doors"]:
            info = self.room.door_meta[key]
            r = info["rect_px"]; orient = info["orient"]
            if orient == "H":
                if rcy > r.centery:
                    depths.append(py - r.bottom)   
                else:
                    depths.append(r.top - py)      
            else:
                if rcx > r.centerx:
                    depths.append(px - r.right)    
                else:
                    depths.append(r.left - px)     
        if not depths:
            return 9999
        return max(0, min(depths)) 
    
    def update(self, dt, ctx):
        # Movement
        vx = (-self.SPEED if ctx.keyboard[ctx.keys.A] else 0.0) \
        + ( self.SPEED if ctx.keyboard[ctx.keys.D] else 0.0)
        vy = (-self.SPEED if ctx.keyboard[ctx.keys.W] else 0.0) \
        + ( self.SPEED if ctx.keyboard[ctx.keys.S] else 0.0)

        dx = int(round(vx * dt))
        dy = int(round(vy * dt))

        #  player logic
        self.player_ent.update(
            dt,
            (dx, dy),
            solid_at=self._solid_at,
            hits_blocker=self._rect_hits_blocker
        )

        self._clamp_to_floor()

        # current room
        gx = self.player.centerx // tiles.TILE
        gy = self.player.centery // tiles.TILE
        rid = self._room_id_at(gx, gy)

        if rid != self.current_room_id:
            self.current_room_id = rid
            if rid is not None and self.room_state[rid] == "unvisited":
                self.pending_lock = {"rid": rid, "timer": self.lock_delay_default}
                self.room_state[rid] = "arming"

        if self.pending_lock:
            ar = self.pending_lock
            if self.current_room_id != ar["rid"]:
                self.room_state[ar["rid"]] = "unvisited"
                self.pending_lock = None
            else:
                ar["timer"] -= dt
                px, py = self.player.centerx, self.player.centery
                depth = self._room_entry_depth_px(ar["rid"], px, py)
                if ar["timer"] <= 0.0 and depth >= self.lock_depth_px:
                    for key in self.room.rooms_meta[ar["rid"]]["doors"]:
                        self._set_door_open(key, False)
                    self._spawn_enemies_for_room(ar["rid"])
                    self.room_state[ar["rid"]] = "locked"
                    self.pending_lock = None

        #  SHOOT
        shoot_x = int(ctx.keyboard[ctx.keys.RIGHT]) - int(ctx.keyboard[ctx.keys.LEFT])
        shoot_y = int(ctx.keyboard[ctx.keys.DOWN])  - int(ctx.keyboard[ctx.keys.UP])
        proj = self.player_ent.try_shoot(shoot_x, shoot_y)
        if proj:
            self.projectiles.append(proj)

        # Projectile update
        new_proj = []
        for p in self.projectiles:
            p.update(dt)
            if not p.alive:
                continue
            if self._rect_hits_wall(p.rect):
                continue
            hit = False
            for e in self.active_enemies:
                if e.alive and p.rect.colliderect(e.rect):
                    e.take_damage(p.dmg)
                    hit = True
                    break
            if hit:
                continue
            new_proj.append(p)
        self.projectiles = new_proj

        self._update_enemies(dt)

       
        rid = self.current_room_id
        if rid is not None and self.room_state[rid] == "locked":
            if not self.active_enemies:
                for key in self.room.rooms_meta[rid]["doors"]:
                    self._set_door_open(key, True)
                self.room_state[rid] = "cleared"
       
        if getattr(self, "_loop_music", False):
            try:
                if not music.is_playing():
                    self.music_index = (self.music_index + 1) % len(self.music_tracks)
                    music.play(os.path.join("playtime", self.music_tracks[self.music_index]))
            except Exception:
                pass

    def _solid_at(self, gx: int, gy: int) -> bool:
        if gy < 0 or gy >= len(self.room.grid): return True
        row = self.room.grid[gy]
        if gx < 0 or gx >= len(row): return True
        tid = row[gx]
        return tiles.is_solid(tid) or tiles.Tile(tid) == tiles.Tile.VOID  
    
    def _spawn_enemies_for_room(self, rid):
        import random
        inner = self.room.rooms_meta[rid]["rect_inner_g"]  
        n = random.randint(3, 4)

        for _ in range(n):
            gx = random.randint(inner.left, inner.right - 1)
            gy = random.randint(inner.top,  inner.bottom - 1)
            px = gx * tiles.TILE + tiles.TILE//4
            py = gy * tiles.TILE + tiles.TILE//4
            self.active_enemies.append(Enemy(px, py, w=tiles.TILE//2, h=tiles.TILE//2, max_hp=4))

    def _update_enemies(self, dt):
        for e in self.active_enemies:
            e.update(dt, self.room, self.player)
        self.active_enemies = [e for e in self.active_enemies if e.alive]

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

            br = self._rect_hits_blocker(r)
            if br:
                if dx > 0:  r.right = min(r.right, br.left)
                else:       r.left  = max(r.left,  br.right)

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
            br = self._rect_hits_blocker(r)
            if br:
                if dy > 0:  r.bottom = min(r.bottom, br.top)
                else:       r.top    = max(r.top,    br.bottom)

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
                if tiles.is_solid(tid) or tiles.Tile(tid) == tiles.Tile.VOID: 
                    return True
                for br in self.door_blockers.values():
                    if br and rect.colliderect(br):
                        return True
        return False

    def _clamp_to_floor(self):
        w = len(self.room.grid[0]) * tiles.TILE
        h = len(self.room.grid)    * tiles.TILE
        if self.player.left < 0: self.player.left = 0
        if self.player.top < 0: self.player.top = 0
        if self.player.right > w: self.player.right = w
        if self.player.bottom > h: self.player.bottom = h

    def _make_blocker(self, key):
        info = self.room.door_meta.get(key)
        if not info:
            return None
        r = info["rect_px"].copy()
        if info["orient"] == "H":
            r.inflate_ip(-2, 0)   
        else:
            r.inflate_ip(0, -2)  
        return r

    def _set_door_open(self, key, open_flag: bool):
        self.door_state[key] = bool(open_flag)
        self.door_blockers[key] = None if open_flag else self._make_blocker(key)

    def _room_id_at(self, gx, gy):
        for m in self.room.rooms_meta:
            if m["rect_inner_g"].collidepoint(gx, gy):
                return m["id"]
        return None

    def _rect_hits_blocker(self, rect):
        for br in self.door_blockers.values():
            if br and rect.colliderect(br):
                return br
        return None
    
    def draw(self, ctx):
        ctx.screen.clear()
        sw, sh = ctx.screen.width, ctx.screen.height
        world_w = len(self.room.grid[0]) * tiles.TILE
        world_h = len(self.room.grid)    * tiles.TILE

        cam_x = max(0, min(self.player.centerx - sw // 2, world_w - sw))
        cam_y = max(0, min(self.player.centery - sh // 2, world_h - sh))

        self.room.draw(ctx, cam_offset=(-cam_x, -cam_y))
        

        for e in self.active_enemies:
            e.draw(ctx, cam_x, cam_y)
        
        for p in self.projectiles:
            ctx.screen.draw.filled_rect(p.rect.move(-cam_x, -cam_y), (220, 220, 60))

        self.player_ent.draw(ctx, cam_x, cam_y)

        btn_img = self.btn_unmute_img if self.music_muted else self.btn_mute_img
        btn_x = ctx.screen.width - self.btn_size - self.btn_margin
        btn_y = self.btn_margin
        ctx.screen.blit(btn_img, (btn_x, btn_y))

        # debug hitbox:
        #ctx.screen.draw.filled_rect(self.player.move(-cam_x, -cam_y), (230, 230, 240))

        # DEBUG HUD 
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

    def on_mouse_down(self, pos, button, ctx):
        bx, by = pos
        btn_x = ctx.screen.width - self.btn_size - self.btn_margin
        btn_y = self.btn_margin

        if btn_x <= bx <= btn_x + self.btn_size and btn_y <= by <= btn_y + self.btn_size:
            self.music_muted = not self.music_muted
            if self.music_muted:
                music.set_volume(0.0)
            else:
                music.set_volume(0.25)