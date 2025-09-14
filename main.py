import tkinter as tk
import threading
import time
import random
from typing import Optional, Tuple
from ja_pow import *

def group_hex(h, step=8):
    s = str(h)
    return " ".join(s[i:i+step] for i in range(0, len(s), step))

def scroll_to_block(idx: int):
    bbox = canvas.bbox(f"block-{idx}")
    allbox = canvas.bbox("all")
    if not bbox or not allbox:
        return
    x1, y1, x2, y2 = bbox
    ax1, ay1, ax2, ay2 = allbox
    block_w = x2 - x1
    view_w = max(canvas.winfo_width(), 1)
    target_left = x1 - (view_w - block_w) / 2
    target_left = max(ax1, min(target_left, max(ax2 - view_w, ax1)))
    frac = 0.0 if (ax2 - ax1) == 0 else (target_left - ax1) / (ax2 - ax1)
    canvas.xview_moveto(frac)

def add_block(block: Optional[JABlock]) -> None:
    if block is None:
        return
    block_w, block_h, gap = 300, 400, 50
    pad = 12
    font = ("Courier New", 10)
    count = len(canvas.find_withtag("block"))
    x1 = count * (block_w + gap) + gap
    h = canvas.winfo_height() or 500
    y1 = (h - block_h) // 2
    x2, y2 = x1 + block_w, y1 + block_h
    canvas.create_rectangle(x1, y1, x2, y2, fill="lightblue", outline="black", tags=("block", f"block-{block.index}"))
    text = (
        f"Block {block.index}\n"
        f"Prev:\n{group_hex(block.prev_hash)}\n"
        f"Msg:\n{block.msg}\n"
        f"Nonce: {block.nonce}\n"
        f"Hash:\n{group_hex(block.block_hash)}"
    )
    canvas.create_text(x1 + pad, y1 + pad, text=text, width=block_w - 2*pad, anchor="nw", font=font, tags=("label", f"block-{block.index}"))
    canvas.config(scrollregion=canvas.bbox("all"))
    scroll_to_block(block.index)

class MinerController:
    def __init__(self, ui_root: tk.Tk):
        self.root = ui_root
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.running = False
        self.index = 1
        self.prev_hash = "0" * 64
        self.msg_template = "Block #{}"
        self.difficulty = 4
        self.algorithm = "sha256"
        self.method = "Sequential ↑"
        self.batch_size = 50000
        self.last_nonce = 0
        self.reverse_nonce = (1 << 31) - 1
        self.mixed_toggle = False
        self.pbkdf2_rounds = 2000

    def set_difficulty(self, val):
        self.difficulty = int(val)

    def set_algorithm(self):
        self.algorithm = algo_var.get()

    def set_method(self, name: str):
        self.method = name

    def start(self):
        if self.running:
            return
        self.running = True
        self.stop_event.clear()
        self.pause_event.clear()
        status_var.set("Mining…")
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()

    def pause_resume(self):
        if not self.running:
            return
        if not self.pause_event.is_set():
            self.pause_event.set()
            status_var.set("Paused")
        else:
            self.pause_event.clear()
            status_var.set("Mining…")

    def reset(self):
        self.stop_event.set()
        self.pause_event.clear()
        self.running = False
        canvas.delete("all")
        self.index = 1
        self.prev_hash = "0" * 64
        self.last_nonce = 0
        self.reverse_nonce = (1 << 31) - 1
        self.mixed_toggle = False
        status_var.set("Idle")
        scroll_to_block(1)

    def _worker_loop(self):
        while not self.stop_event.is_set():
            if self.pause_event.is_set():
                time.sleep(0.05)
                continue
            idx = self.index
            msg = self.msg_template.format(idx)
            prev = self.prev_hash
            diff = self.difficulty
            alg = self.algorithm
            method = self.method
            found, block = self._mine_block_batched(idx, msg, prev, diff, alg, method)
            if not found or block is None or self.stop_event.is_set():
                break
            def ui_update(b=block):
                add_block(b)
                status_var.set(f"Found block {b.index} (nonce={b.nonce})")
            self.root.after(0, ui_update)
            self.prev_hash = block.block_hash
            self.index += 1
        self.running = False

    def _next_nonce_seed(self, method: str) -> int:
        if method == "Sequential ↑":
            n = self.last_nonce
            self.last_nonce += 1
            return n
        if method == "Sequential ↓":
            n = self.reverse_nonce
            self.reverse_nonce -= 1
            return n
        if method == "Stride 7":
            n = self.last_nonce
            self.last_nonce += 7
            return n
        if method == "Random":
            return random.getrandbits(64)
        if method == "Mixed":
            self.mixed_toggle = not self.mixed_toggle
            if self.mixed_toggle:
                return random.getrandbits(64)
            n = self.last_nonce
            self.last_nonce += 1
            return n
        n = self.last_nonce
        self.last_nonce += 1
        return n

    def _mine_block_batched(self, index: int, msg: str, prev_hash: str, difficulty: int, algorithm: str, method: str) -> Tuple[bool, Optional[JABlock]]:
        prefix = "0" * int(difficulty)
        nonce = self._next_nonce_seed(method)
        while not self.stop_event.is_set():
            end = nonce + self.batch_size if method not in ("Sequential ↓",) else nonce - self.batch_size
            while (nonce < end) if method not in ("Sequential ↓",) else (nonce > end):
                if self.pause_event.is_set() or self.stop_event.is_set():
                    break
                header = ja_make_header(prev_hash, msg, int(time.time()), nonce)
                hhex = ja_compute_hash(header, algorithm, self.pbkdf2_rounds)
                if ja_meets_difficulty(hhex, difficulty):
                    return True, JABlock(index, msg, prev_hash, nonce, hhex)
                if method == "Sequential ↑":
                    nonce += 1
                elif method == "Sequential ↓":
                    nonce -= 1
                elif method == "Stride 7":
                    nonce += 7
                elif method == "Random":
                    nonce = random.getrandbits(64)
                elif method == "Mixed":
                    if self.mixed_toggle:
                        nonce = random.getrandbits(64)
                    else:
                        nonce += 1
                    self.mixed_toggle = not self.mixed_toggle
                else:
                    nonce += 1
            time.sleep(0)
            if self.pause_event.is_set():
                while self.pause_event.is_set() and not self.stop_event.is_set():
                    time.sleep(0.05)
        return False, None

