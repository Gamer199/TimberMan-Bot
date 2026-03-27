# author: Gamer199
SAVANNA = (204, 128, 23)
OAK = (163, 150, 63)
NIGHT = (79, 132, 146)
TAIGA = (168, 194, 193)
COLORS = [SAVANNA, OAK, NIGHT, TAIGA]
ARROW = (157, 33, 42)
ARROWCOLOR = [ARROW]

# --- V2 Bot constants ---

# Branch detection color tolerance (RGB Euclidean distance)
COLOR_TOLERANCE = 25

# Additional branch colors observed in screenshots (edges, highlights)
SAVANNA_LIGHT = (235, 167, 73)
SAVANNA_DARK = (142, 89, 16)
OAK_LIGHT = (209, 196, 100)
NIGHT_LIGHT = (118, 175, 191)
TAIGA_LIGHT = (241, 255, 255)

# New biomes added in updates
CITY = (91, 200, 196)
CITY_DARK = (73, 170, 168)
CANDY = (241, 139, 71)
CANDY_LIGHT = (255, 170, 113)

BRANCH_COLORS = [
    SAVANNA, SAVANNA_LIGHT, SAVANNA_DARK,
    OAK, OAK_LIGHT,
    NIGHT, NIGHT_LIGHT,
    TAIGA, TAIGA_LIGHT,
    CITY, CITY_DARK,
    CANDY, CANDY_LIGHT,
]

# Per-biome color groups (used after biome auto-detection to avoid cross-biome false positives)
BIOME_COLORS = {
    "savanna": [SAVANNA, SAVANNA_LIGHT, SAVANNA_DARK],
    "oak": [OAK, OAK_LIGHT],
    "night": [NIGHT, NIGHT_LIGHT],
    "taiga": [TAIGA, TAIGA_LIGHT],
    "city": [CITY, CITY_DARK],
    "candy": [CANDY, CANDY_LIGHT],
}

# Sky reference colors per biome (sampled at x=400, y=50 - reliable sky position)
# Used for biome auto-detection at game start
BIOME_SKY = {
    "savanna": (219, 153, 177),
    "oak": (149, 176, 171),
    "night": (15, 15, 25),
    "taiga": (32, 57, 83),
    "city": (141, 55, 128),
    "candy": (53, 206, 252),
}

# Sky sample position for biome detection (fraction of window width/height)
# x=400 is far from trunk, avoids timer bar and branches
SKY_SAMPLE_X = 0.208  # x≈400 in 1920px client
SKY_SAMPLE_Y = 0.046  # y≈50 in 1080px client

# Relative branch check positions (fractions of game client area width/height)
# Based on original bot's coordinates in 1920x1080 physical pixels:
#   Game client area: x=3, y=28, width=1916, height=1052
#   Left branch zone:  x=690-834,  y=342-378
#   Right branch zone: x=1133-1241, y=338-374

# Left branch check X positions (fraction of client width)
LEFT_CHECK_X = [0.360, 0.396, 0.430]  # ~x=690,760,825 in 1916px client
# Right branch check X positions
RIGHT_CHECK_X = [0.590, 0.617, 0.645]  # ~x=1130,1183,1236 in 1916px client

# Y offset for the first branch row (fraction of client height from top)
# Row 0 = near the chop level (closest to player, immediate danger)
# Higher rows = further up the tree (lookahead)
# The branch at y≈324 is ~3 segments above player; chop level is at y≈540
FIRST_ROW_Y = 0.500  # ~y=540 in 1080px client (near chop level)
# Vertical spacing between branch rows (fraction of client height)
ROW_SPACING = 0.045  # ~49px per row
# Number of branch rows to check (covers chop level to top of visible tree)
LOOKAHEAD_ROWS = 6  # rows at y≈540, 491, 443, 394, 345, 297

# Game over detection pixel (fraction of client width/height)
GAMEOVER_X = 0.503  # ~x=966 in 1920px client
GAMEOVER_Y = 0.910  # ~y=983 in 1080px client (screen y=1015 minus title bar y=32)

# Window title for auto-detection
WINDOW_TITLE = "Timberman"