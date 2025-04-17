import cv2
import numpy as np
import threading
import time

GRID_SIZE = 4
SCREEN_TOP_LEFT = (800, 500)
SCREEN_BOTTOM_RIGHT = (1400, 1100)
TILE_DISPLAY_TIME = 0.7

def get_tile_coordinates():
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

def draw_overlay_path(path, word):
    tile_coords = get_tile_coordinates()
    screen_w = SCREEN_BOTTOM_RIGHT[0] + 100
    screen_h = SCREEN_BOTTOM_RIGHT[1] + 100

    img = np.zeros((screen_h, screen_w, 4), dtype=np.uint8)
    color = (0, 255, 255, 200)

    for i in range(len(path) - 1):
        r1, c1 = path[i]
        r2, c2 = path[i + 1]
        pt1 = tile_coords[r1][c1]
        pt2 = tile_coords[r2][c2]
        cv2.line(img, pt1, pt2, color, 3)

    for idx, (r, c) in enumerate(path):
        cx, cy = tile_coords[r][c]
        cv2.circle(img, (cx, cy), 18, (255, 255, 255, 220), -1)
        cv2.putText(img, str(idx + 1), (cx - 6, cy + 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0, 255), 2)

    last = tile_coords[path[-1][0]][path[-1][1]]
    cv2.putText(img, word, (last[0] + 25, last[1]),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255, 255), 2)

    def show():
        window_name = "Boggle Path Overlay"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
        cv2.imshow(window_name, img)
        cv2.waitKey(int(TILE_DISPLAY_TIME * 1000))
        cv2.destroyWindow(window_name)

    threading.Thread(target=show, daemon=True).start()

def show_paused_label(word: str):
    screen_w = SCREEN_BOTTOM_RIGHT[0] + 100
    screen_h = SCREEN_BOTTOM_RIGHT[1] + 100
    img = np.zeros((screen_h, screen_w, 4), dtype=np.uint8)

    text = f"Paused: {word}"
    cv2.putText(img, text,
                (SCREEN_TOP_LEFT[0] + 20, SCREEN_TOP_LEFT[1] - 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                (255, 255, 0, 255), 3)

    def show():
        window_name = "Paused Info"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
        cv2.imshow(window_name, img)
        cv2.waitKey(1)  # Wait until manually dismissed or overdrawn

    threading.Thread(target=show, daemon=True).start()

def close_all_overlays():
    try:
        cv2.destroyAllWindows()
    except:
        pass
