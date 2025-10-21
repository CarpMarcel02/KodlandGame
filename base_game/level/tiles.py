# base_game/level/tiles.py
from enum import IntEnum
from pygame import Rect
from pgzero.loaders import images as pgz_images 

TILE = 32
TOP_CAP_H = 72              
EXTRA_WALL_TOP = TOP_CAP_H - TILE   
_SIDE = None
_BOTTOM = None
_TOP_END_L = None
_TOP_END_R = None
_BOTTOM_END = None

class Tile(IntEnum):
    FLOOR = 0
    WALL  = 1
    DOOR  = 2
    VOID  = 3 

PROPS = {
    Tile.FLOOR: {"solid": False, "sprite": "floor"},
    Tile.WALL:  {"solid": True,  "sprite": "wall"},
    Tile.DOOR:  {"solid": False, "sprite": "door"},
    Tile.VOID:  {"solid": False, "sprite": None},  

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

_IMAGE_CACHE = {}

def _load_sprite(name: str):
    if not name:
        return None
    if name in _IMAGE_CACHE:
        return _IMAGE_CACHE[name]
    try:
        spr = pgz_images.load(name)          
        _IMAGE_CACHE[name] = spr             
        print(f"[SPRITE] loaded '{name}.png'")
        return spr
    except Exception as e:
        print(f"[SPRITE] MISSING '{name}.png' → fallback color. ({e})")
        _IMAGE_CACHE[name] = None
        return None

def draw_tile(ctx, tid: int, x: int, y: int):
    from pygame import Rect
    t = Tile(tid)

    if t == Tile.VOID:
        return

    if t == Tile.WALL:
        return  

    if t == Tile.FLOOR:
        name = PROPS.get(t, {}).get("sprite") or "floor"
        try:
            spr = ctx.images.load(name)
            ctx.screen.blit(spr, (x, y))
        except Exception:
            ctx.screen.draw.filled_rect(Rect(x, y, TILE, TILE), (35, 35, 35))
        return

    if t == Tile.DOOR:
        name = PROPS.get(t, {}).get("sprite") or "door"
        try:
            spr = ctx.images.load(name)
            ctx.screen.blit(spr, (x, y))
        except Exception:
            ctx.screen.draw.filled_rect(Rect(x, y, TILE, TILE), (140, 120, 40))
        return

    ctx.screen.draw.filled_rect(Rect(x, y, TILE, TILE), (255, 0, 255))

def draw_wall_side_12x32(ctx, x, y, side):

    global _SIDE
    if _SIDE is None:
        _SIDE = _try_load(ctx, "wall_side_12x32")
    if not _SIDE:
        return

    if side == "L":
        ctx.screen.blit(_SIDE, (x + (TILE - 12), y)) 
    else:  
        ctx.screen.blit(_SIDE, (x, y))

def draw_wall_bottom(ctx, x, y):

    global _BOTTOM
    if _BOTTOM is None:
        _BOTTOM = _try_load(ctx, "wall_side_bottom") 
    if not _BOTTOM:
        return

    w = _BOTTOM.get_width()
    h = _BOTTOM.get_height()

    ox = x + (TILE - w) // 2
    oy = y

    ctx.screen.blit(_BOTTOM, (ox, oy))

def draw_wall_bottom_end(ctx, x, y, side):

    global _BOTTOM_END
    if _BOTTOM_END is None:
        _BOTTOM_END = _try_load(ctx, "margins_bottom_12x12") 
    if not _BOTTOM_END:
        return

    w = _BOTTOM_END.get_width()
    h = _BOTTOM_END.get_height()

    oy = y
    if side == "L":
        ox = x - w
    else:  # "R"
        ox = x + TILE
    ctx.screen.blit(_BOTTOM_END, (ox, oy))

def draw_wall_top_end(ctx, x, y, side):

    global _TOP_END_L, _TOP_END_R

    if side == "L":
        if _TOP_END_L is None:
            _TOP_END_L = _try_load(ctx, "margins-top")
        spr = _TOP_END_L
    else:  # "R"
        if _TOP_END_R is None:
            _TOP_END_R = _try_load(ctx, "margins-top")
        spr = _TOP_END_R

    if not spr:
        return

    extra = get_extra_wall_top(ctx)  
    w = spr.get_width()

    if side == "L":
        ctx.screen.blit(spr, (x - w, y - extra))   
    else:
        ctx.screen.blit(spr, (x + TILE, y - extra))  

def _try_load(ctx, name):
    try:
        return ctx.images.load(name)  
    except Exception:
        return None

def draw_wall32(ctx, x, y):
    spr = _try_load(ctx, "wall")
    if spr:
        ctx.screen.blit(spr, (x, y))
    else:
        from pygame import Rect
        ctx.screen.draw.filled_rect(Rect(x, y, TILE, TILE), (70,70,70))



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