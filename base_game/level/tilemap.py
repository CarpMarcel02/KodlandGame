# base_game/level/tilemap.py
import os
from pygame import Rect
from . import tiles

class Tilemap:
    def __init__(self, grid: list[list[int]], spawn_xy: tuple[int, int]):
        self.grid = grid                  # matrice [rows][cols] de tile_id (int)
        self.spawn_xy = spawn_xy          # coordonate pixel pt. spawn (stânga-sus)
        self.tile_size = tiles.TILE
        self._solids = None               # cache de Rect-uri solide

    @property
    def solids(self) -> list[Rect]:
        # construim o singură dată dreptunghiurile solide
        if self._solids is None:
            ts = self.tile_size
            out: list[Rect] = []
            for gy, row in enumerate(self.grid):
                for gx, tid in enumerate(row):
                    if tiles.is_solid(tid):
                        out.append(Rect(gx * ts, gy * ts, ts, ts))
            self._solids = out
        return self._solids

    @classmethod
    def from_ascii(cls, name: str):
        """încarcă data/levels/<name>.txt folosind tiles.CHARSET"""
        here = os.path.dirname(__file__)
        path = os.path.normpath(os.path.join(here, "..", "data", "levels", f"{name}.txt"))
        with open(path, "r", encoding="utf-8") as f:
            rows = [line.rstrip("\n") for line in f]

        grid: list[list[int]] = []
        spawn = (tiles.TILE_SIZE, tiles.TILE_SIZE)

        for gy, line in enumerate(rows):
            row: list[int] = []
            for gx, ch in enumerate(line):
                if ch.upper() == "P":
                    spawn = (gx * tiles.TILE_SIZE, gy * tiles.TILE_SIZE)
                    row.append(int(tiles.CHARSET["."]))  # sub P e aer
                else:
                    row.append(int(tiles.CHARSET.get(ch, tiles.Tile.AIR)))
            grid.append(row)

        return cls(grid, spawn)

    def draw(self, ctx):
        ts = self.tile_size
        for gy, row in enumerate(self.grid):
            for gx, tid in enumerate(row):
                sheet_name, src = tiles.sprite_info(tid)
                x, y = gx * ts, gy * ts
                if sheet_name and src:
                    sheet = ctx.images.load(sheet_name)  # <— din ctx
                    sgx, sgy = src
                    area = Rect(sgx * ts, sgy * ts, ts, ts)
                    ctx.screen.surface.blit(sheet, (x, y), area)
                else:
                    ctx.screen.draw.filled_rect(Rect(x, y, ts, ts), tiles.color_of(tid))
