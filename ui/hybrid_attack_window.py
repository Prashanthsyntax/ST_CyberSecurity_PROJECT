import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import itertools
import string
import time
import hashlib
import csv

from core.rainbow import RainbowPasswordCracker
from core.hash_identifier import identify_hash
from core.mutator import mutate

BG_DARK   = "#1e1e2e"
BG_CARD   = "#2a2a3e"
BG_ACCENT = "#1e3a4a"
FG_PRIMARY= "#cbd5e1"
FG_MUTED  = "#64748b"
FG_BLUE   = "#7dd3fc"
FG_GREEN  = "#22c55e"
FG_RED    = "#ef4444"
FG_PURPLE = "#a78bfa"
FG_AMBER  = "#fbbf24"
BORDER    = "#3a3a50"
BTN_BLUE  = "#185FA5"

ALGORITHMS = {
    "md5":    lambda w: hashlib.md5(w.encode("latin-1")).hexdigest(),
    "sha1":   lambda w: hashlib.sha1(w.encode("latin-1")).hexdigest(),
    "sha256": lambda w: hashlib.sha256(w.encode("latin-1")).hexdigest(),
    "sha512": lambda w: hashlib.sha512(w.encode("latin-1")).hexdigest(),
    "ntlm":   lambda w: hashlib.new("md4", w.encode("utf-16-le")).hexdigest(),
}

rainbow = RainbowPasswordCracker()

STAGE_COLORS = {
    "waiting": BORDER,
    "running": FG_BLUE,
    "done":    FG_GREEN,
    "skipped": FG_MUTED,
}

STAGES = [
    ("Rainbow Table",   "Rainbow Table",    "Instant lookup — fastest"),
    ("Dictionary",      "Dictionary Attack", "Wordlist against hashes"),
    ("Mutation Engine", "Mutation Engine",   "Leet · caps · suffixes"),
    ("Brute Force",     "Brute Force",       "Charset · length range"),
]


