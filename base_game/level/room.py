# base_game/level/room.py
import os
from pygame import Rect
from . import tiles

MAP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "levels")

class Room:
    def __init__(self, grid, doors, spawn_xy):
        self.grid = grid
        self.doors = doors
        self.spawn_xy = spawn_xy

    def _is_wall(self, gx, gy):
        if gy < 0 or gy >= len(self.grid): return False
        if gx < 0 or gx >= len(self.grid[gy]): return False
        return self.grid[gy][gx] == int(tiles.Tile.WALL)

    @classmethod
    def from_ascii(cls, name: str, debug: bool = False):
        map_path = os.path.join(MAP_DIR, name + ".txt")
        if not os.path.exists(map_path):
            tried = [
                map_path,
                os.path.join(os.getcwd(), name + ".txt"),
                os.path.join(os.getcwd(), "maps", name + ".txt"),
            ]
            raise FileNotFoundError(
                "Nu am găsit harta '{}'. Am încercat:\n - {}".format(
                    name, "\n - ".join(tried)
                )
            )

        with open(map_path, "r", encoding="utf-8") as f:
            lines = [ln.rstrip("\n") for ln in f]

        grid = []
        spawn_xy = (0, 0)
        doors = {}

        for y, line in enumerate(lines):
            row = []
            for x, ch in enumerate(line):
                tid = int(tiles.CHARSET.get(ch, tiles.Tile.FLOOR))
                row.append(tid)

                if ch == "P":
                    spawn_xy = (x * tiles.TILE, y * tiles.TILE)

                if ch in ("U", "D", "L", "R"):
                    doors[(ch, x, y)] = Rect(
                        x * tiles.TILE, y * tiles.TILE, tiles.TILE, tiles.TILE
                    )
            grid.append(row)

        self = cls(grid, doors, spawn_xy)

        if debug:
            h = len(grid)
            w = len(grid[0]) if grid else 0
            print("[ASCII] folosesc harta:", map_path)
            print("[ASCII] dimensiuni: {}×{} tiles (TILE={})".format(w, h, tiles.TILE))
            for sx, sy in [(0,0), (1,0), (0,1), (5,5)]:
                if sy < h and sx < len(grid[sy]):
                    tid = grid[sy][sx]
                    try:
                        tname = tiles.Tile(tid).name
                    except Exception:
                        tname = "id={}".format(tid)
                    spr = tiles.PROPS.get(tiles.Tile(tid), {}).get("sprite")
                    print("[MAP] ({},{}) -> id={} {}, sprite='{}'".format(
                        sx, sy, tid, tname, spr
                    ))
            print("[SPAWN] {}  [DOORS] {}".format(spawn_xy, len(doors)))

        return self

    def draw(self, ctx, cam_offset=(0, 0)):
        ox, oy = cam_offset
        ts = tiles.TILE
        sw, sh = ctx.screen.width, ctx.screen.height
        max_x = len(self.grid[0]) - 1
        max_y = len(self.grid) - 1

        gx0 = max(0, (-ox) // ts)
        gy0 = max(0, (-oy) // ts)
        gx1 = min(max_x, (sw - 1 - ox) // ts)
        gy1 = min(max_y, (sh - 1 - oy) // ts)

        extra = tiles.get_extra_wall_top(ctx)         
        extra_rows = (extra + ts - 1) // ts            
        gy0_tall   = max(0, gy0 - extra_rows)

        if not hasattr(self, "_dbg_once"):
            self._dbg_once = True
            print("[TOP EXTRA measured from sprite] =", extra)

        top_gy0 = max(0, int(( -oy - ts) // ts) - 1)               
        top_gy1 = min(max_y, int(( sh - oy + extra) // ts) + 1)     

        side_px = 12
        top_gx0 = max(0, int(( -ox - side_px) // ts))
        top_gx1 = min(max_x, int(((sw - 1 - ox + side_px) // ts)))

        view_top    = 0
        view_bottom = sh

        H = len(self.grid)
        W = len(self.grid[0])

        for gy in range(gy0, gy1 + 1):
            row = self.grid[gy]
            for gx in range(gx0, gx1 + 1):
                tid = row[gx]
                if tiles.Tile(tid) in (tiles.Tile.VOID, tiles.Tile.WALL):
                    continue
                sx = gx * ts + ox
                sy = gy * ts + oy
                tiles.draw_tile(ctx, tid, sx, sy)


        for gy in range(gy0, gy1 + 1):
            for gx in range(gx0, gx1 + 1):
                tid = self.grid[gy][gx]
                if tiles.Tile(tid) != tiles.Tile.WALL:
                    continue

                north = self.grid[gy - 1][gx] if gy > 0 else int(tiles.Tile.VOID)
                south = self.grid[gy + 1][gx] if gy + 1 < H else int(tiles.Tile.VOID)

                is_inside = lambda t: t in (int(tiles.Tile.FLOOR), int(tiles.Tile.DOOR))

                if south == int(tiles.Tile.VOID) and is_inside(north):
                    sx = gx * ts + ox
                    sy = gy * ts + oy
                    tiles.draw_wall_bottom(ctx, sx, sy)

        def _is_south_edge(px, py):
            if px < 0 or py < 0 or py >= H or px >= W:
                return False
            if self.grid[py][px] != int(tiles.Tile.WALL):
                return False
            north = self.grid[py - 1][px] if py > 0 else int(tiles.Tile.VOID)
            south = self.grid[py + 1][px] if py + 1 < H else int(tiles.Tile.VOID)
            is_inside = (north == int(tiles.Tile.FLOOR)) or (north == int(tiles.Tile.DOOR))
            return (south == int(tiles.Tile.VOID)) and is_inside

        for gy in range(gy0, gy1 + 1):
            for gx in range(gx0, gx1 + 1):
                if self.grid[gy][gx] != int(tiles.Tile.WALL):
                    continue
                if not _is_south_edge(gx, gy):
                    continue

                sx = gx * ts + ox
                sy = gy * ts + oy

                if not _is_south_edge(gx - 1, gy):
                    tiles.draw_wall_bottom_end(ctx, sx, sy, "L")
                if not _is_south_edge(gx + 1, gy):
                    tiles.draw_wall_bottom_end(ctx, sx, sy, "R")

        for gy in range(gy0, gy1 + 1):
            for gx in range(gx0, gx1 + 1):
                tid = self.grid[gy][gx]
                if tiles.Tile(tid) != tiles.Tile.WALL:
                    continue

                left_tid  = self.grid[gy][gx-1] if gx > 0 else int(tiles.Tile.VOID)
                right_tid = self.grid[gy][gx+1] if gx + 1 < W else int(tiles.Tile.VOID)

                is_void   = lambda t: t == int(tiles.Tile.VOID)
                is_inside = lambda t: t in (int(tiles.Tile.FLOOR), int(tiles.Tile.DOOR))

                sx = gx * ts + ox
                sy = gy * ts + oy

                if is_void(left_tid) and is_inside(right_tid):
                    tiles.draw_wall_side_12x32(ctx, sx, sy, "L")

                if is_void(right_tid) and is_inside(left_tid):
                    tiles.draw_wall_side_12x32(ctx, sx, sy, "R")

        for gy in range(top_gy0, top_gy1 + 1):
            for gx in range(top_gx0, top_gx1 + 1):
                tid = self.grid[gy][gx]
                if tiles.Tile(tid) != tiles.Tile.WALL:
                    continue

                north_is_wall = (gy > 0 and self.grid[gy - 1][gx] == int(tiles.Tile.WALL))
                south = self.grid[gy + 1][gx] if gy + 1 < H else int(tiles.Tile.VOID)
                south_is_interior = (south == int(tiles.Tile.FLOOR)) or (south == int(tiles.Tile.DOOR))
                if north_is_wall or not south_is_interior:
                    continue

                sx = gx * ts + ox
                sy = gy * ts + oy

                spr_top    = sy - extra
                spr_bottom = sy + ts
                if spr_bottom <= 0 or spr_top >= sh:
                    continue

                tiles.draw_wall_top_32x76(ctx, sx, sy)

                def _is_north_cap_at(px, py):
                    if px < 0 or py < 0 or py >= H or px >= W: return False
                    if self.grid[py][px] != int(tiles.Tile.WALL): return False
                    n_wall = (py > 0 and self.grid[py - 1][px] == int(tiles.Tile.WALL))
                    s = self.grid[py + 1][px] if py + 1 < H else int(tiles.Tile.VOID)
                    s_in = (s == int(tiles.Tile.FLOOR)) or (s == int(tiles.Tile.DOOR))
                    return (not n_wall) and s_in

                if not _is_north_cap_at(gx - 1, gy):
                    tiles.draw_wall_top_end(ctx, sx, sy, "L")
                if not _is_north_cap_at(gx + 1, gy):
                    tiles.draw_wall_top_end(ctx, sx, sy, "R")