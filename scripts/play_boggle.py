# play_boggle.py

import time
import sys
import signal
import pyautogui
import keyboard
from typing import List, Tuple

# Enable PyAutoGUI failsafe
pyautogui.FAILSAFE = True

# === CONFIG ===
GRID_SIZE = 4
SCREEN_TOP_LEFT = (800, 500)
SCREEN_BOTTOM_RIGHT = (1400, 1100)
TILE_DELAY = 0.15
WORD_DELAY = 0.3

PAUSE_KEY = 'p'
EXIT_KEY  = 'esc'

paused = False

# === SIGNAL HANDLER ===
def emergency_exit():
    print("🚨 Emergency exit triggered. Exiting now.")
    keyboard.unhook_all()
    sys.exit(0)

signal.signal(signal.SIGINT, lambda s, f: emergency_exit())

# === HOTKEY HANDLERS ===
def toggle_pause():
    global paused
    paused = not paused
    print("⏸️ Paused." if paused else "▶️ Resumed.")

def get_tile_coordinates() -> List[List[Tuple[int, int]]]:
    x1, y1 = SCREEN_TOP_LEFT
    x2, y2 = SCREEN_BOTTOM_RIGHT
    tile_w = (x2 - x1) // GRID_SIZE
    tile_h = (y2 - y1) // GRID_SIZE
    coords: List[List[Tuple[int, int]]] = []
    for r in range(GRID_SIZE):
        row: List[Tuple[int, int]] = []
        for c in range(GRID_SIZE):
            cx = x1 + c * tile_w + tile_w // 2
            cy = y1 + r * tile_h + tile_h // 2
            row.append((cx, cy))
        coords.append(row)
    return coords

def click_path(path: List[Tuple[int, int]], tile_coords: List[List[Tuple[int, int]]]):
    # press down on first tile
    r0, c0 = path[0]
    x0, y0 = tile_coords[r0][c0]
    while paused: time.sleep(0.1)
    pyautogui.moveTo(x0, y0)
    pyautogui.mouseDown()
    time.sleep(TILE_DELAY)

    # drag through subsequent tiles
    for (r, c) in path[1:]:
        while paused: time.sleep(0.1)
        x, y = tile_coords[r][c]
        pyautogui.moveTo(x, y)
        time.sleep(TILE_DELAY)

    # release & submit
    r_last, c_last = path[-1]
    x_last, y_last = tile_coords[r_last][c_last]
    while paused: time.sleep(0.1)
    pyautogui.mouseUp()
    time.sleep(TILE_DELAY)
    # while paused: time.sleep(0.1)
    # pyautogui.click(x_last, y_last, clicks=2, interval=TILE_DELAY)

def draw_path(path: List[Tuple[int, int]], tile_coords: List[List[Tuple[int, int]]]):
    print("\n🔍 Path:", path)
    for (r, c) in path:
        x, y = tile_coords[r][c]
        print(f" -> ({r},{c}) @ ({x},{y})")

def play_words(paths: List[Tuple[str, List[Tuple[int, int]]]], preview_only: bool = False):
    global paused
    paused = False

    # clear any old hooks, then register ours
    keyboard.unhook_all()
    keyboard.add_hotkey(PAUSE_KEY, toggle_pause)
    keyboard.add_hotkey(EXIT_KEY, emergency_exit)
    if preview_only:
        keyboard.add_hotkey('space', lambda: None)

    tile_coords = get_tile_coordinates()

    if preview_only:
        print("\n▶ Controls (preview): SPACE = next word, ESC = exit preview\n")
    else:
        print("\n▶ Controls (live): P = pause/resume, ESC = emergency stop\n")

    try:
        for i, (word, path) in enumerate(paths, 1):
            print(f"\n▶ Word {i}/{len(paths)}: {word} ({len(path)} letters)")
            draw_path(path, tile_coords)

            if preview_only:
                keyboard.wait('space')
            else:
                while paused:
                    time.sleep(0.1)
                click_path(path, tile_coords)
                time.sleep(WORD_DELAY)
    finally:
        keyboard.unhook_all()
        print("✅ play_words has terminated.")
