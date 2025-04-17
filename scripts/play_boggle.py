import pyautogui
import time
import argparse
import keyboard
from typing import List, Tuple
from overlay import draw_overlay_path

# === CONFIG ===
GRID_SIZE = 4
SCREEN_TOP_LEFT = (800, 500)
SCREEN_BOTTOM_RIGHT = (1400, 1100)
TILE_DELAY = 0.05
WORD_DELAY = 0.2

# === HELPERS ===
def get_tile_coordinates() -> List[List[Tuple[int, int]]]:
    x1, y1 = SCREEN_TOP_LEFT
    x2, y2 = SCREEN_BOTTOM_RIGHT
    tile_w = (x2 - x1) // GRID_SIZE
    tile_h = (y2 - y1) // GRID_SIZE
    coords = []
    for r in range(GRID_SIZE):
        row = []
        for c in range(GRID_SIZE):
            cx = x1 + c * tile_w + tile_w // 2
            cy = y1 + r * tile_h + tile_h // 2
            row.append((cx, cy))
        coords.append(row)
    return coords

def click_path(path: List[Tuple[int, int]], tile_coords):
    for (r, c) in path:
        x, y = tile_coords[r][c]
        pyautogui.moveTo(x, y)
        pyautogui.mouseDown()
        time.sleep(TILE_DELAY)
    x, y = tile_coords[path[-1][0]][path[-1][1]]
    pyautogui.mouseUp()
    time.sleep(TILE_DELAY)
    pyautogui.click(x, y)

def draw_path(path: List[Tuple[int, int]], tile_coords):
    print("\n🔍 Path:", path)
    for (r, c) in path:
        x, y = tile_coords[r][c]
        print(f" -> ({r},{c}) @ ({x},{y})")

def play_words(paths: List[Tuple[str, List[Tuple[int, int]]]], preview_only=False):
    tile_coords = get_tile_coordinates()
    print("\n▶ Controls: SPACE = next word, ESC = exit preview\n")

    for i, (word, path) in enumerate(paths):
        print(f"\n▶ Word {i+1}/{len(paths)}: {word} ({len(path)} letters)")
        draw_path(path, tile_coords)
        draw_overlay_path(path, word)

        if preview_only:
            print("⏸️ Waiting for SPACE to continue, ESC to quit...")
            while True:
                if keyboard.is_pressed("space"):
                    break
                elif keyboard.is_pressed("esc"):
                    print("⛔ Preview exited early by user.")
                    return
                time.sleep(0.05)
        else:
            click_path(path, tile_coords)
            time.sleep(WORD_DELAY)
