from enum import IntEnum

TILE = 32

class Tile(IntEnum):
    FLOOR = 0
    WALL  = 1
    DOOR  = 2

PROPS = {
    Tile.FLOOR: {"solid": False, "sprite": "floor"},   # podea simplă, pe culoare
    Tile.WALL:  {"solid": True,  "sprite": "wall"},        # <- numele fișierului, fără .png
    Tile.DOOR:  {"solid": False, "sprite": "door"},
}

def is_solid(tid: int) -> bool:
    return PROPS.get(Tile(tid), {}).get("solid", False)

def color_of(tid: int):
    return PROPS.get(Tile(tid), {}).get("color", (255, 0, 255))

CHARSET = {
    ".": Tile.FLOOR,
    "#": Tile.WALL,
    "U": Tile.DOOR, "D": Tile.DOOR, "L": Tile.DOOR, "R": Tile.DOOR,
    "P": Tile.FLOOR,
}
