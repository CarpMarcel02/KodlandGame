import os
import random

from pgzero import music
from pgzero.loaders import images as pgz_images
from pygame import Rect

from ..entities.armadillo import ArmadilloEnemy
from ..entities.plant import PlantEnemy
from ..entities.player import Player
from ..entities.skeleton import SkeletonEnemy
from ..level import tiles
from ..level.procgen import generate_world
from ..ui.healthbar import HealthBar
from .base import BaseScene


class PlayScene(BaseScene):
    SPEED = 160.0
    BASE_VOLUME = 0.09
    DEATH_FADE_TIME = 0.6

    def on_enter(self, muted=False):
        self.room = generate_world(
            seed=None, target_rooms=6, first_size=(20, 15), min_size=15, max_size=30
        )

        self.room_state = [m["state"] for m in self.room.rooms_meta]
        self.current_room_id = None

        self.door_state = {}
        self.door_blockers = {}
        self.room.door_state = self.door_state
        self.room.rect_hits_blocker = self._rect_hits_blocker

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
        self.player_ent.set_sfx_muted(bool(muted))
        self.player = self.player_ent.rect

        self._half_player = size // 2
        self.room._half_player = self._half_player

        self.projectiles = []

        music_folder = os.path.join(os.path.dirname(__file__), "..", "music", "playtime")
        self.music_tracks = [
            f for f in os.listdir(music_folder) if f.lower().endswith((".ogg", ".mp3", ".wav"))
        ]
        self.music_index = random.randrange(len(self.music_tracks)) if self.music_tracks else 0
        self.music_muted = muted

        if self.music_tracks:
            try:
                music.play(os.path.join("playtime", self.music_tracks[self.music_index]))
                base_volume = 0.0 if self.music_muted else self.BASE_VOLUME
                music.set_volume(base_volume)
                self._loop_music = True
            except Exception as e:
                print("Music load failed:", e)

        self.btn_mute_img = pgz_images.load("ui/mute")
        self.btn_unmute_img = pgz_images.load("ui/unmute")
        self.btn_size = 36
        self.btn_margin = 35

        self.show_pause_button = True
        self.show_mute_button = True

        self.pending_pause = False

        self.btn_pause_img = pgz_images.load("ui/pause")
        self.btn_pause_size = 36
        self.btn_pause_margin = 10

        self.btn_offset_y = -4
        self.btn_offset_x = 0

        self.hitbox_offset_x = +15
        self.hitbox_offset_y = +15

        self.hitbox_expand_x = 8
        self.hitbox_expand_y = 8

        self.hud_hp = HealthBar()

        self.death_stage = None
        self.death_t = 0.0
        self._death_btns = {}
        self._game_over_fired = False

        self.enemy_projectiles = []

        self._you_win_fired = False

    def _room_center_px(self, rid):
        cx_g, cy_g = self.room.rooms_meta[rid]["center_g"]
        return cx_g * tiles.TILE + tiles.TILE // 2, cy_g * tiles.TILE + tiles.TILE // 2

    def _room_entry_depth_px(self, rid, px, py):
        rcx, rcy = self._room_center_px(rid)
        depths = []
        for key in self.room.rooms_meta[rid]["doors"]:
            info = self.room.door_meta[key]
            r = info["rect_px"]
            orient = info["orient"]
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
        vx = (-self.SPEED if ctx.keyboard[ctx.keys.A] else 0.0) + (
            self.SPEED if ctx.keyboard[ctx.keys.D] else 0.0
        )
        vy = (-self.SPEED if ctx.keyboard[ctx.keys.W] else 0.0) + (
            self.SPEED if ctx.keyboard[ctx.keys.S] else 0.0
        )

        dx = int(round(vx * dt))
        dy = int(round(vy * dt))

        self.player_ent.update(
            dt, (dx, dy), solid_at=self._solid_at, hits_blocker=self._rect_hits_blocker
        )

        self._clamp_to_floor()

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

        shoot_x = int(ctx.keyboard[ctx.keys.RIGHT]) - int(ctx.keyboard[ctx.keys.LEFT])
        shoot_y = int(ctx.keyboard[ctx.keys.DOWN]) - int(ctx.keyboard[ctx.keys.UP])
        proj = self.player_ent.try_shoot(shoot_x, shoot_y)
        if proj:
            self.projectiles.append(proj)

        new_proj = []
        for p in self.projectiles:
            p.update(dt)
            if not p.alive:
                continue
            if self._rect_hits_wall(p.rect):
                continue

            team = getattr(p, "team", "player")

            if team == "player":
                hit = False
                for e in self.active_enemies:
                    if e.alive and p.rect.colliderect(e.rect):
                        e.take_damage(p.dmg)
                        hit = True
                        break
                if hit:
                    continue
            else:
                if p.rect.colliderect(self.player):
                    if getattr(self.player_ent, "take_damage", None):
                        self.player_ent.take_damage(getattr(p, "dmg", 1))
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
                if (not self._you_win_fired) and (self.death_stage is None):
                    if all(state == "cleared" for state in self.room_state):
                        self._you_win_fired = True
                        self._manager.change("you_win", muted=self.music_muted)

        if getattr(self, "_loop_music", False):
            try:
                if not music.is_playing():
                    self.music_index = (self.music_index + 1) % len(self.music_tracks)
                    music.play(os.path.join("playtime", self.music_tracks[self.music_index]))
            except Exception:
                pass
        if self.pending_pause:
            self._manager.change("pause")
            self.pending_pause = False

        if self.death_stage is not None:
            self._update_death(dt)
            return

    def _solid_at(self, gx: int, gy: int) -> bool:
        if gy < 0 or gy >= len(self.room.grid):
            return True
        row = self.room.grid[gy]
        if gx < 0 or gx >= len(row):
            return True
        tid = row[gx]
        return tiles.is_solid(tid) or tiles.Tile(tid) == tiles.Tile.VOID

    def _spawn_enemies_for_room(self, rid):
        import random

        inner = self.room.rooms_meta[rid]["rect_inner_g"]
        ts = tiles.TILE

        placed_rects = []

        def _ok_pos(rect: Rect) -> bool:

            if self._rect_hits_wall(rect):
                return False

            pcx, pcy = self.player.centerx, self.player.centery
            ecx, ecy = rect.centerx, rect.centery
            if (pcx - ecx) ** 2 + (pcy - ecy) ** 2 < (3 * ts) ** 2:
                return False

            for r in placed_rects:
                if rect.colliderect(r):
                    return False
            return True

        def _try_place(w: int, h: int):
            for _ in range(64):
                gx = random.randint(inner.left, inner.right - 1)
                gy = random.randint(inner.top, inner.bottom - 1)
                px = gx * ts + (ts - w) // 2
                py = gy * ts + (ts - h) // 2
                probe = Rect(px, py, w, h)
                if _ok_pos(probe):
                    placed_rects.append(probe)
                    return px, py
            return None

        n_skel = random.randint(2, 4)
        for _ in range(n_skel):
            pos = _try_place(24, 24)
            if pos:
                self.active_enemies.append(SkeletonEnemy(*pos))

        n_arm = random.randint(2, 3)
        for _ in range(n_arm):
            pos = _try_place(22, 22)
            if pos:
                self.active_enemies.append(ArmadilloEnemy(*pos))
        max_plants = 4

        def _plant_wall_slots():
            slots = []

            gy = inner.top
            for gx in range(inner.left, inner.right):
                if not self._solid_at(gx, gy) and self._solid_at(gx, gy - 1):
                    px = gx * ts + (ts - 24) // 2
                    py = gy * ts + (ts - 24) // 2
                    slots.append((px, py, "down"))

            gy = inner.bottom - 1
            for gx in range(inner.left, inner.right):
                if not self._solid_at(gx, gy) and self._solid_at(gx, gy + 1):
                    px = gx * ts + (ts - 24) // 2
                    py = gy * ts + (ts - 24) // 2
                    slots.append((px, py, "up"))

            gx = inner.left
            for gy in range(inner.top, inner.bottom):
                if not self._solid_at(gx, gy) and self._solid_at(gx - 1, gy):
                    px = gx * ts + (ts - 24) // 2
                    py = gy * ts + (ts - 24) // 2
                    slots.append((px, py, "right"))

            gx = inner.right - 1
            for gy in range(inner.top, inner.bottom):
                if not self._solid_at(gx, gy) and self._solid_at(gx + 1, gy):
                    px = gx * ts + (ts - 24) // 2
                    py = gy * ts + (ts - 24) // 2
                    slots.append((px, py, "left"))

            return slots

        plant_slots = _plant_wall_slots()
        random.shuffle(plant_slots)

        placed_plants = 0
        for px, py, facing in plant_slots:
            if placed_plants >= max_plants:
                break
            probe = Rect(px, py, 24, 24)
            if not _ok_pos(probe):
                continue
            self.active_enemies.append(PlantEnemy(px, py, facing=facing))
            placed_rects.append(probe)
            placed_plants += 1
        self.room._enemy_rects = [e.rect for e in self.active_enemies]

    def _update_enemies(self, dt):
        self.room._enemy_rects = [e.rect for e in self.active_enemies]

        new_list = []
        for e in self.active_enemies:
            evt = e.update(dt, self.room, self.player)
            if evt:
                if evt[0] == "HIT_PLAYER":
                    dmg = int(evt[1])
                    if getattr(self.player_ent, "take_damage", None):
                        self.player_ent.take_damage(dmg)
                    if self.player_ent.hp <= 0:
                        self._trigger_game_over()
                        return
                elif evt[0] == "SPAWN_ENEMY_PROJECTILE":
                    self.projectiles.append(evt[1])

            if e.alive:
                new_list.append(e)

        self.active_enemies = new_list
        self.room._enemy_rects = [e.rect for e in self.active_enemies]

        for _ in range(2):

            for e in self.active_enemies:
                dx, dy, col = self._mtv_rect_rect(e.rect, self.player)
                if col:
                    if getattr(e, "pushable", True):
                        self._nudge_enemy_safe(e, dx, dy)

            es = self.active_enemies
            n = len(es)
            for i in range(n):
                a = es[i]
                for j in range(i + 1, n):
                    b = es[j]
                    dx, dy, col = self._mtv_rect_rect(a.rect, b.rect)
                    if not col:
                        continue

                    pa = getattr(a, "pushable", True)
                    pb = getattr(b, "pushable", True)

                    if pa and pb:
                        half_dx = self._round_px(dx * 0.5)
                        half_dy = self._round_px(dy * 0.5)
                        moved_a = False
                        if (half_dx or half_dy) and self._can_move_enemy(a, half_dx, half_dy):
                            a.rect.x += half_dx
                            a.rect.y += half_dy
                            moved_a = True
                        else:
                            if half_dx and self._can_move_enemy(a, half_dx, 0):
                                a.rect.x += half_dx
                                moved_a = True
                            elif half_dy and self._can_move_enemy(a, 0, half_dy):
                                a.rect.y += half_dy
                                moved_a = True

                        moved_b = False
                        if (half_dx or half_dy) and self._can_move_enemy(b, -half_dx, -half_dy):
                            b.rect.x -= half_dx
                            b.rect.y -= half_dy
                            moved_b = True
                        else:
                            if half_dx and self._can_move_enemy(b, -half_dx, 0):
                                b.rect.x -= half_dx
                                moved_b = True
                            elif half_dy and self._can_move_enemy(b, 0, -half_dy):
                                b.rect.y -= half_dy
                                moved_b = True

                        if not (moved_a or moved_b):
                            full_dx = self._round_px(dx)
                            full_dy = self._round_px(dy)
                            if self._can_move_enemy(a, full_dx, full_dy):
                                a.rect.x += full_dx
                                a.rect.y += full_dy

                    elif pa and not pb:
                        full_dx = self._round_px(dx)
                        full_dy = self._round_px(dy)
                        if self._can_move_enemy(a, full_dx, full_dy):
                            a.rect.x += full_dx
                            a.rect.y += full_dy

                    elif not pa and pb:
                        full_dx = self._round_px(dx)
                        full_dy = self._round_px(dy)
                        if self._can_move_enemy(b, -full_dx, -full_dy):
                            b.rect.x -= full_dx
                            b.rect.y -= full_dy

                    else:
                        pass

        self.room._enemy_rects = [e.rect for e in self.active_enemies]

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
                if dy > 0:
                    r.bottom = min(r.bottom, br.top)
                else:
                    r.top = max(r.top, br.bottom)

    def _rect_hits_wall(self, rect: Rect) -> bool:
        ts = tiles.TILE
        gy0, gy1 = rect.top // ts, rect.bottom // ts
        gx0, gx1 = rect.left // ts, rect.right // ts
        for gy in range(gy0, gy1 + 1):
            if gy < 0 or gy >= len(self.room.grid):
                return True
            row = self.room.grid[gy]
            for gx in range(gx0, gx1 + 1):
                if gx < 0 or gx >= len(row):
                    return True
                tid = row[gx]
                if tiles.is_solid(tid) or tiles.Tile(tid) == tiles.Tile.VOID:
                    return True
                for br in self.door_blockers.values():
                    if br and rect.colliderect(br):
                        return True
        return False

    def _clamp_to_floor(self):
        w = len(self.room.grid[0]) * tiles.TILE
        h = len(self.room.grid) * tiles.TILE
        if self.player.left < 0:
            self.player.left = 0
        if self.player.top < 0:
            self.player.top = 0
        if self.player.right > w:
            self.player.right = w
        if self.player.bottom > h:
            self.player.bottom = h

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

    def on_resume(self):
        try:
            if not self.music_muted:
                new_vol = min(1.0, music.get_volume() * 2.0)
                music.set_volume(new_vol)
        except Exception:
            pass

        self.show_pause_button = True
        self.show_mute_button = True

    def draw(self, ctx):
        ctx.screen.clear()
        sw, sh = ctx.screen.width, ctx.screen.height
        world_w = len(self.room.grid[0]) * tiles.TILE
        world_h = len(self.room.grid) * tiles.TILE

        cam_x = max(0, min(self.player.centerx - sw // 2, world_w - sw))
        cam_y = max(0, min(self.player.centery - sh // 2, world_h - sh))

        self.room.draw(ctx, cam_offset=(-cam_x, -cam_y))

        actors = [*self.active_enemies, self.player_ent]
        actors.sort(key=lambda obj: obj.rect.bottom)

        for obj in actors:
            obj.draw(ctx, cam_x, cam_y)

        btn_x = ctx.screen.width - self.btn_size - self.btn_margin + self.btn_offset_x
        btn_y = self.btn_margin + self.btn_offset_y

        if self.show_mute_button:
            btn_img = self.btn_unmute_img if self.music_muted else self.btn_mute_img
            ctx.screen.blit(btn_img, (btn_x, btn_y))

        if self.show_pause_button:
            pause_x = btn_x - self.btn_pause_size - 25 + self.btn_offset_x
            pause_y = btn_y
            ctx.screen.blit(self.btn_pause_img, (pause_x, pause_y))

        self.hud_hp.draw(ctx, self.player_ent.hp, self.player_ent.max_hp)

        if self.death_stage in ("fade", "menu"):
            self._draw_death_overlay(ctx)

        for p in self.projectiles:
            if getattr(p, "sprite", None):
                img = pgz_images.load(p.sprite)
                ctx.screen.blit(img, (p.rect.x - cam_x, p.rect.y - cam_y))
            else:
                ctx.screen.draw.filled_rect(p.rect.move(-cam_x, -cam_y), (220, 220, 60))

    def on_mouse_down(self, pos, button, ctx):
        if button != 1:
            return
        bx, by = pos
        if self.death_stage == "menu":
            if self._click_death_menu(pos, ctx):
                return

        btn_x = ctx.screen.width - self.btn_size - self.btn_margin + self.btn_offset_x
        btn_y = self.btn_margin + self.btn_offset_y

        mute_hit = (
            btn_x + self.hitbox_offset_x - self.hitbox_expand_x
            <= bx
            <= btn_x + self.btn_size + self.hitbox_offset_x + self.hitbox_expand_x
            and btn_y + self.hitbox_offset_y - self.hitbox_expand_y
            <= by
            <= btn_y + self.btn_size + self.hitbox_offset_y + self.hitbox_expand_y
        )

        if mute_hit:
            self.show_mute_button = False
            ctx.screen.clear()
            self.draw(ctx)

            self.music_muted = not self.music_muted
            if self.music_muted:
                music.set_volume(0.0)
            else:
                music.set_volume(self.BASE_VOLUME)
            if getattr(self, "player_ent", None):
                self.player_ent.set_sfx_muted(self.music_muted)
            self.show_mute_button = True
            ctx.screen.clear()
            self.draw(ctx)
            return

        pause_x = btn_x - self.btn_pause_size - 25 + self.btn_offset_x
        pause_y = btn_y

        pause_hit = (
            pause_x + self.hitbox_offset_x - self.hitbox_expand_x
            <= bx
            <= pause_x + self.btn_pause_size + self.hitbox_offset_x + self.hitbox_expand_x
            and pause_y + self.hitbox_offset_y - self.hitbox_expand_y
            <= by
            <= pause_y + self.btn_pause_size + self.hitbox_offset_y + self.hitbox_expand_y
        )

        if pause_hit:
            self.show_pause_button = False

            ctx.screen.clear()
            self.draw(ctx)

            self._manager.change("pause", ctx)
            return

    def _sign(self, v: float) -> int:
        return 1 if v > 0 else (-1 if v < 0 else 0)

    def _mtv_rect_rect(self, a: Rect, b: Rect):
        dx = a.centerx - b.centerx
        px = (a.w + b.w) * 0.5 - abs(dx)
        if px <= 0:
            return 0, 0, False

        dy = a.centery - b.centery
        py = (a.h + b.h) * 0.5 - abs(dy)
        if py <= 0:
            return 0, 0, False

        if px < py:
            return self._sign(dx) * px, 0, True
        else:
            return 0, self._sign(dy) * py, True

    def _round_px(self, v: float) -> int:
        iv = int(round(v))
        if iv == 0 and abs(v) > 0.0:
            return 1 if v > 0 else -1
        return iv

    def _can_move_enemy(self, e, dx, dy):
        test = e.rect.move(dx, dy)
        return not self._rect_hits_wall(test)

    def _nudge_enemy_safe(self, e, dx: float, dy: float):
        dx = self._round_px(dx)
        dy = self._round_px(dy)
        if dx == 0 and dy == 0:
            return

        if self._can_move_enemy(e, dx, dy):
            e.rect.x += dx
            e.rect.y += dy
            return

        if abs(dx) >= abs(dy):
            if dx and self._can_move_enemy(e, dx, 0):
                e.rect.x += dx
                return
            if dy and self._can_move_enemy(e, 0, dy):
                e.rect.y += dy
                return
        else:
            if dy and self._can_move_enemy(e, 0, dy):
                e.rect.y += dy
                return
            if dx and self._can_move_enemy(e, dx, 0):
                e.rect.x += dx
                return

    def _draw_hud(self, ctx):
        bar_w, bar_h = 160, 12
        x, y = 10, ctx.screen.height - bar_h - 10

        ctx.screen.draw.rect(Rect(x - 1, y - 1, bar_w + 2, bar_h + 2), (15, 15, 15))
        ctx.screen.draw.filled_rect(Rect(x, y, bar_w, bar_h), (40, 40, 40))

        p = 0.0
        if self.player_ent.max_hp > 0:
            p = max(0.0, min(1.0, self.player_ent.hp / self.player_ent.max_hp))

        fill_w = max(0, int((bar_w - 2) * p))
        ctx.screen.draw.filled_rect(Rect(x + 1, y + 1, fill_w, bar_h - 2), (60, 200, 80))

    def _trigger_game_over(self):
        if self._game_over_fired:
            return
        self._game_over_fired = True
        try:
            self._manager.change("game_over", muted=self.music_muted)
        except TypeError:
            self._manager.change("game_over")
