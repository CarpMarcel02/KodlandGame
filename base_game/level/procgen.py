import math
import random

from pygame import Rect

from . import tiles
from .room import Room

ROOM_GAP_TILES = int((76 * 2) / tiles.TILE)
ROOM_GAP = ROOM_GAP_TILES


SIDE_OVERHANG_PX = 43
TOP_OVERHANG_PX = 44

PAD_X_TILES = math.ceil(SIDE_OVERHANG_PX / tiles.TILE)
PAD_Y_TILES = math.ceil(TOP_OVERHANG_PX / tiles.TILE)

ROOM_GAP_X = PAD_X_TILES * 2
ROOM_GAP_Y = PAD_Y_TILES * 2


def _place_adjacent(base, side, w, h):
    if side == "U":
        gap = ROOM_GAP_Y
        cx = base["x"] + base["w"] // 2
        x = cx - w // 2
        y = base["y"] - h - gap
    elif side == "D":
        gap = ROOM_GAP_Y
        cx = base["x"] + base["w"] // 2
        x = cx - w // 2
        y = base["y"] + base["h"] + gap
    elif side == "L":
        gap = ROOM_GAP_X
        cy = base["y"] + base["h"] // 2
        x = base["x"] - w - gap
        y = cy - h // 2
    else:
        gap = ROOM_GAP_X
        cy = base["y"] + base["h"] // 2
        x = base["x"] + base["w"] + gap
        y = cy - h // 2
    return {"x": x, "y": y, "w": w, "h": h}


def _overlap_padded(a, b, pad_x, pad_y):
    ax0 = a["x"] - pad_x
    ay0 = a["y"] - pad_y
    ax1 = a["x"] + a["w"] + pad_x
    ay1 = a["y"] + a["h"] + pad_y
    bx0 = b["x"] - pad_x
    by0 = b["y"] - pad_y
    bx1 = b["x"] + b["w"] + pad_x
    by1 = b["y"] + b["h"] + pad_y
    return not (ax1 <= bx0 or bx1 <= ax0 or ay1 <= by0 or by1 <= ay0)


