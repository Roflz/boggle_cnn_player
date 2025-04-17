import os
import shutil
import string
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

# === CONFIG ===
MISCLASSIFIED_DIR = os.path.join("data", "misclassified")
LABELED_DIR = os.path.join("data", "boggle_tiles")
BONUS_CLASSES = ['normal', 'DL', 'TL', 'DW', 'TW']
BONUS_COLORS = ['gray', 'blue', 'cyan', 'green', 'red']

class RelabelGUI:
    def __init__(self):
        self.files = sorted([f for f in os.listdir(MISCLASSIFIED_DIR) if f.endswith(".png")])
        self.index = 0
        self.letter = '?'  # fallback/default guess
        self.bonus = 0

        self.root = tk.Tk()
        self.root.title("Relabel Misclassified Tiles")
        self.root.configure(bg="#222")

        self.image_label = tk.Label(self.root, bg="#222")
        self.image_label.pack(pady=10)

        self.status = tk.Label(self.root, text="", fg="white", bg="#222", font=("Courier", 12))
        self.status.pack()

        self.feedback = tk.Label(self.root, text="", fg="yellow", bg="#222", font=("Courier", 10))
        self.feedback.pack()

        self.root.bind("<Key>", self.key_press)

        self.load_image()
        self.root.mainloop()

    def load_image(self):
        if self.index >= len(self.files):
            messagebox.showinfo("Done", "All tiles reviewed.")
            self.root.quit()
            return

        fname = self.files[self.index]
        self.current_path = os.path.join(MISCLASSIFIED_DIR, fname)
        self.pil_img = Image.open(self.current_path).convert("RGB")
        self.tk_img = ImageTk.PhotoImage(self.pil_img.resize((256, 256)))
        self.image_label.config(image=self.tk_img)
        self.feedback.config(text="")
        self.update_status()

    def update_status(self):
        bonus_text = BONUS_CLASSES[self.bonus]
        self.status.config(text=f"Tile {self.index + 1}/{len(self.files)} — Letter: {self.letter}, Bonus: {bonus_text}")

    def key_press(self, event):
        key = event.keysym.upper()
        if key in string.ascii_uppercase:
            self.letter = key
            self.feedback.config(text=f"✔ Letter set to {key}")
        elif key in ['1', '2', '3', '4', '5']:
            self.bonus = int(key) - 1
            self.feedback.config(text=f"✔ Bonus set to {BONUS_CLASSES[self.bonus]}")
        elif key == 'RETURN':
            self.confirm()
        elif key == 'Z':
            self.index = max(0, self.index - 1)
            self.load_image()
        elif key == 'Q':
            self.root.quit()
        self.update_status()

    def confirm(self):
        if self.letter == '?':
            messagebox.showwarning("No letter", "Please assign a letter using A–Z before saving.")
            return

        out_dir = os.path.join(LABELED_DIR, self.letter.upper())
        os.makedirs(out_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(self.current_path))[0]
        out_path = os.path.join(out_dir, f"{base}__bonus-{BONUS_CLASSES[self.bonus]}.png")
        shutil.move(self.current_path, out_path)
        print(f"✔ Relabeled and moved to: {out_path}")

        self.index += 1
        self.load_image()

if __name__ == "__main__":
    RelabelGUI()
