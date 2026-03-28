# Timberman Biomes

## Status Overview

| # | Biome | Sky Color | Branch Colors | Status | Screenshot |
|---|-------|-----------|---------------|--------|------------|
| 1 | Savanna | (219, 153, 177) | (204,128,23) (235,167,73) (142,89,16) | Untested (may have changed) | TimberMan.png |
| 2 | Night | (15, 15, 25) | (79,132,146) (118,175,191) | Working ✓ | TimberMan3.png |
| 3 | Taiga/Snow | (32, 57, 83) | (168,194,193) (241,255,255) | Untested | TimberMan4.png |
| 4 | City/Neon | (141, 55, 128) | (91,200,196) (73,170,168) | Working | TimberMan10.png |
| 5 | Candy | (53, 206, 252) | (241,139,71) (255,170,113) | Working | TimberMan11.png |
| 6 | Forest (new) | (133, 181, 255) | (51,176,123) (56,219,150) | Broken - not in bot yet | TimberMan12.png |
| 7 | Oak (old) | (149, 176, 171) | (163,150,63) (209,196,100) | Broken - may no longer exist | TimberMan2.png |

## Notes

- The game was updated since the original bot was written, changing some biome colors
- Biome is auto-detected by sampling sky color at (x=400, y=50) in client area
- Forest (TimberMan12.png) was previously detected as "candy" because sky colors are close
- Oak (old) sky (149,176,171) may no longer appear in the current game version
- Savanna and Taiga need retesting to confirm colors haven't changed
