# boggle_launcher_gui.py

import tkinter as tk
import subprocess
import sys
import os

class BoggleLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Boggle Bot Launcher")
        self.root.geometry("300x180")
        self.root.configure(bg="#1e1e1e")

        tk.Label(self.root, text="Select Run Mode",
                 font=("Helvetica", 14, "bold"),
                 fg="white", bg="#1e1e1e").pack(pady=10)

        tk.Button(self.root,
                  text="🔍 Preview Mode (Step-by-step)",
                  command=self.run_preview,
                  width=30, bg="#444", fg="white"
        ).pack(pady=6)

        tk.Button(self.root,
                  text="🤖 Live Mode (Auto Play)",
                  command=self.run_live,
                  width=30, bg="#555", fg="white"
        ).pack(pady=6)

        tk.Button(self.root,
                  text="❌ Cancel",
                  command=self.root.destroy,
                  width=30, bg="#333", fg="white"
        ).pack(pady=12)

        self.root.mainloop()

    def run_preview(self):
        self.launch_script(preview=True)

    def run_live(self):
        self.launch_script(preview=False)

    def launch_script(self, preview):
        # Ensure we invoke the same interpreter and correct script path
        script = os.path.join(os.path.dirname(__file__), "auto_boggle_runner.py")
        args = [sys.executable, script]
        if preview:
            args.append("--preview")
        subprocess.Popen(args)
        self.root.destroy()

if __name__ == "__main__":
    BoggleLauncher()
