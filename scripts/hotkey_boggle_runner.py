import keyboard
import subprocess
import threading
import time

# === CONFIG ===
TRIGGER_HOTKEY = 'ctrl+alt+b'
PAUSE_HOTKEY = 'ctrl+alt+p'
NEXT_WORD_HOTKEY = 'space'

IS_PLAYING = False
IS_PREVIEW = True  # Set to True to run in preview mode
PAUSE_FLAG = threading.Event()
PAUSE_FLAG.set()

# === FUNCTION ===
def run_boggle():
    global IS_PLAYING
    if IS_PLAYING:
        print("⚠️ Already running.")
        return

    IS_PLAYING = True
    print("\n🚀 Starting Boggle run...\n")
    args = ["python", "scripts/auto_boggle_runner.py"]
    if IS_PREVIEW:
        args.append("--preview")

    process = subprocess.Popen(args)
    process.wait()
    IS_PLAYING = False
    print("\n✅ Finished.")

# === KEYBOARD LOOP ===
def keyboard_listener():
    print("\n🎮 Listening for hotkeys...")
    print(f"▶ Trigger: {TRIGGER_HOTKEY}\n▶ Pause:   {PAUSE_HOTKEY}\n▶ Next (Preview only): {NEXT_WORD_HOTKEY}")

    keyboard.add_hotkey(TRIGGER_HOTKEY, lambda: threading.Thread(target=run_boggle).start())

    def toggle_pause():
        if PAUSE_FLAG.is_set():
            print("⏸️ Paused")
            PAUSE_FLAG.clear()
        else:
            print("▶️ Resumed")
            PAUSE_FLAG.set()

    keyboard.add_hotkey(PAUSE_HOTKEY, toggle_pause)
    keyboard.wait()

if __name__ == "__main__":
    keyboard_listener()
