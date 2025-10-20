# base_game/level/room.py
import os
from pygame import Rect
from . import tiles

class Room:
    def __init__(self, grid, doors, spawn_xy):
        self.grid = grid
        self.doors = doors
        self.spawn_xy = spawn_xy

    @classmethod
    def from_ascii(cls, name: str):
        here = os.path.dirname(__file__)
        path = os.path.normpath(os.path.join(here, "..", "data", "levels", f"{name}.txt"))
        with open(path, "r", encoding="utf-8") as f:
            rows = [line.rstrip("\n") for line in f]

        grid = []
        spawn = (tiles.TILE, tiles.TILE)
        marks = {"U": [], "D": [], "L": [], "R": []}

        for gy, line in enumerate(rows):
            row = []
            for gx, ch in enumerate(line):
                tid = int(tiles.CHARSET.get(ch, tiles.Tile.FLOOR))
                if ch == "P":
                    spawn = (gx * tiles.TILE, gy * tiles.TILE)
                    tid = int(tiles.Tile.FLOOR)
                if ch in marks:
                    marks[ch].append((gx, gy))
                row.append(tid)
            grid.append(row)

        doors = {}
        for tag, coords in marks.items():
            if not coords: continue
            xs = [gx for gx, _ in coords]; ys = [gy for _, gy in coords]
            x0, x1 = min(xs), max(xs); y0, y1 = min(ys), max(ys)
            doors[tag] = Rect(x0 * tiles.TILE, y0 * tiles.TILE,
                              (x1 - x0 + 1) * tiles.TILE, (y1 - y0 + 1) * tiles.TILE)

        return cls(grid, doors, spawn)

    def draw(self, ctx):
        ts = tiles.TILE
        for gy, row in enumerate(self.grid):
            for gx, tid in enumerate(row):
                x, y = gx * ts, gy * ts
                props = tiles.PROPS.get(tiles.Tile(tid), {})
                name = props.get("sprite")
                if name:
                    ctx.screen.blit(name, (x, y))  # folosește direct PNG-ul 32x32
                else:
                    ctx.screen.draw.filled_rect(Rect(x, y, ts, ts), tiles.color_of(tid))
