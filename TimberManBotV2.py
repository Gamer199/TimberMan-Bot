"""
Timberman Bot V2 - Fast bot with lookahead for the Steam version of Timberman.

Improvements over V1:
- mss for fast screen capture (~5ms vs ~50ms)
- keyboard lib for near-instant key input
- Tight loop instead of threading.Timer (target <20ms cycle)
- 3-row branch lookahead to avoid getting trapped
- Auto-detects game window position
- Theme-agnostic branch detection (learns background at start)
- Debug mode to verify pixel positions

Usage:
    python TimberManBotV2.py          # Normal mode
    python TimberManBotV2.py --debug  # Debug mode (saves annotated screenshot)
"""

import sys
import time
import math
import ctypes
import ctypes.wintypes

import mss
import numpy as np
import keyboard
import constant

# Make process DPI-aware so we get physical pixel coordinates (not scaled)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


# ── Win32 helpers ──────────────────────────────────────────────────────────

_game_hwnd = None


def find_game_window():
    """Find the Timberman window and return (left, top, width, height) of the client area."""
    global _game_hwnd
    hwnd = ctypes.windll.user32.FindWindowW(None, constant.WINDOW_TITLE)
    if not hwnd:
        # Try partial match
        found = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
        def enum_cb(h, _):
            length = ctypes.windll.user32.GetWindowTextLengthW(h)
            if length:
                buf = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(h, buf, length + 1)
                if "timber" in buf.value.lower():
                    found.append(h)
            return True

        ctypes.windll.user32.EnumWindows(enum_cb, 0)
        if not found:
            return None
        hwnd = found[0]

    _game_hwnd = hwnd

    # Get the client area (game content, excluding title bar/borders)
    rect = ctypes.wintypes.RECT()
    ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(rect))

    # Convert client rect to screen coordinates
    point = ctypes.wintypes.POINT(0, 0)
    ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(point))

    return (point.x, point.y, rect.right, rect.bottom)


def focus_game_window():
    """Bring the Timberman window to the foreground."""
    if _game_hwnd:
        # Simulate Alt key press to bypass SetForegroundWindow restriction
        keyboard.press('alt')
        ctypes.windll.user32.SetForegroundWindow(_game_hwnd)
        keyboard.release('alt')
        time.sleep(0.3)


# ── Fast keyboard input via SendInput ──────────────────────────────────────

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
VK_LEFT = 0x25
VK_RIGHT = 0x27


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.wintypes.WORD),
        ("wScan", ctypes.wintypes.WORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]

    _fields_ = [
        ("type", ctypes.wintypes.DWORD),
        ("_input", _INPUT),
    ]


def send_key(vk_code):
    """Send a key press+release via SendInput (fastest possible on Windows)."""
    inputs = (INPUT * 2)()

    # Key down
    inputs[0].type = INPUT_KEYBOARD
    inputs[0]._input.ki.wVk = vk_code

    # Key up
    inputs[1].type = INPUT_KEYBOARD
    inputs[1]._input.ki.wVk = vk_code
    inputs[1]._input.ki.dwFlags = KEYEVENTF_KEYUP

    ctypes.windll.user32.SendInput(2, ctypes.byref(inputs), ctypes.sizeof(INPUT))


def press_left():
    keyboard.press_and_release('left')


def press_right():
    keyboard.press_and_release('right')


# ── Branch detection ──────────────────────────────────────────────────────

