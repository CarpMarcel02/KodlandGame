# base_game/level/procgen.py
import random
from pygame import Rect
from . import tiles
from .room import Room

ROOM_GAP = 1 

def _overlap(a, b):
    return not (a["x"] + a["w"] <= b["x"] or
                b["x"] + b["w"] <= a["x"] or
                a["y"] + a["h"] <= b["y"] or
                b["y"] + b["h"] <= a["y"])

def _place_adjacent(base, side, w, h):
    if side == "U":
        cx = base["x"] + base["w"] // 2
        x  = cx - w // 2
        y  = base["y"] - h - ROOM_GAP     
    elif side == "D":
        cx = base["x"] + base["w"] // 2
        x  = cx - w // 2
        y  = base["y"] + base["h"] + ROOM_GAP
    elif side == "L":
        cy = base["y"] + base["h"] // 2
        x  = base["x"] - w - ROOM_GAP
        y  = cy - h // 2
    else:  # "R"
        cy = base["y"] + base["h"] // 2
        x  = base["x"] + base["w"] + ROOM_GAP
        y  = cy - h // 2
    return {"x": x, "y": y, "w": w, "h": h}


def generate_world(seed=None, target_rooms=6,
                   first_size=(20, 15),
                   min_size=15, max_size=30):

    if seed is not None:
        random.seed(seed)

    rooms = []
    links = []   

    w0, h0 = first_size
    a = {"x": 0, "y": 0, "w": int(w0), "h": int(h0)}
    rooms.append(a)
    frontier = [0]

    MAX_TRIES = target_rooms * 20
    tries = 0
    while len(rooms) < target_rooms and tries < MAX_TRIES and frontier:
        tries += 1
        base_idx = random.choice(frontier)
        base = rooms[base_idx]

        for side in random.sample(["U", "D", "L", "R"], 4):
            w = random.randint(min_size, max_size)
            h = random.randint(min_size, max_size)

            cand = _place_adjacent(base, side, w, h)

            bad = False
            for r in rooms:
                if _overlap(cand, r):
                    bad = True
                    break
            if bad:
                continue

            b_idx = len(rooms)
            rooms.append(cand)
            frontier.append(b_idx)
            links.append((base_idx, b_idx, side))
            break

        if random.random() < 0.35:
            try:
                frontier.remove(base_idx)
            except ValueError:
                pass

    min_x = min(r["x"] for r in rooms)
    min_y = min(r["y"] for r in rooms)
    max_x = max(r["x"] + r["w"] for r in rooms)
    max_y = max(r["y"] + r["h"] for r in rooms)

    shift_x = -min_x if min_x < 0 else 0
    shift_y = -min_y if min_y < 0 else 0

    for r in rooms:
        r["x"] += shift_x
        r["y"] += shift_y

    W = max_x + shift_x
    H = max_y + shift_y

    WALL = int(tiles.Tile.WALL)
    FLOOR = int(tiles.Tile.FLOOR)
    DOOR = int(tiles.Tile.DOOR)
    VOID  = int(tiles.Tile.VOID)

    grid = [[VOID for _ in range(W)] for __ in range(H)]  

    for r in rooms:
        x0, y0, w, h = r["x"], r["y"], r["w"], r["h"]
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                is_border = (x == x0 or x == x0 + w - 1 or y == y0 or y == y0 + h - 1)
                grid[y][x] = WALL if is_border else FLOOR

    door_rects = []
    for (ai, bi, side) in links:
        a = rooms[ai]
        b = rooms[bi]

        if side == "U" and not (b["y"] + b["h"] == a["y"]):
            a, b = b, a; side = "D"
        elif side == "D" and not (a["y"] + a["h"] == b["y"]):
            a, b = b, a; side = "U"
        elif side == "L" and not (b["x"] + b["w"] == a["x"]):
            a, b = b, a; side = "R"
        elif side == "R" and not (a["x"] + a["w"] == b["x"]):
            a, b = b, a; side = "L"

        res = _carve_double_door(grid, a, b, side, W, H, DOOR, tiles.TILE)
        if res:
            gx, gy, orient = res
            if orient == "H":
                r = Rect(gx * tiles.TILE, gy * tiles.TILE, 2 * tiles.TILE, tiles.TILE)
            else:
                r = Rect(gx * tiles.TILE, gy * tiles.TILE, tiles.TILE, 2 * tiles.TILE)
            door_rects.append((orient, r))

    first = rooms[0]
    spawn_xy = ((first["x"] + first["w"] // 2) * tiles.TILE,
                (first["y"] + first["h"] // 2) * tiles.TILE)

    doors = {}
    for orient, r in door_rects:
        gx, gy = r.x // tiles.TILE, r.y // tiles.TILE
        doors[(orient, gx, gy)] = r
    PAD = 3  
    grid, doors, spawn_xy = _pad_world(grid, doors, spawn_xy, PAD, tiles.TILE, VOID)

    return Room(grid=grid, doors=doors, spawn_xy=spawn_xy)

def _pad_world(grid, doors, spawn_xy, pad, TILE, VOID):
        old_h = len(grid)
        old_w = len(grid[0]) if old_h else 0
        new_w = old_w + 2 * pad
        new_h = old_h + 2 * pad

        new_grid = [[VOID for _ in range(new_w)] for __ in range(new_h)]

        for y in range(old_h):
            row_old = grid[y]
            row_new = new_grid[y + pad]
            for x in range(old_w):
                row_new[x + pad] = row_old[x]

        sx, sy = spawn_xy
        sx += pad * TILE
        sy += pad * TILE

        new_doors = {}
        for key, r in doors.items():
            r.x += pad * TILE
            r.y += pad * TILE
            new_doors[key] = r

        return new_grid, new_doors, (sx, sy)

def _carve_double_door(grid, a, b, side, W, H, DOOR, TILE):

    if side in ("U", "D"):
        start = max(a["x"] + 1, b["x"] + 1)
        end   = min(a["x"] + a["w"] - 2, b["x"] + b["w"] - 2)
        if start > end:
            return None
        x0 = (start + end) // 2
        x0 = max(1, min(W - 3, x0))  

        y_a = a["y"] if side == "U" else a["y"] + a["h"] - 1
        y_b = b["y"] + b["h"] - 1 if side == "U" else b["y"]

        for x in (x0, x0 + 1):
            if 0 <= x < W:
                if 0 <= y_a < H: grid[y_a][x] = DOOR
                if 0 <= y_b < H: grid[y_b][x] = DOOR

        gy = min(y_a, y_b)
        return (x0, gy, "H")

    else:
        start = max(a["y"] + 1, b["y"] + 1)
        end   = min(a["y"] + a["h"] - 2, b["y"] + b["h"] - 2)
        if start > end:
            return None
        y0 = (start + end) // 2
        y0 = max(1, min(H - 3, y0)) 

        x_a = a["x"] if side == "L" else a["x"] + a["w"] - 1
        x_b = b["x"] + b["w"] - 1 if side == "L" else b["x"]

        for y in (y0, y0 + 1):
            if 0 <= y < H:
                if 0 <= x_a < W: grid[y][x_a] = DOOR
                if 0 <= x_b < W: grid[y][x_b] = DOOR

        gx = min(x_a, x_b)
        return (gx, y0, "V")
    
    