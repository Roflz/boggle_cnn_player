import os
import subprocess

# Paths to scripts
SCRIPTS = {
    "crop tiles from screenshots": "scripts/auto_tile_cropper.py",
    "label new tiles": "scripts/tile_label_gui.py",
    "train and evaluate model": "scripts/cnn_tile_classifier.py",
    "relabel misclassified tiles": "scripts/relabel_misclassified_gui.py",
}

def ask_step(name):
    response = input(f"▶ Run step: {name}? [Y/n] ").strip().lower()
    return response in ["", "y", "yes"]

def run(script_path):
    print(f"\n🚀 Running: {script_path}")
    subprocess.run(["python", script_path], check=True)

def main():
    print("=== BOGGLE TILE TRAINING LOOP ===\n")
    for name, path in SCRIPTS.items():
        if ask_step(name):
            run(path)
        else:
            print(f"⏭️ Skipped: {name}")

    print("\n✅ Training loop complete. You can re-run it anytime to continue improving.")

if __name__ == "__main__":
    main()