def color_distance(c1, c2):
    return math.sqrt((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2)


def detect_biome(img, win_w, win_h):
    """Detect which biome the current round is using based on sky color."""
    sky_x = int(win_w * constant.SKY_SAMPLE_X)
    sky_y = int(win_h * constant.SKY_SAMPLE_Y)
    sky_pixel = img.pixel(sky_x, sky_y)[:3]

    best_biome = None
    best_dist = float("inf")
    for biome, sky_ref in constant.BIOME_SKY.items():
        d = color_distance(sky_pixel, sky_ref)
        if d < best_dist:
            best_dist = d
            best_biome = biome

    return best_biome, sky_pixel


# Active branch colors (set per round after biome detection)
_active_colors = constant.BRANCH_COLORS


def set_active_biome(biome_name):
    """Set active branch colors based on detected biome."""
    global _active_colors
    if biome_name in constant.BIOME_COLORS:
        _active_colors = constant.BIOME_COLORS[biome_name]
    else:
        _active_colors = constant.BRANCH_COLORS


def is_branch_color(pixel):
    """Check if pixel matches any active branch wood color within tolerance."""
    for ref in _active_colors:
        if all(abs(pixel[i] - ref[i]) <= constant.COLOR_TOLERANCE for i in range(3)):
            return True
    return False


def detect_branch_at(img, x_positions, y_pos):
    """Check if a branch exists at the given row using color matching."""
    for x in x_positions:
        pixel = img.pixel(x, y_pos)[:3]
        if is_branch_color(pixel):
            return True
    return False


def detect_branch_np(img_arr, x_positions, y_pos):
    """Fast branch detection using numpy BGRA uint8 array."""
    for x in x_positions:
        pixel = (int(img_arr[y_pos, x, 2]), int(img_arr[y_pos, x, 1]), int(img_arr[y_pos, x, 0]))
        if is_branch_color(pixel):
            return True
    return False


def learn_background_colors(img, left_xs, right_xs, sample_ys):
    """
    Learn the background color by sampling at multiple y positions
    and finding the most common color at each check position.
    """
    from collections import Counter

    def mode_color(x_pos, ys):
        colors = []
        for y in ys:
            try:
                c = img.pixel(x_pos, y)[:3]
                colors.append(c)
            except Exception:
                pass
        if not colors:
            return None
        counter = Counter(colors)
        return counter.most_common(1)[0][0]

    # Use the middle x position from each side
    left_bg = mode_color(left_xs[len(left_xs) // 2], sample_ys)
    right_bg = mode_color(right_xs[len(right_xs) // 2], sample_ys)

    return left_bg, right_bg


# ── Main bot logic ────────────────────────────────────────────────────────

def run_bot(debug=False):
    # Find game window
    win = find_game_window()
    if not win:
        print("ERROR: Could not find Timberman window!")
        print("Make sure Timberman is running in windowed mode.")
        return

    win_x, win_y, win_w, win_h = win
    print(f"Found game window: pos=({win_x}, {win_y}), size={win_w}x{win_h}")

    # Calculate absolute pixel positions from relative offsets
    left_check_xs = [int(win_w * frac) for frac in constant.LEFT_CHECK_X]
    right_check_xs = [int(win_w * frac) for frac in constant.RIGHT_CHECK_X]

    row_ys = []
    for i in range(constant.LOOKAHEAD_ROWS):
        y = int(win_h * (constant.FIRST_ROW_Y - i * constant.ROW_SPACING))
        row_ys.append(y)

    gameover_x = int(win_w * constant.GAMEOVER_X)
    gameover_y = int(win_h * constant.GAMEOVER_Y)

    print(f"Left check X positions:  {left_check_xs}")
    print(f"Right check X positions: {right_check_xs}")
    print(f"Branch row Y positions:  {row_ys}")
    print(f"Game over check: ({gameover_x}, {gameover_y})")

    # Screen capture region (the game window)
    monitor = {
        "left": win_x,
        "top": win_y,
        "width": win_w,
        "height": win_h,
    }

    sct = mss.mss()

    if debug:
        print("Focusing Timberman window for screenshot...")
        focus_game_window()
        time.sleep(0.5)  # Wait for window to come to foreground
        run_debug_mode(sct, monitor, left_check_xs, right_check_xs, row_ys,
                       gameover_x, gameover_y, win_w, win_h)
        return

    # Wait for user to press F1 to start
    print()
    print("Press F1 to START the bot (make sure the game is ready to play)")
    print("Press F1 again to STOP the bot")
    keyboard.wait("f1")
    print("Focusing Timberman window...")
    focus_game_window()
    print("Starting in 0.5 seconds...")
    time.sleep(0.5)

    # Take initial screenshot to detect biome and learn background colors
    img = sct.grab(monitor)

    biome, sky_pixel = detect_biome(img, win_w, win_h)
    set_active_biome(biome)
    print(f"Detected biome: {biome} (sky color: {sky_pixel})")
    print(f"Active branch colors: {len(_active_colors)} colors")

    sample_ys = [int(win_h * f) for f in [0.1, 0.15, 0.2, 0.25, 0.4, 0.5, 0.6]]
    left_bg, right_bg = learn_background_colors(img, left_check_xs, right_check_xs, sample_ys)
    print(f"Learned background colors: left={left_bg}, right={right_bg}")

    # Main loop
    running = True
    chop_count = 0
    last_direction = "right"
    cycle_times = []

    def stop_bot():
        nonlocal running
        running = False

    keyboard.on_press_key("f1", lambda _: stop_bot())

    print("Bot running! Press F1 to stop.")

    while running:
        t_start = time.perf_counter()

        # Capture game window as numpy array (BGRA uint8)
        img = np.array(sct.grab(monitor))

        # Check game over (cast to int to avoid uint8 overflow)
        go_r, go_g, go_b = int(img[gameover_y, gameover_x, 2]), int(img[gameover_y, gameover_x, 1]), int(img[gameover_y, gameover_x, 0])
        if abs(go_r - constant.ARROW[0]) <= 15 and abs(go_g - constant.ARROW[1]) <= 15 and abs(go_b - constant.ARROW[2]) <= 15:
            print(f"Game Over! Score: ~{chop_count - 3} (chops: {chop_count})")
            break

        # Detect branches at each row using numpy
        branches = []  # list of ("left", "right", or None) per row
        for y in row_ys:
            if y < 0 or y >= win_h:
                branches.append(None)
                continue

            has_left = detect_branch_np(img, left_check_xs, y)
            has_right = detect_branch_np(img, right_check_xs, y)

            if has_left:
                branches.append("left")
            elif has_right:
                branches.append("right")
            else:
                branches.append(None)

        # Decision logic with lookahead
        direction = decide_direction(branches, last_direction)

        # Log first 20 chops for debugging
        if chop_count < 20:
            print(f"  Chop {chop_count}: branches={branches} -> {direction}")

        # Wait before pressing key — match game's input timing
        elapsed = time.perf_counter() - t_start
        remaining = 0.25 - elapsed
        if remaining > 0:
            time.sleep(remaining)

        # Press key
        if direction == "left":
            press_left()
        else:
            press_right()

        last_direction = direction
        chop_count += 1

        # Track cycle time
        t_end = time.perf_counter()
        cycle_ms = (t_end - t_start) * 1000
        cycle_times.append(cycle_ms)

        # Print stats periodically
        if chop_count % 200 == 0:
            avg = sum(cycle_times[-200:]) / len(cycle_times[-200:])
            print(f"Chops: {chop_count}, avg cycle: {avg:.1f}ms")

    # Print final stats
    if cycle_times:
        avg = sum(cycle_times) / len(cycle_times)
        min_t = min(cycle_times)
        max_t = max(cycle_times)
        print(f"\nStats: {chop_count} chops, avg cycle: {avg:.1f}ms, "
              f"min: {min_t:.1f}ms, max: {max_t:.1f}ms")


def decide_direction(branches, last_direction):
    """
    Decide which direction to chop based on branch positions.

    branches: list of ("left", "right", or None) for each row,
              index 0 = closest row (must avoid), higher = further ahead

    Strategy:
    - Row 0 (immediate threat): MUST avoid this branch
    - Row 1-2 (lookahead): prefer the side that's safe for more rows ahead
    - If no branches visible: alternate sides for fastest chopping
    """
    if not branches:
        return "left" if last_direction == "right" else "right"

    # Row 0: immediate threat - must go to opposite side
    if branches[0] == "left":
        return "right"
    if branches[0] == "right":
        return "left"

    # No immediate branch - use lookahead to preposition
    if len(branches) > 1 and branches[1] is not None:
        # Next branch is coming - preposition to the opposite side
        if branches[1] == "left":
            return "right"
        if branches[1] == "right":
            return "left"

    if len(branches) > 2 and branches[2] is not None:
        if branches[2] == "left":
            return "right"
        if branches[2] == "right":
            return "left"

    # No branches visible - stay on current side (don't alternate into unseen branches)
    return last_direction


# ── Debug/calibration mode ────────────────────────────────────────────────

def run_debug_mode(sct, monitor, left_xs, right_xs, row_ys, go_x, go_y, win_w, win_h):
    """Capture a frame, annotate it with check positions, and save for verification."""
    from PIL import Image, ImageDraw

    print("\n=== DEBUG MODE ===")
    print("Capturing current game frame...")

    img = sct.grab(monitor)

    # Detect biome
    biome, sky_pixel = detect_biome(img, win_w, win_h)
    set_active_biome(biome)
    print(f"Detected biome: {biome} (sky color: {sky_pixel})")
    print(f"Active branch colors: {len(_active_colors)} colors for {biome}")

    # Convert to PIL image for drawing
    pil_img = Image.frombytes("RGB", (img.width, img.height), img.rgb)
    draw = ImageDraw.Draw(pil_img)

    # Draw branch check positions
    for row_idx, y in enumerate(row_ys):
        if y < 0 or y >= win_h:
            continue

        # Left check positions (red circles)
        for x in left_xs:
            draw.ellipse([x - 5, y - 5, x + 5, y + 5], outline="red", width=2)
            pixel = img.pixel(x, y)[:3]
            is_branch = is_branch_color(pixel)
            label = f"L{row_idx} ({pixel[0]},{pixel[1]},{pixel[2]})"
            if is_branch:
                label += " BRANCH!"
            draw.text((x + 8, y - 5), label, fill="red")

        # Right check positions (blue circles)
        for x in right_xs:
            draw.ellipse([x - 5, y - 5, x + 5, y + 5], outline="blue", width=2)
            pixel = img.pixel(x, y)[:3]
            is_branch = is_branch_color(pixel)
            label = f"R{row_idx} ({pixel[0]},{pixel[1]},{pixel[2]})"
            if is_branch:
                label += " BRANCH!"
            draw.text((x + 8, y - 5), label, fill="blue")

    # Draw game over check position (green)
    draw.ellipse([go_x - 5, go_y - 5, go_x + 5, go_y + 5], outline="green", width=2)
    go_pixel = img.pixel(go_x, go_y)[:3]
    draw.text((go_x + 8, go_y - 5), f"GO ({go_pixel[0]},{go_pixel[1]},{go_pixel[2]})", fill="green")

    # Check branches at each row
    for row_idx, y in enumerate(row_ys):
        if y < 0 or y >= win_h:
            continue
        has_left = detect_branch_at(img, left_xs, y)
        has_right = detect_branch_at(img, right_xs, y)
        print(f"Row {row_idx} (y={y}): left_branch={has_left}, right_branch={has_right}")

    # Save annotated image
    output_path = "debug_screenshot.png"
    pil_img.save(output_path)
    print(f"\nAnnotated screenshot saved to: {output_path}")
    print("Check the image to verify that the check positions align with the branches.")
    print("If positions are off, adjust the constants in constant.py")


# ── Entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    debug = "--debug" in sys.argv
    run_bot(debug=debug)
