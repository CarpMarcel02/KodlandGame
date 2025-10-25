# base_game/level/tiles.py
from enum import IntEnum
from pygame import Rect
from pgzero.loaders import images as pgz_images 

TILE = 32
TOP_CAP_H = 72              
EXTRA_WALL_TOP = TOP_CAP_H - TILE   


class Tile(IntEnum):
    FLOOR = 0
    WALL  = 1
    DOOR  = 2
    VOID  = 3 
    HALL  = 4

PROPS = {
    Tile.FLOOR: {"solid": False, "sprite": "floor"},
    Tile.WALL:  {"solid": True,  "sprite": "wall"},
    Tile.DOOR:  {"solid": False, "sprite": "door"},
    Tile.VOID:  {"solid": False, "sprite": None},  
    Tile.HALL:  {"solid": False, "sprite": "floor_hall1"},

}

def is_solid(tid: int) -> bool:
    return PROPS.get(Tile(tid), {}).get("solid", False)

def color_of(tid: int):
    return (90, 90, 90) if is_solid(tid) else (25, 25, 25)

CHARSET = {
    ".": Tile.FLOOR, "#": Tile.WALL,
    "U": Tile.DOOR, "D": Tile.DOOR, "L": Tile.DOOR, "R": Tile.DOOR,
    "P": Tile.FLOOR,
}


def draw_tile(ctx, tid: int, x: int, y: int):
    t = Tile(tid)

    if t in (Tile.VOID, Tile.WALL, Tile.DOOR):
        return

    if t in (Tile.FLOOR, Tile.HALL):
        name = PROPS.get(t, {}).get("sprite") or "floor"
        try:
            spr = ctx.images.load(name)   
            ctx.screen.blit(spr, (x, y))
        except Exception:
            ctx.screen.draw.filled_rect(Rect(x, y, TILE, TILE), (35, 35, 35))
        return

    ctx.screen.draw.filled_rect(Rect(x, y, TILE, TILE), (255, 0, 255))

def draw_wall_side_12x32(ctx, x, y, side):
    SIDE_OFFSET = 43  
    spr = None

    if side == "L":
        spr = _try_load(ctx, "wall_side_left_32x76")
        if not spr:
            return
        ox = x - SIDE_OFFSET

    elif side == "R":
        spr = _try_load(ctx, "wall_side_right_32x76")
        if not spr:
            return
        ox = x + TILE - spr.get_width() + SIDE_OFFSET

    else:
        return

    oy = y - (spr.get_height() - TILE)
    ctx.screen.blit(spr, (ox, oy))
        
def draw_wall_bottom(ctx, x, y):
    spr = _try_load(ctx, "wall_side_bottom_32x76")
    if not spr:
        return

    oy = y + TILE - 32
    ox = x
    ctx.screen.blit(spr, (ox, oy))

def draw_corner_top_left(ctx, x, y):
    spr = _try_load(ctx, "wall_corner_top_left_76x76")
    if not spr:
        return
    SIDE_OFFSET = 43 
    ox = x - SIDE_OFFSET
    oy = y - (spr.get_height() - TILE)
    ctx.screen.blit(spr, (ox, oy))


def draw_corner_top_right(ctx, x, y):
    spr = _try_load(ctx, "wall_corner_top_right_76x76")
    if not spr:
        return
    SIDE_OFFSET = 43 
    ox = x + TILE - spr.get_width() + SIDE_OFFSET
    oy = y - (spr.get_height() - TILE)
    ctx.screen.blit(spr, (ox, oy))


def draw_corner_bottom_left(ctx, x, y):
    spr = _try_load(ctx, "wall_corner_bottom_left_76x76")
    if not spr:
        return
    SIDE_OFFSET = 43  
    ox = x - SIDE_OFFSET
    oy = y - (spr.get_height() - TILE) + 40
    ctx.screen.blit(spr, (ox, oy))


def draw_corner_bottom_right(ctx, x, y):
    spr = _try_load(ctx, "wall_corner_bottom_right_76x76")
    if not spr:
        return
    SIDE_OFFSET = 43 
    ox = x + TILE - spr.get_width() + SIDE_OFFSET
    oy = y - (spr.get_height() - TILE) + 43
    ctx.screen.blit(spr, (ox, oy))

def _try_load(ctx, name):
    try:
        return ctx.images.load(name) 
    except Exception as e:
        print(f"[IMG] missing '{name}.png' ? -> {e}")
        return None


def draw_wall_top_32x76(ctx, x, y):
    spr = _try_load(ctx, "wall_top_32x76")
    if spr:
        extra = get_extra_wall_top(ctx)
        ctx.screen.blit(spr, (x, y - extra))
    else:
        from pygame import Rect
        h = 76
        extra = max(0, h - TILE)
        ctx.screen.draw.filled_rect(Rect(x, y - extra, TILE, h), (90, 90, 100))

