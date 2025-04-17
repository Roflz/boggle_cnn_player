import os
import pytesseract
import torch
import string
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox, Frame, Button, Checkbutton, BooleanVar, font
from torchvision import transforms
from predict_tile_letter import Predictor

# === CONFIG ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNLABELED_DIR = os.path.join(BASE_DIR, "data", "unlabeled_tiles")
LABELED_DIR = os.path.join(BASE_DIR, "data", "boggle_tiles")
MODEL_PATH = os.path.join(BASE_DIR, "models", "cnn_model.pt")
IMG_SIZE = 28
BONUS_CLASSES = ['normal (1)', 'DL (2)', 'TL (3)', 'DW (4)', 'TW (5)']
BONUS_COLORS = ['gray', 'blue', 'cyan', 'green', 'red']

# === Dark Mode Theme ===
BG_COLOR = "#1e1e1e"
TEXT_COLOR = "#e0e0e0"
HIGHLIGHT_COLOR = "#ff7f50"
FEEDBACK_COLOR = "#ffd166"

predictor = Predictor(MODEL_PATH)

def tesseract_guess(pil_img):
    return pytesseract.image_to_string(
        pil_img,
        config='--psm 10 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    ).strip().upper()

class LabelGUI:
    def __init__(self):
        self.files = sorted([f for f in os.listdir(UNLABELED_DIR) if f.endswith(".png")])
        self.index = 0
        self.history = []
        self.correct_cnn = 0
        self.correct_tess = 0
        self.total = 0
        self.bonus = 0
        self.letter_override = None
        self.labeled_basenames = self.get_labeled_basenames()

        self.root = tk.Tk()
        self.root.title("Boggle Tile Labeling Tool")
        self.root.configure(bg=BG_COLOR)

        self.skip_existing = BooleanVar(value=True)
        self.use_cnn_guess = BooleanVar(value=True)
        self.skip_high_confidence = BooleanVar(value=False)

        self.img_label = tk.Label(self.root, bg=BG_COLOR)
        self.img_label.pack(pady=10)

        self.info_font = font.Font(family="Courier", size=12)
        self.info = tk.Label(
            self.root, text="", justify="left",
            font=self.info_font, fg=TEXT_COLOR, bg=BG_COLOR
        )
        self.info.pack()

        self.input_font = font.Font(family="Courier", size=13, weight="bold")
        self.input_label = tk.Label(
            self.root, text="", font=self.input_font,
            fg=HIGHLIGHT_COLOR, bg=BG_COLOR, pady=6
        )
        self.input_label.pack()

        self.feedback = tk.Label(
            self.root, text="", fg=FEEDBACK_COLOR,
            font=("Helvetica", 12, "bold"), bg=BG_COLOR
        )
        self.feedback.pack(pady=5)

        control_frame = Frame(self.root, bg=BG_COLOR)
        control_frame.pack(pady=8)
        Button(
            control_frame, text="✅ Confirm (Enter)",
            command=self.confirm_tile, bg="#444", fg=TEXT_COLOR
        ).pack(side="left", padx=8)
        Button(
            control_frame, text="↩ Undo (Z)",
            command=self.undo_tile, bg="#444", fg=TEXT_COLOR
        ).pack(side="left", padx=8)
        Checkbutton(
            control_frame, text="Skip already labeled",
            variable=self.skip_existing, bg=BG_COLOR,
            fg=TEXT_COLOR, selectcolor=BG_COLOR
        ).pack(side="left", padx=8)
        Checkbutton(
            control_frame, text="Use CNN as default",
            variable=self.use_cnn_guess, bg=BG_COLOR,
            fg=TEXT_COLOR, selectcolor=BG_COLOR
        ).pack(side="left", padx=8)
        Checkbutton(
            control_frame, text="Skip high confidence tiles",
            variable=self.skip_high_confidence, bg=BG_COLOR,
            fg=TEXT_COLOR, selectcolor=BG_COLOR
        ).pack(side="left", padx=8)

        self.help_label = tk.Label(
            self.root,
            text="1 = Normal   2 = DL   3 = TL   4 = DW   5 = TW",
            fg="#888", bg=BG_COLOR, font=("Courier", 10)
        )
        self.help_label.pack()

        self.history_frame = Frame(self.root, bg=BG_COLOR)
        self.history_frame.pack(pady=5)
        self.history_labels = [tk.Label(self.history_frame, bg=BG_COLOR) for _ in range(4)]
        for lbl in self.history_labels:
            lbl.pack(side="left", padx=5)

        self.root.bind("<Key>", self.key_press)

        self.total_tiles = len(self.files)
        self.show_progress()
        self.load_image()
        self.root.mainloop()

    def get_labeled_basenames(self):
        basenames = set()
        for letter_folder in os.listdir(LABELED_DIR):
            path = os.path.join(LABELED_DIR, letter_folder)
            if os.path.isdir(path):
                for f in os.listdir(path):
                    if f.endswith(".png"):
                        base = f.split("__bonus-")[0]
                        basenames.add(base)
        return basenames

    def show_progress(self):
        progress_text = f"Progress: {self.index + 1}/{self.total_tiles} tiles labeled"
        self.info.config(text=progress_text)

    def load_image(self):
        while self.index < len(self.files):
            file = self.files[self.index]
            base = os.path.splitext(file)[0]
            if self.skip_existing.get() and base in self.labeled_basenames:
                # delete even if skipping existing
                self.delete_unlabeled(file)
                self.index += 1
                self.show_progress()
                continue

            path = os.path.join(UNLABELED_DIR, file)
            self.img_pil = Image.open(path).convert("RGB")
            self.tk_img = ImageTk.PhotoImage(self.img_pil.resize((256, 256)))
            self.img_label.config(image=self.tk_img)

            self.tess = tesseract_guess(self.img_pil) or '?'
            self.cnn, self.cnn_bonus, self.cnn_confidence, self.bonus_confidence = predictor.predict_letter_bonus_confidence(self.img_pil)
            self.last_guess = (self.cnn, self.cnn_bonus)
            self.bonus = self.cnn_bonus if self.cnn_bonus != 0 else 0

            # Round confidences to 4 decimals
            cnn_conf = round(self.cnn_confidence, 4)
            bonus_conf = round(self.bonus_confidence, 4)

            if self.skip_high_confidence.get() and cnn_conf >= 0.995 and bonus_conf >= 0.995:
                print(f"Skipping {file} with high confidence. Letter {cnn_conf:.4f}, Bonus {bonus_conf:.4f}")
                # delete tile regardless
                self.delete_unlabeled(file)
                # optionally save low-confidence only
                if cnn_conf < 1.0000 and bonus_conf < 1.0000:
                    self.save_label(self.cnn)
                self.index += 1
                self.show_progress()
                continue

            self.feedback.config(text="")
            self.update_info()
            return

        messagebox.showinfo("Done", "All tiles labeled.")
        self.root.quit()

    def delete_unlabeled(self, filename):
        src = os.path.join(UNLABELED_DIR, filename)
        try:
            os.remove(src)
            print(f"Deleted unlabeled tile: {filename}")
        except Exception as e:
            print(f"⚠️ Could not delete {filename}: {e}")

    def update_info(self):
        file = self.files[self.index]
        bonus_label = BONUS_CLASSES[self.bonus]
        default_letter = self.letter_override or (self.cnn if self.use_cnn_guess.get() else self.tess)

        disagrees = (self.cnn != self.tess and self.cnn != '?' and self.tess != '?')
        flag = "  ⚠️" if self.bonus_confidence < 0.65 else ""

        self.info.config(
            text=(
                f"📄 File:            {file}\n"
                f"🔠 Tesseract Guess: {self.tess}{'  ⛔' if disagrees else ''}\n"
                f"🧠 CNN Guess:       {self.cnn} ({bonus_label}){flag}\n"
                f"   Letter Conf:     {self.cnn_confidence:.1%}\n"
                f"   Bonus Conf:      {self.bonus_confidence:.1%}\n"
            ), fg=TEXT_COLOR, bg=BG_COLOR
        )
        self.input_label.config(
            text=f"👉 Selected Input:  Letter = {default_letter}, Bonus = {bonus_label}"
        )

    def key_press(self, event):
        key = event.keysym.upper()
        if key == 'Q':
            self.letter_override = 'QU'
            self.feedback.config(text="✔ Letter set to QU")
        elif key in string.ascii_uppercase:
            self.letter_override = key
            self.feedback.config(text=f"✔ Letter set to {key}")
        elif key in ['1','2','3','4','5']:
            self.bonus = int(key) - 1
            self.feedback.config(text=f"✔ Bonus set to {BONUS_CLASSES[self.bonus]}")
        elif key == 'RETURN':
            self.confirm_tile()
        elif key == 'Z':
            self.undo_tile()
        elif key == 'ESCAPE':
            self.root.quit()
        self.update_info()

    def confirm_tile(self):
        letter = self.letter_override or (self.cnn if self.use_cnn_guess.get() else self.tess)
        self.save_label(letter)
        self.delete_unlabeled(self.files[self.index])
        self.letter_override = None
        self.index += 1
        if self.cnn_bonus == 0:
            self.bonus = 0
        self.show_progress()
        self.flash_feedback("✔ Saved!", color="#8ef5a0")
        self.load_image()

    def flash_feedback(self, message, color="#8ef5a0"):
        self.feedback.config(text=message, fg=color)
        self.root.after(500, lambda: self.feedback.config(text=""))

    def save_label(self, label):
        bonus_name = BONUS_CLASSES[self.bonus].split()[0]
        out_dir = os.path.join(LABELED_DIR, label)
        os.makedirs(out_dir, exist_ok=True)
        file = self.files[self.index]
        name = os.path.splitext(file)[0]
        output_file = os.path.join(out_dir, f"{name}__bonus-{bonus_name}.png")
        self.img_pil.save(output_file)

        log_path = os.path.join(LABELED_DIR, "guess_log.txt")
        with open(log_path, "a") as log:
            log.write(f"{name}.png -> label:{label}, bonus:{bonus_name}, cnn_guess:{self.last_guess[0]}, cnn_bonus:{BONUS_CLASSES[self.last_guess[1]].split()[0]}, letter_conf:{self.cnn_confidence:.4f}, bonus_conf:{self.bonus_confidence:.4f}\n")

        self.history.append((label, bonus_name, self.bonus, self.tk_img))
        self.history = self.history[-4:]
        self.update_history()

        if self.last_guess[0] == label:
            self.correct_cnn += 1
        if self.tess == label:
            self.correct_tess += 1
        self.total += 1

        print(f"✔ Saved {file} as {label}, Bonus: {bonus_name}")
        print(f"   Accuracy — CNN: {self.correct_cnn}/{self.total}, Tesseract: {self.correct_tess}/{self.total}")

    def undo_tile(self):
        if self.index > 0:
            self.index -= 1
            self.history = self.history[:-1]
            self.update_history()
            self.load_image()

    def update_history(self):
        for i, lbl in enumerate(self.history_labels):
            if i < len(self.history):
                letter, bonus, bonus_index, img = self.history[i]
                lbl.config(image=img, text=f"{letter}\n{bonus}", fg=BONUS_COLORS[bonus_index], bg=BG_COLOR, compound="top")
                lbl.image = img
            else:
                lbl.config(image='', text='')

if __name__ == "__main__":
    LabelGUI()