root = tk.Tk()
root.title("app")
root.geometry("1200x680")

title = tk.Label(root, text="Blockchain Simulation", font=("Arial", 16, "bold"))
title.pack(side="top", pady=10)

wrap = tk.Frame(root)
wrap.pack(fill="both", expand=True)

h_scroll = tk.Scrollbar(wrap, orient="horizontal")
h_scroll.pack(side="bottom", fill="x")

canvas = tk.Canvas(wrap, bg="white", xscrollcommand=h_scroll.set)
canvas.pack(side="left", fill="both", expand=True)
h_scroll.config(command=canvas.xview)

controls = tk.Frame(root)
controls.pack(side="bottom", fill="x", pady=8)

status_var = tk.StringVar(value="Idle")
tk.Label(controls, textvariable=status_var).pack(side="left", padx=12)

miner = MinerController(root)

tk.Label(controls, text="Difficulty:").pack(side="left", padx=6)
tk.Scale(controls, from_=1, to=7, orient="horizontal", length=200, command=miner.set_difficulty).pack(side="left", padx=4)

tk.Label(controls, text="Hash algo:").pack(side="left", padx=6)
algo_var = tk.StringVar(value="sha256")
for name in ("sha256", "blake2b", "pbkdf2"):
    tk.Radiobutton(controls, text=name.upper(), value=name, variable=algo_var, command=miner.set_algorithm).pack(side="left")

tk.Label(controls, text="Nonce method:").pack(side="left", padx=6)
methods = ["Sequential ↑", "Sequential ↓", "Stride 7", "Random", "Mixed"]
method_var = tk.StringVar(value=methods[0])
method_menu = tk.OptionMenu(controls, method_var, methods[0], *methods, command=lambda v: miner.set_method(str(v)))
method_menu.pack(side="left", padx=4)

tk.Button(controls, text="Start", command=miner.start).pack(side="right", padx=6)
tk.Button(controls, text="Pause/Resume", command=miner.pause_resume).pack(side="right", padx=6)
tk.Button(controls, text="Reset", command=miner.reset).pack(side="right", padx=6)

root.mainloop()
