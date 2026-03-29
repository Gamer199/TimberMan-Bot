A simple Bot which plays the [Timberman Steam Version](https://store.steampowered.com/app/398710/Timberman/) on Windows, it is only working in Single Player.

## V2 Bot (TimberManBotV2.py)

An improved bot with faster screen capture, auto window detection, and branch lookahead.

### Features:
- **Auto-detects game window** — no hardcoded screen coordinates
- **Auto-detects biome** — works across all 7 biomes (Savanna, Oak, Night, Taiga, City, Candy, Forest)
- **DPI-aware** — works correctly on scaled displays
- **Numpy-accelerated screen capture** — optimized capture region for fast pixel reads
- **6-row branch lookahead** — checks multiple positions up the tree
- **Per-biome color tolerance** — prevents false positives (e.g. Taiga sky gradient)
- **F1 hotkey** — start/stop from any window, auto-focuses the game
- **Debug mode** — saves annotated screenshot to verify check positions

### Instructions:
1. Install dependencies: `pip install -r requirements.txt`
2. Open Timberman in Windowed Mode
3. Go to Single Player and start the round
4. Run `python TimberManBotV2.py`
5. Press **F1** to start the bot (works from any window)
6. Press **F1** again to stop, or the bot stops automatically when you die

### Debug Mode:
Run `python TimberManBotV2.py --debug` to capture a screenshot with annotated check positions. Useful for verifying pixel positions when adding new biomes.

### High Score: 2034

## V1 Bot (TimberManBot.py)

The original bot. Simpler but requires manual coordinate setup.

### Instructions:
1. Open Timberman in Windowed Mode
2. Go to Single Player and start the round
3. When chopping is ready start the script
4. The Script stops automatically, when you die

### Additional Notes:

The script is not perfect.

Sometimes when the branches start on the right side you die.

When the game lags the bot doesn't work really well.

The Snow Biome often lags.

This bot wasn't written for multiplayer, but can be modified, by changing the coordinates, which check if branches are nearby.
