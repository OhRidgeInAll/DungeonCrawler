
VOID = 'void'
FLOOR = 'floor'
WALL_TOP = 'wall_top'
WALL_SIDE = 'wall_side'
WALL_END = 'wall_end'
HAZARD = 'hazard'
DECOR = 'decor'
SHADOW = 'shadow'

#I have probably over labelled this idk if im letting someone even join this project

TILE_DEFS = {
    0: (VOID, 'Void'),
    1: (WALL_TOP, 'Top of Wall (purple)'),
    2: (WALL_TOP, 'Top of Wall, horizontal edge - south end of a wall piece, above a wall side piece (purple)'),
    3: (WALL_TOP, 'Top of Wall, vertical edge - left/right edge of a wall strip (purple)'),
    4: (FLOOR, 'Purple Tile, broken/dirty ground'),
    5: (WALL_SIDE, 'Side of Wall, segment (purple)'),
    6: (WALL_SIDE, 'Side of Wall, vent (purple)'),
    7: (DECOR, 'Edge of ground, pipe - extends off the tile edge into the void'),
    8: (FLOOR, 'Brown Tile'),
    9: (FLOOR, 'Purple Tile'),
    10: (WALL_SIDE, 'Side of Wall, control panel (purple)'),
    11: (WALL_SIDE, 'Side of Wall, window (purple)'),
    12: (WALL_SIDE, 'Side of Wall, floor light (purple)'),
    13: (WALL_SIDE, 'Side of Wall, low segment variant (purple)'),
    14: (WALL_SIDE, 'Side of Wall, wall mounted light (purple)'),
    15: (FLOOR, 'Purple Tile, clean metal'),
    16: (FLOOR, 'Purple Tile, metal minor tiling'),
    17: (FLOOR, 'Purple Tile, metal tiling'),
    18: (FLOOR, 'Green Tile, moss'),
    19: (FLOOR, 'Purple Tile, metal dank tiling'),
    20: (FLOOR, 'Purple Tile, caution lines'),
    21: (FLOOR, 'Purple Tile, checkerboard'),
    22: (FLOOR, 'Green Tile, checkerboard'),
    23: (FLOOR, 'Green Tile, exposed purple tile'),
    24: (FLOOR, 'Purple Tile, tiling + dank - transition piece for easing from a purple section into a '
                 'dank/mossy one; example combos: 15>16>17>24, or 19>52. Contextual, not a random-fill tile.'),
    25: (FLOOR, 'Blue Tile (stone)'),
    26: (FLOOR, 'Raised mossy rusted Purple Tile'),
    27: (HAZARD, 'Side of Oil Pit - used surrounded by caution tiles, like a wall-edge piece but recessed into the floor'),
    28: (DECOR, 'Top of Big Cylinder, dark, left piece'),
    29: (DECOR, 'Top of Big Cylinder, dark, right piece'),
    30: (DECOR, 'Top of Big Cylinder, light, left piece'),
    31: (DECOR, 'Top of Big Cylinder, light, right piece'),
    32: (WALL_SIDE, 'Side of Wall, sensors (purple)'),
    33: (FLOOR, 'Purple Tile, grate vertical'),
    34: (HAZARD, 'Oil Pit'),
    35: (HAZARD, 'Oil Ripples'),
    36: (FLOOR, 'Purple Tile, grate horizontal'),
    37: (WALL_SIDE, 'Side of Wall, wavy marking (purple)'),
    38: (WALL_END, 'Top of Wall, east end cap (purple)'),
    39: (DECOR, 'Blockade, purple tile (closed) - toggleable with 56 by some world element'),
    40: (DECOR, 'Bottom of Big Cylinder, dark, left piece'),
    41: (DECOR, 'Bottom of Big Cylinder, dark, right piece'),
    42: (DECOR, 'Bottom of Big Cylinder, light, left piece'),
    43: (DECOR, 'Bottom of Big Cylinder, light, right piece'),
    44: (FLOOR, 'Purple Tile, loose mossy'),
    45: (WALL_END, 'Top of Wall, north end cap (purple)'),
    46: (DECOR, 'Side of Floor (purple) - edge of a room before the void; place at the south edge of the '
                 'southernmost tiles, or as a wall base if the room is walled'),
    47: (FLOOR, 'Purple Tile, mossy shingles, minor rust'),
    48: (FLOOR, 'Purple Tile, RED caution lines'),
    49: (WALL_SIDE, 'Side of Wall, red floor lights (purple)'),
    50: (WALL_SIDE, 'Side of Wall, red wall mounted light (purple)'),
    51: (FLOOR, 'RED Tile'),
    52: (FLOOR, 'Dank stone metal striped tile'),
    53: (WALL_END, 'Top of Wall, south end cap (purple)'),
    54: (FLOOR, 'Purple Tile, mossy divoted tile'),
    55: (FLOOR, 'Purple Tile, mossy shingles, major rust (variant)'),
    56: (DECOR, 'Blockade, purple tile, receded/open - toggleable with 39 by some world element'),
    59: (SHADOW, 'Shadow on side of wall, left corner'),
    60: (SHADOW, 'Shadow on floor, upper-left corner'),
    61: (SHADOW, 'Shadow on floor, left edge of wall (rotate for north edge of wall)'),
    62: (SHADOW, 'Shadow on floor, outside join, upper-left corner'),
}

FLOOR_TILE_INDICES = [4, 9, 15, 16, 17, 44, 47, 54, 55]

def tiles_with_role(role):
    return [idx for idx, (r, _name) in TILE_DEFS.items() if r == role]
