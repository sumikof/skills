"""
{APP_NAME} - メインエントリーポイント
"""
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Windows高DPI対応
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("{APP_NAME}")
        self.geometry("800x600")
        self.resizable(True, True)
        self._setup_ui()

    def _setup_ui(self):
        # メインフレーム
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ウィジェットをここに追加する
        label = ttk.Label(main_frame, text="Hello, World!")
        label.pack(pady=20)

        btn = ttk.Button(main_frame, text="クリック", command=self._on_click)
        btn.pack()

    def _on_click(self):
        messagebox.showinfo("情報", "ボタンがクリックされました")


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