class HybridAttackFrame(tk.Frame):
    def __init__(self, parent, nav=None):
        super().__init__(parent, bg=BG_DARK)
        self.nav = nav

        self.hash_file     = tk.StringVar()
        self.wordlist_file = tk.StringVar()
        self.charset_var   = tk.StringVar(
            value="abcdefghijklmnopqrstuvwxyz0123456789")
        self.min_len       = tk.IntVar(value=1)
        self.max_len       = tk.IntVar(value=4)
        self.running       = False
        self.paused        = False
        self.results       = []

        self.mutation_rules = {
            "leet":       tk.BooleanVar(value=True),
            "capitalise": tk.BooleanVar(value=True),
            "numbers":    tk.BooleanVar(value=True),
            "symbols":    tk.BooleanVar(value=True),
            "reverse":    tk.BooleanVar(value=False),
            "year":       tk.BooleanVar(value=True),
            "duplicate":  tk.BooleanVar(value=False),
        }

        self.stage_labels = {}
        self.rule_btns    = {}

        # ── BUILD ORDER ──────────────────────────────────────
        self._build_titlebar()
        self._build_files_section()
        self._build_stage_indicators()
        self._build_mutation_section()
        self._build_brute_config()
        self._build_stats_bar()
        self._build_progress()
        self._build_buttons()       # buttons BEFORE log
        self._build_statusbar()     # statusbar to bottom
        self._build_log()           # log fills remaining space

    # ── Title bar ────────────────────────────────────────────
    def _build_titlebar(self):
        bar = tk.Frame(self, bg=BG_CARD, height=36)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        for color in ["#ff5f57", "#febc2e", "#28c840"]:
            tk.Label(bar, bg=color, width=2).pack(
                side="left",
                padx=(8 if color == "#ff5f57" else 4, 0),
                pady=10)
        tk.Label(bar,
                 text="Window 3 — Hybrid Attack Engine  "
                      "(Rainbow → Dictionary → Mutation → Brute Force)",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 9)).pack(side="left", padx=12)

    # ── File selectors ───────────────────────────────────────
    def _build_files_section(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(10, 0))

        for label, var in [
            ("HASH FILE",     self.hash_file),
            ("WORDLIST FILE", self.wordlist_file),
        ]:
            tk.Label(frame, text=label,
                     bg=BG_DARK, fg=FG_MUTED,
                     font=("Courier", 8)).pack(anchor="w", pady=(4, 2))

            row = tk.Frame(frame, bg=BG_DARK)
            row.pack(fill="x")

            tk.Entry(row, textvariable=var,
                     bg=BG_CARD, fg=FG_PRIMARY,
                     insertbackground=FG_BLUE,
                     relief="flat",
                     highlightthickness=1,
                     highlightbackground=BORDER,
                     font=("Courier", 10),
                     width=80).pack(side="left", fill="x",
                                    expand=True,
                                    padx=(0, 8), ipady=5)

            tk.Button(row, text="Browse",
                      bg=BG_CARD, fg=FG_BLUE,
                      relief="flat",
                      highlightthickness=1,
                      highlightbackground=BORDER,
                      font=("Courier", 10),
                      activebackground=BG_ACCENT,
                      activeforeground=FG_BLUE,
                      cursor="hand2",
                      padx=10, pady=3,
                      command=lambda v=var: self._browse(v)
                      ).pack(side="left")

    def _browse(self, var):
        path = filedialog.askopenfilename()
        if path:
            var.set(path)

    # ── Stage indicators — single row 1×4 ────────────────────
    def _build_stage_indicators(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(10, 0))

        tk.Label(frame,
                 text="ATTACK STAGES — RUNS IN ORDER",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w", pady=(0, 5))

        grid = tk.Frame(frame, bg=BG_DARK)
        grid.pack(fill="x")
        for i in range(4):
            grid.columnconfigure(i, weight=1)

        for i, (key, name, desc) in enumerate(STAGES):
            card = tk.Frame(grid, bg=BG_CARD,
                            highlightthickness=1,
                            highlightbackground=BORDER)
            card.grid(row=0, column=i,
                      sticky="ew", padx=4, pady=2)

            inner = tk.Frame(card, bg=BG_CARD)
            inner.pack(fill="both", padx=10, pady=7)

            tk.Label(inner, text=f"Stage {i+1}",
                     bg=BG_CARD, fg=FG_MUTED,
                     font=("Courier", 7)).pack(anchor="w")

            lbl = tk.Label(inner, text=name,
                           bg=BG_CARD, fg=FG_PRIMARY,
                           font=("Courier", 9, "bold"))
            lbl.pack(anchor="w")

            tk.Label(inner, text=desc,
                     bg=BG_CARD, fg=FG_MUTED,
                     font=("Courier", 7)).pack(anchor="w")

            self.stage_labels[key] = (card, lbl)

    def _set_stage(self, name, state):
        if name not in self.stage_labels:
            return
        card, lbl = self.stage_labels[name]
        color = STAGE_COLORS.get(state, BORDER)
        card.configure(highlightbackground=color)
        lbl.configure(fg=color)

    # ── Mutation rules ───────────────────────────────────────
    def _build_mutation_section(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(10, 0))

        tk.Label(frame, text="MUTATION RULES",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w", pady=(0, 4))

        row = tk.Frame(frame, bg=BG_DARK)
        row.pack(fill="x")

        rule_labels = {
            "leet":       "Leet speak",
            "capitalise": "Capitalise",
            "numbers":    "Add numbers",
            "symbols":    "Add symbols",
            "reverse":    "Reverse",
            "year":       "Year suffix",
            "duplicate":  "Duplicate",
        }

        for rule, label in rule_labels.items():
            btn = tk.Button(row, text=label,
                            font=("Courier", 9),
                            relief="flat",
                            cursor="hand2",
                            padx=8, pady=4)
            btn.pack(side="left", padx=3)
            self.rule_btns[rule] = btn
            self._refresh_rule_btn(rule)
            btn.configure(
                command=lambda r=rule: self._toggle_rule(r))

    def _refresh_rule_btn(self, rule):
        btn    = self.rule_btns[rule]
        active = self.mutation_rules[rule].get()
        if active:
            btn.configure(
                bg=BG_CARD, fg=FG_BLUE,
                highlightthickness=1,
                highlightbackground=FG_BLUE,
                activebackground=BG_ACCENT,
                activeforeground=FG_BLUE)
        else:
            btn.configure(
                bg=BG_DARK, fg=FG_MUTED,
                highlightthickness=1,
                highlightbackground=BORDER,
                activebackground=BG_DARK,
                activeforeground=FG_PRIMARY)

    def _toggle_rule(self, rule):
        self.mutation_rules[rule].set(
            not self.mutation_rules[rule].get())
        self._refresh_rule_btn(rule)

    # ── Brute force config ───────────────────────────────────
    def _build_brute_config(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(10, 0))

        tk.Label(frame, text="BRUTE FORCE CONFIG",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w", pady=(0, 4))

        row = tk.Frame(frame, bg=BG_DARK)
        row.pack(fill="x")

        tk.Label(row, text="Charset:",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 9)).pack(side="left", padx=(0, 6))

        tk.Entry(row, textvariable=self.charset_var,
                 bg=BG_CARD, fg=FG_PRIMARY,
                 insertbackground=FG_BLUE,
                 relief="flat",
                 highlightthickness=1,
                 highlightbackground=BORDER,
                 font=("Courier", 9),
                 width=38).pack(side="left", ipady=4)

        # Min / Max spinboxes
        for lbl_txt, var in [("Min:", self.min_len),
                              ("Max:", self.max_len)]:
            tk.Label(row, text=lbl_txt,
                     bg=BG_DARK, fg=FG_MUTED,
                     font=("Courier", 9)).pack(
                     side="left", padx=(10, 2))
            tk.Spinbox(row, from_=1, to=8,
                       textvariable=var,
                       bg=BG_CARD, fg=FG_PRIMARY,
                       buttonbackground=BG_CARD,
                       relief="flat", width=3,
                       font=("Courier", 9)
                       ).pack(side="left")

        # Presets
        pr = tk.Frame(frame, bg=BG_DARK)
        pr.pack(fill="x", pady=(4, 0))
        tk.Label(pr, text="Presets:",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(side="left")
        for lbl_txt, val in [
            ("a-z",        string.ascii_lowercase),
            ("a-z+0-9",    string.ascii_lowercase + string.digits),
            ("A-Za-z+0-9", string.ascii_letters + string.digits),
            ("Full",       string.ascii_letters + string.digits
                           + string.punctuation),
        ]:
            tk.Button(pr, text=lbl_txt,
                      bg=BG_CARD, fg=FG_BLUE,
                      relief="flat", font=("Courier", 8),
                      activebackground=BG_ACCENT,
                      command=lambda v=val: self.charset_var.set(v)
                      ).pack(side="left", padx=3)

    # ── Stats bar ────────────────────────────────────────────
    def _build_stats_bar(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(10, 0))

        self.stat_vars = {
            "Total":     tk.StringVar(value="0"),
            "Cracked":   tk.StringVar(value="0"),
            "Remaining": tk.StringVar(value="0"),
            "Current":   tk.StringVar(value="—"),
            "Elapsed":   tk.StringVar(value="0.0s"),
        }
        colors = {
            "Total":     FG_BLUE,
            "Cracked":   FG_GREEN,
            "Remaining": FG_RED,
            "Current":   FG_PURPLE,
            "Elapsed":   FG_PRIMARY,
        }
        for label, var in self.stat_vars.items():
            card = tk.Frame(frame, bg=BG_CARD,
                            highlightthickness=1,
                            highlightbackground=BORDER)
            card.pack(side="left", expand=True,
                      fill="x", padx=4)
            tk.Label(card, textvariable=var,
                     bg=BG_CARD, fg=colors[label],
                     font=("Courier", 16, "bold")
                     ).pack(pady=(8, 2))
            tk.Label(card, text=label,
                     bg=BG_CARD, fg=FG_MUTED,
                     font=("Courier", 8)
                     ).pack(pady=(0, 8))

    # ── Progress bar ─────────────────────────────────────────
    def _build_progress(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(8, 0))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TProgressbar",
                        troughcolor=BG_CARD,
                        background=BTN_BLUE,
                        thickness=8)

        self.progress = ttk.Progressbar(
            frame,
            mode="determinate",
            maximum=100,
            value=0)
        self.progress.pack(fill="x")

        self.progress_label = tk.Label(
            frame,
            text="0%  ·  waiting...",
            bg=BG_DARK, fg=FG_MUTED,
            font=("Courier", 8))
        self.progress_label.pack(anchor="w", pady=2)

    # ── Buttons — packed BEFORE log ──────────────────────────
    def _build_buttons(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(10, 6))

        # Start
        self.start_btn = tk.Button(
            frame,
            text="▶  Start Hybrid Attack",
            bg=BTN_BLUE, fg="#e0f0ff",
            font=("Courier", 12, "bold"),
            relief="flat",
            highlightthickness=1,
            highlightbackground=BTN_BLUE,
            activebackground="#1a6fbf",
            activeforeground="#ffffff",
            cursor="hand2",
            command=self._start)
        self.start_btn.pack(
            side="left", expand=True,
            fill="x", padx=(0, 6), ipady=10)

        # Pause
        self.pause_btn = tk.Button(
            frame,
            text="Pause",
            bg=BG_DARK, fg=FG_AMBER,
            font=("Courier", 11),
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
            activebackground=BG_CARD,
            activeforeground=FG_AMBER,
            cursor="hand2",
            command=self._toggle_pause)
        self.pause_btn.pack(
            side="left", expand=True,
            fill="x", padx=3, ipady=10)

        # Export
        tk.Button(frame,
                  text="Export CSV",
                  bg=BG_DARK, fg=FG_PRIMARY,
                  font=("Courier", 11),
                  relief="flat",
                  highlightthickness=1,
                  highlightbackground=BORDER,
                  activebackground=BG_CARD,
                  activeforeground=FG_BLUE,
                  cursor="hand2",
                  command=self._export_csv
                  ).pack(side="left", expand=True,
                         fill="x", padx=3, ipady=10)

        # Clear
        tk.Button(frame,
                  text="Clear",
                  bg=BG_DARK, fg=FG_PRIMARY,
                  font=("Courier", 11),
                  relief="flat",
                  highlightthickness=1,
                  highlightbackground=BORDER,
                  activebackground=BG_CARD,
                  activeforeground=FG_PRIMARY,
                  cursor="hand2",
                  command=self._clear
                  ).pack(side="left", expand=True,
                         fill="x", padx=(3, 0), ipady=10)

    # ── Status bar — side=bottom before log ──────────────────
    def _build_statusbar(self):
        bar = tk.Frame(self, bg=BG_CARD, height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        tk.Label(bar, text="●",
                 bg=BG_CARD, fg=FG_GREEN,
                 font=("Courier", 10)).pack(
                 side="left", padx=(12, 4))

        self.status_var = tk.StringVar(
            value="Ready · Select files and click "
                  "Start Hybrid Attack")
        tk.Label(bar, textvariable=self.status_var,
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 9)).pack(side="left")

        tk.Label(bar,
                 text="Rainbow → Dict → Mutate → Brute",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 9)).pack(
                 side="right", padx=12)

    def _set_status(self, msg):
        self.status_var.set(msg)

    # ── Live log — packed LAST fills remaining space ──────────
    def _build_log(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="both", expand=True,
                   padx=16, pady=(6, 4))

        tk.Label(frame, text="LIVE ATTACK LOG",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(
                 anchor="w", pady=(0, 4))

        log_frame = tk.Frame(frame, bg=BG_CARD,
                              highlightthickness=1,
                              highlightbackground=BORDER)
        log_frame.pack(fill="both", expand=True)

        self.log_box = tk.Text(
            log_frame,
            bg=BG_CARD, fg=FG_PRIMARY,
            font=("Courier", 10),
            relief="flat",
            state="disabled",
            wrap="word",
            padx=10, pady=8)

        sb = tk.Scrollbar(log_frame,
                          command=self.log_box.yview,
                          bg=BG_CARD,
                          troughcolor=BG_DARK)
        self.log_box.configure(yscrollcommand=sb.set)
        self.log_box.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.log_box.tag_configure("rainbow", foreground=FG_GREEN)
        self.log_box.tag_configure("dict",    foreground=FG_BLUE)
        self.log_box.tag_configure("mutate",  foreground=FG_AMBER)
        self.log_box.tag_configure("brute",   foreground=FG_RED)
        self.log_box.tag_configure("found",   foreground=FG_GREEN)
        self.log_box.tag_configure("info",    foreground=FG_MUTED)

    def _log(self, msg, tag="info"):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n", tag)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # ── Pause / resume ───────────────────────────────────────
    def _toggle_pause(self):
        if not self.running:
            return
        self.paused = not self.paused
        if self.paused:
            self.pause_btn.configure(text="Resume",
                                      fg=FG_GREEN)
            self._set_status(
                "Paused · Click Resume to continue")
        else:
            self.pause_btn.configure(text="Pause",
                                      fg=FG_AMBER)
            self._set_status("Resumed · Attack running...")

    # ── Start ────────────────────────────────────────────────
    def _start(self):
        if self.running:
            return
        hf = self.hash_file.get().strip()
        wf = self.wordlist_file.get().strip()
        if not hf or not wf:
            messagebox.showwarning(
                "Input Error",
                "Please select both hash and wordlist files.")
            return
        self._clear()
        self.running = True
        self.paused  = False
        self.start_btn.configure(
            state="disabled", text="⏳  Running...")
        threading.Thread(
            target=self._attack_worker,
            args=(hf, wf),
            daemon=True).start()

    # ── Core hybrid worker ───────────────────────────────────
    def _attack_worker(self, hash_file, wordlist_file):
        start_time = time.time()

        try:
            with open(hash_file, "r", encoding="latin-1") as f:
                all_hashes = [h.strip() for h in f if h.strip()]
            with open(wordlist_file, "r", encoding="latin-1") as f:
                wordlist = [w.strip() for w in f if w.strip()]
        except Exception as e:
            messagebox.showerror("File Error", str(e))
            self.running = False
            return

        total         = len(all_hashes)
        remaining     = set(all_hashes)
        cracked_count = 0

        self.after(0, lambda: self.stat_vars[
            "Total"].set(str(total)))
        self.after(0, lambda: self.stat_vars[
            "Remaining"].set(str(total)))

        def elapsed():
            return round(time.time() - start_time, 2)

        def record(hash_val, plaintext, method,
                   stage_name, tag):
            nonlocal cracked_count
            cracked_count += 1
            remaining.discard(hash_val)
            self.results.append({
                "idx":    cracked_count,
                "hash":   hash_val[:36] + "..."
                          if len(hash_val) > 36
                          else hash_val,
                "plain":  plaintext,
                "method": method,
                "stage":  stage_name,
                "status": "Cracked",
                "tag":    tag,
            })
            self.after(0, self._update_stats,
                           cracked_count,
                           len(remaining),
                           stage_name, elapsed())

        def wait_if_paused():
            while self.paused and self.running:
                time.sleep(0.1)

        def upd_prog(done, total_cnt,
                     stage_num, stage_name):
            pct = int((done / total_cnt) * 100) \
                  if total_cnt else 0
            self.after(0, self._update_progress,
                           pct, stage_num, stage_name,
                           cracked_count, total, elapsed())

        # ── Stage 1: Rainbow ─────────────────────────────────
        self.after(0, self._set_stage,
                       "Rainbow Table", "running")
        self.after(0, self._log,
                       "=== Stage 1: Rainbow Table ===",
                       "info")
        self.after(0,
                       self.stat_vars["Current"].set,
                       "Stage 1")
        self.after(0, self._set_status,
                       "Stage 1/4 — Rainbow table running")

        to_remove = set()
        for h in list(remaining):
            wait_if_paused()
            if not self.running:
                break
            result = rainbow.lookup(h)
            if result is not None:
                self.after(0, self._log,
                    f"[RAINBOW] {h[:24]}...  →  "
                    f"'{result}'", "rainbow")
                record(h, result, "Rainbow",
                       "Rainbow", "rainbow")
                to_remove.add(h)

        remaining -= to_remove
        self.after(0, self._set_stage,
                       "Rainbow Table", "done")
        if not remaining or not self.running:
            self.after(0, self._done)
            return

        # ── Stage 2: Dictionary ──────────────────────────────
        self.after(0, self._set_stage,
                       "Dictionary", "running")
        self.after(0, self._log,
                       "=== Stage 2: Dictionary Attack ===",
                       "info")
        self.after(0,
                       self.stat_vars["Current"].set,
                       "Stage 2")
        self.after(0, self._set_status,
                       "Stage 2/4 — Dictionary attack running")

        to_remove = set()
        for i, word in enumerate(wordlist):
            wait_if_paused()
            if not self.running:
                break
            for h in list(remaining):
                for algo, fn in ALGORITHMS.items():
                    try:
                        if fn(word) == h.lower():
                            self.after(0, self._log,
                                f"[DICT/{algo.upper()}] "
                                f"{h[:20]}...  →  "
                                f"'{word}'", "dict")
                            record(h, word, algo.upper(),
                                   "Dictionary", "dict")
                            to_remove.add(h)
                            break
                    except Exception:
                        pass
            remaining -= to_remove
            to_remove.clear()
            if i % 200 == 0:
                upd_prog(i, len(wordlist), 2, "Dict")
            if not remaining:
                break

        self.after(0, self._set_stage,
                       "Dictionary", "done")
        if not remaining or not self.running:
            self.after(0, self._done)
            return

        # ── Stage 3: Mutation ────────────────────────────────
        self.after(0, self._set_stage,
                       "Mutation Engine", "running")
        self.after(0, self._log,
                       "=== Stage 3: Mutation Engine ===",
                       "info")
        self.after(0,
                       self.stat_vars["Current"].set,
                       "Stage 3")
        self.after(0, self._set_status,
                       "Stage 3/4 — Mutation engine running")

        active_rules = [r for r, v
                        in self.mutation_rules.items()
                        if v.get()]
        to_remove = set()

        for i, word in enumerate(wordlist):
            wait_if_paused()
            if not self.running:
                break
            for variant in mutate(word, active_rules):
                for h in list(remaining):
                    for algo, fn in ALGORITHMS.items():
                        try:
                            if fn(variant) == h.lower():
                                self.after(0, self._log,
                                    f"[MUTATE] '{variant}'"
                                    f"  →  {h[:20]}...",
                                    "mutate")
                                record(h, variant,
                                       algo.upper(),
                                       "Mutation", "mutate")
                                to_remove.add(h)
                                break
                        except Exception:
                            pass
                remaining -= to_remove
                to_remove.clear()
            if i % 100 == 0:
                upd_prog(i, len(wordlist), 3, "Mutate")
            if not remaining:
                break

        self.after(0, self._set_stage,
                       "Mutation Engine", "done")
        if not remaining or not self.running:
            self.after(0, self._done)
            return

        # ── Stage 4: Brute force ─────────────────────────────
        self.after(0, self._set_stage,
                       "Brute Force", "running")
        self.after(0, self._log,
                       "=== Stage 4: Brute Force ===",
                       "info")
        self.after(0,
                       self.stat_vars["Current"].set,
                       "Stage 4")
        self.after(0, self._set_status,
                       "Stage 4/4 — Brute force running")

        charset   = self.charset_var.get() \
                    or string.ascii_lowercase
        min_l     = self.min_len.get()
        max_l     = self.max_len.get()
        to_remove = set()
        count     = 0

        for length in range(min_l, max_l + 1):
            if not remaining or not self.running:
                break
            self.after(0, self._log,
                f"[BRUTE] Trying length {length}...",
                "info")
            for combo in itertools.product(
                    charset, repeat=length):
                wait_if_paused()
                if not self.running:
                    break
                word = "".join(combo)
                for h in list(remaining):
                    for algo, fn in ALGORITHMS.items():
                        try:
                            if fn(word) == h.lower():
                                self.after(0, self._log,
                                    f"[BRUTE/{algo.upper()}]"
                                    f" '{word}'  →  "
                                    f"{h[:20]}...", "brute")
                                record(h, word, algo.upper(),
                                       "Brute Force", "brute")
                                to_remove.add(h)
                                break
                        except Exception:
                            pass
                remaining -= to_remove
                to_remove.clear()
                count += 1
                if count % 5000 == 0:
                    self.after(0, self._log,
                        f"[BRUTE] {count} combos tried...",
                        "info")
                if not remaining:
                    break

        self.after(0, self._set_stage,
                       "Brute Force", "done")

        for h in remaining:
            self.results.append({
                "idx":    len(self.results) + 1,
                "hash":   h[:36] + "..."
                          if len(h) > 36 else h,
                "plain":  "—",
                "method": "—",
                "stage":  "All stages",
                "status": "Not Found",
                "tag":    "notfound",
            })

        self.after(0, self._done)

    # ── UI update helpers ────────────────────────────────────
    def _update_stats(self, cracked, remaining,
                      stage, elapsed_t):
        self.stat_vars["Cracked"].set(str(cracked))
        self.stat_vars["Remaining"].set(str(remaining))
        self.stat_vars["Elapsed"].set(f"{elapsed_t}s")

    def _update_progress(self, pct, stage_num,
                         stage_name, cracked,
                         total, elapsed_t):
        self.progress["value"] = pct
        self.progress_label.configure(
            text=f"{pct}%  ·  Stage {stage_num}/4  ·  "
                 f"{cracked}/{total} cracked  ·  "
                 f"{elapsed_t}s")
        self.stat_vars["Elapsed"].set(f"{elapsed_t}s")
        self._set_status(
            f"Stage {stage_num}/4 — {stage_name} running  "
            f"·  {cracked} cracked  ·  {elapsed_t}s")

    def _done(self):
        self.running = False
        self.start_btn.configure(
            state="normal",
            text="▶  Start Hybrid Attack")
        self.pause_btn.configure(
            text="Pause", fg=FG_AMBER)
        total   = len(self.results)
        cracked = sum(1 for r in self.results
                      if r["status"] == "Cracked")
        self.progress["value"] = 100
        self.progress_label.configure(
            text=f"100%  ·  All stages complete  ·  "
                 f"{cracked}/{total} cracked")
        self._set_status(
            f"Done  ·  {cracked}/{total} cracked  ·  "
            f"{self.stat_vars['Elapsed'].get()}")
        self._log(
            f"=== Done: {cracked}/{total} cracked ===",
            "found")
        self.stat_vars["Current"].set("Done")
        
        from core.session_logger import log_session
        cracked = sum(
            1 for r in self.results
            if r["status"] == "Cracked")
        log_session("Hybrid", {
            "cracked":  cracked,
            "total":    len(self.results),
            "elapsed":  self.stat_vars[
                "Elapsed"].get(),
            "summary":
                f"{cracked}/{len(self.results)}"
                f" cracked · 4 stages",
        })

    # ── Export CSV ───────────────────────────────────────────
    def _export_csv(self):
        if not self.results:
            messagebox.showwarning(
                "No Data", "No results to export yet.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="hybrid_results.csv")
        if not path:
            return
        with open(path, "w", newline="",
                  encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "idx", "hash", "plain", "method",
                "stage", "status", "tag"])
            writer.writeheader()
            writer.writerows(self.results)
        messagebox.showinfo(
            "Exported", f"Results saved to:\n{path}")

    # ── Clear ────────────────────────────────────────────────
    def _clear(self):
        self.results.clear()
        for k, v in self.stat_vars.items():
            v.set("0.0s" if k == "Elapsed" else
                  "—"    if k == "Current"  else "0")
        self.progress["value"] = 0
        self.progress_label.configure(
            text="0%  ·  waiting...")
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        for key, _, _ in STAGES:
            self._set_stage(key, "waiting")
        self._set_status("Cleared · Ready")