_TOP_CAP_SPR = None
_TOP_CAP_EXTRA = None

def get_extra_wall_top(ctx):
    global _TOP_CAP_SPR, _TOP_CAP_EXTRA
    if _TOP_CAP_EXTRA is not None:
        return _TOP_CAP_EXTRA
    if _TOP_CAP_SPR is None:
        _TOP_CAP_SPR = _try_load(ctx, "wall_top_32x76")
    if _TOP_CAP_SPR:
        _TOP_CAP_EXTRA = max(0, _TOP_CAP_SPR.get_height() - TILE)
    else:
        _TOP_CAP_EXTRA = 0
    return _TOP_CAP_EXTRA

DOOR_W = 64
DOOR_H = 76
DOOR_OVERHANG_Y = DOOR_H - TILE  
DOOR_SIDE_OFFSET = 43 

SIDE_INSET_PX = TILE - DOOR_W + DOOR_SIDE_OFFSET  
DOOR_VERT_TOP_ADJUST = DOOR_OVERHANG_Y - TILE     

def draw_closed_door(ctx, variant, x, y):
    name_by_variant = {
        "UP":    "closeddoor_up",
        "DOWN":  "closeddoor_down",
        "LEFT":  "closeddoor_left",
        "RIGHT": "closeddoor_right",
    }
    spr = _try_load(ctx, name_by_variant.get(variant))
    if not spr:
        return
    extra_h = spr.get_height() - TILE 

    if variant == "UP":
        ox = x
        oy = y - extra_h
    elif variant == "DOWN":
        ox = x
        oy = y - extra_h + 44
    elif variant == "LEFT":
        ox = x - DOOR_SIDE_OFFSET
        oy = y - extra_h + 32
    else:  
        ox = x + TILE - spr.get_width() + DOOR_SIDE_OFFSET
        oy = y - extra_h + 32
    ctx.screen.blit(spr, (ox, oy))

def draw_open_door(ctx, variant, x, y):
    name_by_variant = {
        "UP": "opendoor_up",
        "DOWN": "opendoor_down",
        "LEFT": "opendoor_left",
        "RIGHT": "opendoor_right",
    }
    spr = _try_load(ctx, name_by_variant.get(variant))
    if not spr:
        return

    extra_h = spr.get_height() - TILE  

    if variant == "UP":
        ox = x
        oy = y - extra_h
    elif variant == "DOWN":
        ox = x
        oy = y - extra_h + 44
    elif variant == "LEFT":
        ox = x - DOOR_SIDE_OFFSET
        oy = y - extra_h + 32
    else:  
        ox = x + TILE - spr.get_width() + DOOR_SIDE_OFFSET
        oy = y - extra_h + 32

    ctx.screen.blit(spr, (ox, oy))

def door_draw_offset(variant, base_x, base_y):
    if variant == "UP":
        return base_x, base_y - DOOR_OVERHANG_Y
    if variant == "DOWN":
        return base_x, base_y  
    if variant == "LEFT":
        return base_x - SIDE_INSET_PX, base_y - DOOR_VERT_TOP_ADJUST
    return base_x + SIDE_INSET_PX, base_y - DOOR_VERT_TOP_ADJUST   

def door_bbox_px(variant, base_x, base_y):
    ox, oy = door_draw_offset(variant, base_x, base_y)
    return ox, oy, DOOR_W, DOOR_H


def draw_hall_border(ctx, x, y, side: str):
  
    if side == "L":
        spr = _try_load(ctx, "wall_hall_updown") 
        if spr:
            ctx.screen.blit(spr, (x - spr.get_width(), y))
        else:
            ctx.screen.draw.filled_rect(Rect(x - 12, y, 12, TILE), (80, 90, 100))
        return

    if side == "R":
        spr = _try_load(ctx, "wall_hall_updown") 
        if spr:
            ctx.screen.blit(spr, (x + TILE, y))
        else:
            ctx.screen.draw.filled_rect(Rect(x + TILE, y, 12, TILE), (80, 90, 100))
        return

    if side == "U":
        spr = _try_load(ctx, "wall_hall_leftright") 
        if spr:
            ctx.screen.blit(spr, (x, y - spr.get_height()))
        else:
            ctx.screen.draw.filled_rect(Rect(x, y - 12, TILE, 12), (80, 90, 100))
        return

    if side == "D":
        spr = _try_load(ctx, "wall_hall_leftright")   
        if spr:
            ctx.screen.blit(spr, (x, y + TILE))
        else:
            ctx.screen.draw.filled_rect(Rect(x, y + TILE, TILE, 12), (80, 90, 100))
        return