def generate_world(seed=None, target_rooms=6, first_size=(20, 15), min_size=15, max_size=30):

    if seed is not None:
        random.seed(seed)

    rooms = []
    links = []

    w0, h0 = first_size
    a = {"x": 0, "y": 0, "w": int(w0), "h": int(h0)}
    rooms.append(a)
    frontier = [0]

    max_tries = target_rooms * 20
    tries = 0
    while len(rooms) < target_rooms and tries < max_tries and frontier:
        tries += 1
        base_idx = random.choice(frontier)
        base = rooms[base_idx]

        for side in random.sample(["U", "D", "L", "R"], 4):
            w = random.randint(min_size, max_size)
            h = random.randint(min_size, max_size)

            cand = _place_adjacent(base, side, w, h)

            pad_x, pad_y = PAD_X_TILES, PAD_Y_TILES
            bad = False
            for r in rooms:
                if _overlap_padded(cand, r, pad_x, pad_y):
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

    width = max_x + shift_x
    height = max_y + shift_y

    wall_id = int(tiles.Tile.WALL)
    floor_id = int(tiles.Tile.FLOOR)
    door_id = int(tiles.Tile.DOOR)
    void_id = int(tiles.Tile.VOID)

    grid = [[void_id for _ in range(width)] for __ in range(height)]

    for r in rooms:
        x0, y0, w, h = r["x"], r["y"], r["w"], r["h"]
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                is_border = x == x0 or x == x0 + w - 1 or y == y0 or y == y0 + h - 1
                grid[y][x] = wall_id if is_border else floor_id

    door_rects = []
    door_marks = []
    doors_info_tmp = []
    for ai, bi, side in links:
        a = rooms[ai]
        b = rooms[bi]

        if side == "U" and not (b["y"] + b["h"] == a["y"]):
            a, b = b, a
            side = "D"
        elif side == "D" and not (a["y"] + a["h"] == b["y"]):
            a, b = b, a
            side = "U"
        elif side == "L" and not (b["x"] + b["w"] == a["x"]):
            a, b = b, a
            side = "R"
        elif side == "R" and not (a["x"] + a["w"] == b["x"]):
            a, b = b, a
            side = "L"

        res_list = _carve_double_door(grid, a, b, side, width, height, door_id, tiles.TILE)
        if not res_list:
            continue

        _fill_corridor_between_doors(grid, res_list, width, height, int(tiles.Tile.HALL))

        for gx, gy, orient in res_list:
            door_marks.append((gx, gy, orient))
            if orient == "H":
                r = Rect(gx * tiles.TILE, gy * tiles.TILE, 2 * tiles.TILE, tiles.TILE)
            else:
                r = Rect(gx * tiles.TILE, gy * tiles.TILE, tiles.TILE, 2 * tiles.TILE)
            door_rects.append((orient, r))
            doors_info_tmp.append((orient, gx, gy, r, (ai, bi)))

    first = rooms[0]
    spawn_xy = (
        (first["x"] + first["w"] // 2) * tiles.TILE,
        (first["y"] + first["h"] // 2) * tiles.TILE,
    )

    doors = {}
    for orient, r in door_rects:
        gx, gy = r.x // tiles.TILE, r.y // tiles.TILE
        doors[(orient, gx, gy)] = r
    pad = 3

    grid, doors, spawn_xy = _pad_world(grid, doors, spawn_xy, pad, tiles.TILE, void_id)

    rooms_meta = []
    for i, r in enumerate(rooms):
        rx = r["x"] + pad
        ry = r["y"] + pad
        rw = r["w"]
        rh = r["h"]
        rect_full_g = Rect(rx, ry, rw, rh)
        rect_inner_g = Rect(rx + 1, ry + 1, max(0, rw - 2), max(0, rh - 2))
        cx = rect_inner_g.centerx
        cy = rect_inner_g.centery
        rooms_meta.append(
            {
                "id": i,
                "rect_g": rect_full_g,
                "rect_inner_g": rect_inner_g,
                "center_g": (cx, cy),
                "doors": [],
                "state": "cleared" if i == 0 else "unvisited",
            }
        )

    adj = {i: [] for i in range(len(rooms))}
    for ai, bi, _side in links:
        if bi not in adj[ai]:
            adj[ai].append(bi)
        if ai not in adj[bi]:
            adj[bi].append(ai)

    door_meta = {}
    for orient, gx, gy, _rect_before_pad, (ai, bi) in doors_info_tmp:
        key = (orient, gx + pad, gy + pad) if False else (orient, gx, gy)

        key = (orient, gx, gy)

        rect_px = doors.get(key)
        if rect_px is None:
            continue

        door_meta[key] = {"rect_px": rect_px, "orient": orient, "rooms": (ai, bi)}
        rooms_meta[ai]["doors"].append(key)
        rooms_meta[bi]["doors"].append(key)

    room = Room(grid=grid, doors=doors, spawn_xy=spawn_xy)
    room.rooms_meta = rooms_meta
    room.door_meta = door_meta
    room.adj = adj
    room.start_room_id = 0

    return room


def _pad_world(grid, doors, spawn_xy, pad, tile_size, void_id):
    old_h = len(grid)
    old_w = len(grid[0]) if old_h else 0
    new_w = old_w + 2 * pad
    new_h = old_h + 2 * pad

    new_grid = [[void_id for _ in range(new_w)] for __ in range(new_h)]

    for y in range(old_h):
        row_old = grid[y]
        row_new = new_grid[y + pad]
        for x in range(old_w):
            row_new[x + pad] = row_old[x]

    sx, sy = spawn_xy
    sx += pad * tile_size
    sy += pad * tile_size

    new_doors = {}
    for key, r in doors.items():
        r.x += pad * tile_size
        r.y += pad * tile_size
        new_doors[key] = r

    return new_grid, new_doors, (sx, sy)


def _carve_double_door(grid, a, b, side, width, height, door_id, tile_size):
    if side in ("U", "D"):
        start = max(a["x"] + 1, b["x"] + 1)
        end = min(a["x"] + a["w"] - 2, b["x"] + b["w"] - 2)
        if start > end:
            return None
        x0 = (start + end) // 2
        x0 = max(1, min(width - 3, x0))

        y_a = a["y"] if side == "U" else a["y"] + a["h"] - 1
        y_b = b["y"] + b["h"] - 1 if side == "U" else b["y"]

        for x in (x0, x0 + 1):
            if 0 <= x < width:
                if 0 <= y_a < height:
                    grid[y_a][x] = door_id
                if 0 <= y_b < height:
                    grid[y_b][x] = door_id

        return [(x0, y_a, "H"), (x0, y_b, "H")]

    else:
        start = max(a["y"] + 1, b["y"] + 1)
        end = min(a["y"] + a["h"] - 2, b["y"] + b["h"] - 2)
        if start > end:
            return None
        y0 = (start + end) // 2
        y0 = max(1, min(height - 3, y0))

        x_a = a["x"] if side == "L" else a["x"] + a["w"] - 1
        x_b = b["x"] + b["w"] - 1 if side == "L" else b["x"]

        for y in (y0, y0 + 1):
            if 0 <= y < height:
                if 0 <= x_a < width:
                    grid[y][x_a] = door_id
                if 0 <= x_b < width:
                    grid[y][x_b] = door_id

        return [(x_a, y0, "V"), (x_b, y0, "V")]


def _fill_corridor_between_doors(grid, res_list, width, height, hall_id):

    if not res_list or len(res_list) < 2:
        return

    (x1, y1, o1), (x2, y2, o2) = res_list[0], res_list[1]
    assert o1 == o2, "both door halves must have same orientation"
    if o1 == "H":
        x0 = x1
        y_start = min(y1, y2) + 1
        y_stop = max(y1, y2)
        for y in range(y_start, y_stop):
            for x in (x0, x0 + 1):
                if 0 <= x < width and 0 <= y < height:
                    grid[y][x] = hall_id
    else:
        y0 = y1
        x_start = min(x1, x2) + 1
        x_stop = max(x1, x2)
        for x in range(x_start, x_stop):
            for y in (y0, y0 + 1):
                if 0 <= x < width and 0 <= y < height:
                    grid[y][x] = hall_id
