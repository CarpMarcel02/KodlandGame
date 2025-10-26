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
        if gy < 0 or gy >= len(self.grid):
            return False
        if gx < 0 or gx >= len(self.grid[gy]):
            return False
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
                "Did not found map '{}'. tryed:\n - {}".format(name, "\n - ".join(tried))
            )

        with open(map_path, encoding="utf-8") as f:
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
                    doors[(ch, x, y)] = Rect(x * tiles.TILE, y * tiles.TILE, tiles.TILE, tiles.TILE)
            grid.append(row)

        self = cls(grid, doors, spawn_xy)

        return self

    def draw(self, ctx, cam_offset=(0, 0)):
        ox, oy = cam_offset
        ts = tiles.TILE
        sw, sh = ctx.screen.width, ctx.screen.height

        height = len(self.grid)
        width = len(self.grid[0]) if height else 0
        if height == 0 or width == 0:
            return

        max_x = width - 1
        max_y = height - 1

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

                up = self.grid[gy - 1][gx] if gy > 0 else int(tiles.Tile.VOID)
                down = self.grid[gy + 1][gx] if gy + 1 < height else int(tiles.Tile.VOID)
                left = self.grid[gy][gx - 1] if gx > 0 else int(tiles.Tile.VOID)
                right = self.grid[gy][gx + 1] if gx + 1 < width else int(tiles.Tile.VOID)

                sx = gx * tiles.TILE + ox
                sy = gy * tiles.TILE + oy

                if left == int(tiles.Tile.VOID):
                    tiles.draw_hall_border(ctx, sx, sy, "L")
                if right == int(tiles.Tile.VOID):
                    tiles.draw_hall_border(ctx, sx, sy, "R")
                if up == int(tiles.Tile.VOID):
                    tiles.draw_hall_border(ctx, sx, sy, "U")
                if down == int(tiles.Tile.VOID):
                    tiles.draw_hall_border(ctx, sx, sy, "D")

        def at(x, y, default):
            if y < 0 or y >= height or x < 0 or x >= width:
                return default
            return self.grid[y][x]

        void_id = int(tiles.Tile.VOID)
        floor_id = int(tiles.Tile.FLOOR)
        door_id = int(tiles.Tile.DOOR)

        for gy in range(wy0, wy1 + 1):
            for gx in range(wx0, wx1 + 1):
                if tiles.Tile(self.grid[gy][gx]) != tiles.Tile.WALL:
                    continue

                north = at(gx, gy - 1, void_id)
                south = at(gx, gy + 1, void_id)
                left_v = at(gx - 1, gy, void_id)
                right_v = at(gx + 1, gy, void_id)

                sx = gx * ts + ox
                sy = gy * ts + oy

                if north != int(tiles.Tile.WALL) and south in (floor_id, door_id):
                    tiles.draw_wall_top_32x76(ctx, sx, sy)

                if south == void_id and north in (floor_id, door_id):
                    tiles.draw_wall_bottom(ctx, sx, sy)

                if left_v == void_id and right_v in (floor_id, door_id):
                    tiles.draw_wall_side_12x32(ctx, sx, sy, "L")

                if right_v == void_id and left_v in (floor_id, door_id):
                    tiles.draw_wall_side_12x32(ctx, sx, sy, "R")

                if north == void_id and left_v == void_id:
                    tiles.draw_corner_top_left(ctx, sx, sy)
                if north == void_id and right_v == void_id:
                    tiles.draw_corner_top_right(ctx, sx, sy)
                if south == void_id and left_v == void_id:
                    tiles.draw_corner_bottom_left(ctx, sx, sy)
                if south == void_id and right_v == void_id:
                    tiles.draw_corner_bottom_right(ctx, sx, sy)

        hall_id = int(tiles.Tile.HALL)
        outside_ids = (void_id, hall_id)

        door_state = getattr(self, "door_state", None)

        for key, r in self.doors.items():
            orient, _kx, _ky = key

            dx = r.x // tiles.TILE
            dy = r.y // tiles.TILE

            def at2(x, y, default):
                if y < 0 or y >= height or x < 0 or x >= width:
                    return default
                return self.grid[y][x]

            if orient == "H":
                if at2(dx, dy - 1, void_id) in outside_ids:
                    facing = "UP"
                elif at2(dx, dy + 1, void_id) in outside_ids:
                    facing = "DOWN"
                else:
                    facing = "UP"
            else:
                if at2(dx - 1, dy, void_id) in outside_ids:
                    facing = "LEFT"
                elif at2(dx + 1, dy, void_id) in outside_ids:
                    facing = "RIGHT"
                else:
                    facing = "LEFT"

            bx, by, bw, bh = tiles.door_bbox_px(facing, r.x, r.y)
            sx0 = bx + ox
            sy0 = by + oy
            sx1 = sx0 + bw
            sy1 = sy0 + bh

            margin_left = 12
            margin_right = 12
            margin_top = 12
            margin_bottom = 12

            if facing == "LEFT":
                margin_right = 48

            if (
                (sx1 < -margin_left)
                or (sx0 > sw + margin_right)
                or (sy1 < -margin_top)
                or (sy0 > sh + margin_bottom)
            ):
                continue

            is_open = True if door_state is None else door_state.get(key, True)
            if is_open:
                tiles.draw_open_door(ctx, facing, r.x + ox, r.y + oy)
            else:
                tiles.draw_closed_door(ctx, facing, r.x + ox, r.y + oy)
