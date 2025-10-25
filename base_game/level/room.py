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
                "Did not found map '{}'. tryed:\n - {}".format(
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
            print("Using map:", map_path)
            print("Dimensions: {}×{} tiles (TILE={})".format(w, h, tiles.TILE))
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

        H = len(self.grid)
        W = len(self.grid[0]) if H else 0
        if H == 0 or W == 0:
            return

        max_x = W - 1
        max_y = H - 1

        gx0 = max(0, (-ox) // ts)
        gy0 = max(0, (-oy) // ts)
        gx1 = min(max_x, (sw - 1 - ox) // ts)
        gy1 = min(max_y, (sh - 1 - oy) // ts)

        vpad = tiles.get_extra_wall_top(ctx) or 0  
        hpad = 48                                  

        wx0 = max(0, int((-ox - hpad) // ts))
        wy0 = max(0, int((-oy - vpad) // ts))
        wx1 = min(max_x, int((sw - 1 - ox + hpad) // ts))
        wy1 = min(max_y, int((sh - 1 - oy + vpad) // ts))

        # Floor
        for gy in range(gy0, gy1 + 1):
            row = self.grid[gy]
            for gx in range(gx0, gx1 + 1):
                tid = row[gx]
                if tiles.Tile(tid) in (tiles.Tile.VOID, tiles.Tile.WALL, tiles.Tile.DOOR):
                    continue
                tiles.draw_tile(ctx, tid, gx * ts + ox, gy * ts + oy)
        
        for gy in range(gy0, gy1 + 1):
            for gx in range(gx0, gx1 + 1):
                if tiles.Tile(self.grid[gy][gx]) != tiles.Tile.HALL:
                    continue

                # Neighbours
                up    = self.grid[gy-1][gx] if gy > 0 else int(tiles.Tile.VOID)
                down  = self.grid[gy+1][gx] if gy+1 < H else int(tiles.Tile.VOID)
                left  = self.grid[gy][gx-1] if gx > 0 else int(tiles.Tile.VOID)
                right = self.grid[gy][gx+1] if gx+1 < W else int(tiles.Tile.VOID)

                sx = gx * tiles.TILE + ox
                sy = gy * tiles.TILE + oy

                if left  == int(tiles.Tile.VOID): tiles.draw_hall_border(ctx, sx, sy, "L")
                if right == int(tiles.Tile.VOID): tiles.draw_hall_border(ctx, sx, sy, "R")
                if up    == int(tiles.Tile.VOID): tiles.draw_hall_border(ctx, sx, sy, "U")
                if down  == int(tiles.Tile.VOID): tiles.draw_hall_border(ctx, sx, sy, "D")

        def at(x, y, default):
            if y < 0 or y >= H or x < 0 or x >= W:
                return default
            return self.grid[y][x]

        # 2) Walls and corners
        for gy in range(wy0, wy1 + 1):
            for gx in range(wx0, wx1 + 1):
                if tiles.Tile(self.grid[gy][gx]) != tiles.Tile.WALL:
                    continue

                north = at(gx, gy - 1, int(tiles.Tile.VOID))
                south = at(gx, gy + 1, int(tiles.Tile.VOID))
                left  = at(gx - 1, gy, int(tiles.Tile.VOID))
                right = at(gx + 1, gy, int(tiles.Tile.VOID))

                sx = gx * ts + ox
                sy = gy * ts + oy

                if north != int(tiles.Tile.WALL) and south in (int(tiles.Tile.FLOOR), int(tiles.Tile.DOOR)):
                    tiles.draw_wall_top_32x76(ctx, sx, sy)

                if south == int(tiles.Tile.VOID) and north in (int(tiles.Tile.FLOOR), int(tiles.Tile.DOOR)):
                    tiles.draw_wall_bottom(ctx, sx, sy)

                if left == int(tiles.Tile.VOID) and right in (int(tiles.Tile.FLOOR), int(tiles.Tile.DOOR)):
                    tiles.draw_wall_side_12x32(ctx, sx, sy, "L")

                if right == int(tiles.Tile.VOID) and left in (int(tiles.Tile.FLOOR), int(tiles.Tile.DOOR)):
                    tiles.draw_wall_side_12x32(ctx, sx, sy, "R")

                VOID = int(tiles.Tile.VOID)
                if (north == VOID and left  == VOID): tiles.draw_corner_top_left(ctx, sx, sy)
                if (north == VOID and right == VOID): tiles.draw_corner_top_right(ctx, sx, sy)
                if (south == VOID and left  == VOID): tiles.draw_corner_bottom_left(ctx, sx, sy)
                if (south == VOID and right == VOID): tiles.draw_corner_bottom_right(ctx, sx, sy)
        
        VOID = int(tiles.Tile.VOID)
        FLOOR = int(tiles.Tile.FLOOR)
        DOOR  = int(tiles.Tile.DOOR)
        HALL  = int(tiles.Tile.HALL)
        OUTSIDE = (VOID, HALL)

        door_state = getattr(self, "door_state", None) 

        for key, r in self.doors.items():
            orient, _kx, _ky = key

            dx = r.x // tiles.TILE
            dy = r.y // tiles.TILE

            def at(x, y, default):
                if y < 0 or y >= len(self.grid) or x < 0 or x >= len(self.grid[0]):
                    return default
                return self.grid[y][x]

            if orient == "H":
                if at(dx, dy - 1, VOID) in OUTSIDE:
                    facing = "UP"
                elif at(dx, dy + 1, VOID) in OUTSIDE:
                    facing = "DOWN"
                else:
                    facing = "UP"
            else:  
                if at(dx - 1, dy, VOID) in OUTSIDE:
                    facing = "LEFT"
                elif at(dx + 1, dy, VOID) in OUTSIDE:
                    facing = "RIGHT"
                else:
                    facing = "LEFT"

            bx, by, bw, bh = tiles.door_bbox_px(facing, r.x, r.y)
            sx0 = bx + ox; sy0 = by + oy
            sx1 = sx0 + bw; sy1 = sy0 + bh

            MARGIN_LEFT   = 12
            MARGIN_RIGHT  = 12
            MARGIN_TOP    = 12
            MARGIN_BOTTOM = 12

            if facing == "LEFT":
                MARGIN_RIGHT = 48 

            if (sx1 < -MARGIN_LEFT) or (sx0 > sw + MARGIN_RIGHT) or (sy1 < -MARGIN_TOP) or (sy0 > sh + MARGIN_BOTTOM):
                continue

            is_open = True if door_state is None else door_state.get(key, True)
            if is_open:
                tiles.draw_open_door(ctx, facing, r.x + ox, r.y + oy)
            else:
                tiles.draw_closed_door(ctx, facing, r.x + ox, r.y + oy)