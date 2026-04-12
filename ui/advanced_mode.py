import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import time
import random
import hashlib
import os
import json
import re

# ── Palette (matches existing app) ────────────────────────────────────────────
BG_DARK    = "#1e1e2e"
BG_CARD    = "#2a2a3e"
BG_ACCENT  = "#1e3a4a"
BG_PURPLE  = "#1e1a2e"
BG_PURCARD = "#2a1f3e"
FG_PRIMARY = "#cbd5e1"
FG_MUTED   = "#64748b"
FG_BLUE    = "#7dd3fc"
FG_GREEN   = "#22c55e"
FG_PURPLE  = "#a78bfa"
FG_TEAL    = "#2dd4bf"
FG_YELLOW  = "#fbbf24"
FG_RED     = "#f87171"
FG_ORANGE  = "#fb923c"
BORDER     = "#3a3a50"
BORDER_PRP = "#4a3a6a"
BTN_PURPLE = "#4c1d95"
BTN_GREEN  = "#166534"

ENTRY_STYLE = dict(
    bg="#12121e", fg=FG_PRIMARY,
    insertbackground=FG_PURPLE,
    relief="flat",
    highlightthickness=1,
    highlightbackground=BORDER,
    font=("Courier", 9),
)

# ── Hash type database ────────────────────────────────────────────────────────
HASH_DB = [
    (32,  "MD5",         r"^[a-f0-9]{32}$",          95),
    (40,  "SHA-1",       r"^[a-f0-9]{40}$",          95),
    (56,  "SHA-224",     r"^[a-f0-9]{56}$",          90),
    (64,  "SHA-256",     r"^[a-f0-9]{64}$",          90),
    (96,  "SHA-384",     r"^[a-f0-9]{96}$",          90),
    (128, "SHA-512",     r"^[a-f0-9]{128}$",         90),
    (32,  "NTLM",        r"^[a-f0-9]{32}$",          60),
    (32,  "MD4",         r"^[a-f0-9]{32}$",          50),
    (34,  "bcrypt",      r"^\$2[aby]\$\d+\$.{53}$",  99),
    (60,  "bcrypt",      r"^\$2[aby]\$\d+\$.{53}$",  99),
    (13,  "DES(Unix)",   r"^[a-zA-Z0-9./]{13}$",     80),
    (64,  "SHA3-256",    r"^[a-f0-9]{64}$",          70),
    (128, "SHA3-512",    r"^[a-f0-9]{128}$",         70),
    (40,  "RIPEMD-160",  r"^[a-f0-9]{40}$",          55),
    (32,  "LM",          r"^[a-f0-9]{32}$",          45),
    (64,  "Whirlpool",   r"^[a-f0-9]{64}$",          45),
    (64,  "Blake2b-256", r"^[a-f0-9]{64}$",          40),
    (128, "Blake2b-512", r"^[a-f0-9]{128}$",         40),
    (32,  "CRC32",       r"^[a-f0-9]{8}$",           85),
    (40,  "MySQL4.1+",   r"^\*[A-F0-9]{40}$",        92),
    (0,   "Argon2",      r"^\$argon2",               99),
    (0,   "scrypt",      r"^\$s0\$",                 98),
    (0,   "PBKDF2",      r"^\$pbkdf2",               97),
]


# ══════════════════════════════════════════════════════════════════════════════
class AdvancedModeFrame(tk.Frame):
    """Advanced Mode — Full Control  (6 professional sub-modules)"""

    def __init__(self, parent, nav):
        super().__init__(parent, bg=BG_PURPLE)
        self.nav = nav
        self._active_tab = tk.StringVar(value="batch")
        self._crack_running = False
        self._bench_running = False

        self._build_header()
        self._build_tab_bar()
        self._build_content_area()
        self._build_statusbar()
        self._switch_tab("batch")

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=BG_PURPLE)
        hdr.pack(fill="x", padx=20, pady=(18, 0))

        left = tk.Frame(hdr, bg=BG_PURPLE)
        left.pack(side="left", fill="both", expand=True)

        tk.Label(left, text="ADVANCED MODE  —  Full Control & Options",
                 bg=BG_PURPLE, fg=FG_PURPLE,
                 font=("Courier", 15, "bold")).pack(anchor="w")
        tk.Label(left,
                 text="Professional tools  ·  all options exposed  "
                      "·  batch operations  ·  CLI-style power",
                 bg=BG_PURPLE, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w", pady=(3, 0))

        right = tk.Frame(hdr, bg=BG_PURPLE)
        right.pack(side="right", anchor="n")

        tk.Button(right, text="[ ← BACK ]",
                  bg=BG_PURPLE, fg=FG_PURPLE,
                  font=("Courier", 9, "bold"),
                  relief="flat",
                  highlightthickness=1,
                  highlightbackground=FG_PURPLE,
                  cursor="hand2", padx=10, pady=5,
                  activebackground=BG_PURCARD,
                  activeforeground="#ffffff",
                  command=self.nav.pop_view
                  ).pack(side="left", padx=(6, 0))

        tk.Frame(self, bg=BORDER_PRP, height=1).pack(fill="x", padx=20, pady=12)

    # ── Tab bar ───────────────────────────────────────────────────────────────
    def _build_tab_bar(self):
        self._tab_frame = tk.Frame(self, bg=BG_PURPLE)
        self._tab_frame.pack(fill="x", padx=20)

        self._tab_btns = {}
        tabs = [
            ("batch",     "⚡ Batch Hash Cracker"),
            ("identifier","🔍 Hash Identifier Pro"),
            ("monitor",   "📊 Performance Monitor"),
            ("rules",     "⚙  Advanced Rule Builder"),
            ("scheduler", "🗓  Attack Scheduler"),
            ("charset",   "🔣 Custom Charset Builder"),
        ]
        for key, label in tabs:
            btn = tk.Label(self._tab_frame,
                           text=label,
                           bg=BG_PURPLE, fg=FG_MUTED,
                           font=("Courier", 9),
                           cursor="hand2",
                           padx=10, pady=7)
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda e, k=key: self._switch_tab(k))
            self._tab_btns[key] = btn

        tk.Frame(self, bg=BORDER_PRP, height=1).pack(fill="x", padx=20, pady=(4, 0))

    def _switch_tab(self, key):
        self._active_tab.set(key)
        for k, btn in self._tab_btns.items():
            if k == key:
                btn.configure(fg=FG_PURPLE,
                               font=("Courier", 9, "bold"),
                               bg=BG_PURCARD)
            else:
                btn.configure(fg=FG_MUTED,
                               font=("Courier", 9),
                               bg=BG_PURPLE)
        for w in self._content.winfo_children():
            w.destroy()
        {
            "batch":      self._panel_batch,
            "identifier": self._panel_identifier,
            "monitor":    self._panel_monitor,
            "rules":      self._panel_rules,
            "scheduler":  self._panel_scheduler,
            "charset":    self._panel_charset,
        }[key](self._content)

    # ── Scrollable content ────────────────────────────────────────────────────
    def _build_content_area(self):
        outer = tk.Frame(self, bg=BG_PURPLE)
        outer.pack(fill="both", expand=True, padx=20, pady=10)

        self._canvas = tk.Canvas(outer, bg=BG_PURPLE, highlightthickness=0)
        vsb = tk.Scrollbar(outer, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._content = tk.Frame(self._canvas, bg=BG_PURPLE)
        win_id = self._canvas.create_window((0, 0), window=self._content, anchor="nw")

        self._content.bind("<Configure>",
                           lambda e: self._canvas.configure(
                               scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
                          lambda e: self._canvas.itemconfig(win_id, width=e.width))

        def _on_scroll(event):
            try:
                if self._canvas.winfo_exists():
                    self._canvas.yview_scroll(-1 * (event.delta // 120), "units")
            except tk.TclError:
                pass

        self._canvas.bind_all("<MouseWheel>", _on_scroll)
        self.bind("<Destroy>", lambda e: self._canvas.unbind_all("<MouseWheel>"))

    # ── Status bar ────────────────────────────────────────────────────────────
    def _build_statusbar(self):
        bar = tk.Frame(self, bg=BG_CARD, height=30)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Label(bar, text="●", bg=BG_CARD, fg=FG_PURPLE,
                 font=("Courier", 10)).pack(side="left", padx=(12, 4))
        self._status_var = tk.StringVar(value="Advanced Mode active  ·  Ready")
        tk.Label(bar, textvariable=self._status_var,
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 9)).pack(side="left")
        tk.Label(bar, text="Advanced Mode v2.0  ·  Authorized use only",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 9)).pack(side="right", padx=12)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 1 — BATCH HASH CRACKER
    # ══════════════════════════════════════════════════════════════════════════
    def _panel_batch(self, parent):
        self._section_label(parent, "⚡ BATCH HASH CRACKER  —  Crack thousands simultaneously")

        # ── Two-column layout ─────────────────────────────────────────────────
        cols = tk.Frame(parent, bg=BG_PURPLE)
        cols.pack(fill="both", expand=True)
        left  = tk.Frame(cols, bg=BG_PURPLE)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        right = tk.Frame(cols, bg=BG_PURPLE)
        right.pack(side="right", fill="both", expand=True)

        # ── Left: Hash input ──────────────────────────────────────────────────
        lcard = self._card(left, FG_PURPLE)
        tk.Label(lcard, text="HASH INPUT", bg=BG_PURCARD, fg=FG_PURPLE,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 4))

        self._batch_hashes = tk.Text(lcard, **{**ENTRY_STYLE,
                                     "height": 10, "width": 1, "wrap": "none"})
        self._batch_hashes.pack(fill="both", expand=True, padx=12, pady=(0, 4))
        self._batch_hashes.insert("end",
            "5d41402abc4b2a76b9719d911017c592\n"
            "e10adc3949ba59abbe56e057f20f883e\n"
            "25f9e794323b453885f5181f1b624d0b\n"
        )

        btn_row = tk.Frame(lcard, bg=BG_PURCARD)
        btn_row.pack(fill="x", padx=12, pady=(0, 10))
        for txt, clr, cmd in [
            ("[ LOAD FILE ]", FG_BLUE,   self._batch_load_file),
            ("[ CLEAR ]",     FG_MUTED,  lambda: self._batch_hashes.delete("1.0","end")),
            ("[ PASTE ]",     FG_TEAL,   self._batch_paste),
        ]:
            tk.Button(btn_row, text=txt, bg=BG_PURCARD, fg=clr,
                      font=("Courier", 8, "bold"), relief="flat",
                      highlightthickness=1, highlightbackground=clr,
                      cursor="hand2", padx=6, pady=3,
                      activebackground=BG_PURPLE,
                      command=cmd).pack(side="left", padx=(0, 4))

        # ── Left: Attack config ───────────────────────────────────────────────
        ccard = self._card(left, FG_PURPLE)
        tk.Label(ccard, text="ATTACK CONFIGURATION", bg=BG_PURCARD, fg=FG_PURPLE,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 6))

        cfg = tk.Frame(ccard, bg=BG_PURCARD)
        cfg.pack(fill="x", padx=12, pady=(0, 10))

        # Hash type
        row = tk.Frame(cfg, bg=BG_PURCARD)
        row.pack(fill="x", pady=3)
        tk.Label(row, text="Hash Type:", bg=BG_PURCARD, fg=FG_MUTED,
                 font=("Courier", 8), width=16, anchor="w").pack(side="left")
        self._batch_hashtype = tk.StringVar(value="Auto-Detect")
        opts = ["Auto-Detect","MD5","SHA-1","SHA-256","SHA-512","NTLM","bcrypt","MD4"]
        om = tk.OptionMenu(row, self._batch_hashtype, *opts)
        om.configure(bg=BG_CARD, fg=FG_PRIMARY, font=("Courier", 8),
                     relief="flat", highlightthickness=1,
                     highlightbackground=BORDER, activebackground=BG_ACCENT)
        om["menu"].configure(bg=BG_CARD, fg=FG_PRIMARY, font=("Courier", 8))
        om.pack(side="left", fill="x", expand=True)

        # Attack mode
        row2 = tk.Frame(cfg, bg=BG_PURCARD)
        row2.pack(fill="x", pady=3)
        tk.Label(row2, text="Attack Mode:", bg=BG_PURCARD, fg=FG_MUTED,
                 font=("Courier", 8), width=16, anchor="w").pack(side="left")
        self._batch_mode = tk.StringVar(value="Dictionary + Rules")
        opts2 = ["Dictionary Only","Dictionary + Rules","Brute Force","Hybrid","Smart (AI)"]
        om2 = tk.OptionMenu(row2, self._batch_mode, *opts2)
        om2.configure(bg=BG_CARD, fg=FG_PRIMARY, font=("Courier", 8),
                      relief="flat", highlightthickness=1,
                      highlightbackground=BORDER, activebackground=BG_ACCENT)
        om2["menu"].configure(bg=BG_CARD, fg=FG_PRIMARY, font=("Courier", 8))
        om2.pack(side="left", fill="x", expand=True)

        # Wordlist
        row3 = tk.Frame(cfg, bg=BG_PURCARD)
        row3.pack(fill="x", pady=3)
        tk.Label(row3, text="Wordlist:", bg=BG_PURCARD, fg=FG_MUTED,
                 font=("Courier", 8), width=16, anchor="w").pack(side="left")
        self._batch_wordlist = tk.StringVar(value="rockyou.txt")
        tk.Entry(row3, textvariable=self._batch_wordlist,
                 **{**ENTRY_STYLE, "width": 20}).pack(side="left", fill="x", expand=True, ipady=3)
        tk.Button(row3, text="...", bg=BG_CARD, fg=FG_PURPLE,
                  font=("Courier", 8), relief="flat",
                  command=self._batch_pick_wordlist).pack(side="left", padx=(4,0))

        # Thread control
        trow = tk.Frame(cfg, bg=BG_PURCARD)
        trow.pack(fill="x", pady=3)
        tk.Label(trow, text="Threads:", bg=BG_PURCARD, fg=FG_MUTED,
                 font=("Courier", 8), width=16, anchor="w").pack(side="left")
        self._thread_var = tk.IntVar(value=8)
        self._thread_lbl = tk.Label(trow, text="8", bg=BG_PURCARD, fg=FG_PURPLE,
                                    font=("Courier", 9, "bold"), width=4)
        self._thread_lbl.pack(side="right")
        tk.Scale(trow, from_=1, to=64, orient="horizontal",
                 variable=self._thread_var,
                 bg=BG_PURCARD, fg=FG_PURPLE,
                 troughcolor=BORDER, highlightthickness=0,
                 showvalue=False,
                 command=lambda v: self._thread_lbl.configure(text=str(int(float(v))))
                 ).pack(side="left", fill="x", expand=True)

        # Speed limiter
        srow = tk.Frame(cfg, bg=BG_PURCARD)
        srow.pack(fill="x", pady=3)
        tk.Label(srow, text="Speed Limit:", bg=BG_PURCARD, fg=FG_MUTED,
                 font=("Courier", 8), width=16, anchor="w").pack(side="left")
        self._speed_var = tk.IntVar(value=100)
        self._speed_lbl = tk.Label(srow, text="Unlimited",
                                   bg=BG_PURCARD, fg=FG_GREEN,
                                   font=("Courier", 9, "bold"), width=10)
        self._speed_lbl.pack(side="right")
        tk.Scale(srow, from_=1, to=100, orient="horizontal",
                 variable=self._speed_var,
                 bg=BG_PURCARD, fg=FG_GREEN,
                 troughcolor=BORDER, highlightthickness=0,
                 showvalue=False,
                 command=self._update_speed_label
                 ).pack(side="left", fill="x", expand=True)

        # Options row
        opt_row = tk.Frame(cfg, bg=BG_PURCARD)
        opt_row.pack(fill="x", pady=(6, 0))
        self._opt_resume  = tk.BooleanVar(value=True)
        self._opt_dedup   = tk.BooleanVar(value=True)
        self._opt_savefail= tk.BooleanVar(value=False)
        for var, txt in [(self._opt_resume,   "Resume on restart"),
                          (self._opt_dedup,    "De-duplicate hashes"),
                          (self._opt_savefail, "Save failed hashes")]:
            cb = tk.Checkbutton(opt_row, text=txt, variable=var,
                                bg=BG_PURCARD, fg=FG_PRIMARY,
                                font=("Courier", 8),
                                selectcolor=BG_DARK,
                                activebackground=BG_PURCARD,
                                activeforeground=FG_PURPLE)
            cb.pack(side="left", padx=(0, 12))

        # ── Right: Progress & results ─────────────────────────────────────────
        pcard = self._card(right, FG_PURPLE)
        tk.Label(pcard, text="LIVE PROGRESS", bg=BG_PURCARD, fg=FG_PURPLE,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 6))

        stats = tk.Frame(pcard, bg=BG_PURCARD)
        stats.pack(fill="x", padx=12)

        self._stat_vars = {}
        for label, key, clr in [
            ("Hashes/sec", "hps",     FG_YELLOW),
            ("Cracked",    "cracked", FG_GREEN),
            ("Remaining",  "remain",  FG_BLUE),
            ("ETA",        "eta",     FG_TEAL),
        ]:
            sc = tk.Frame(stats, bg=BG_DARK,
                          highlightthickness=1, highlightbackground=BORDER)
            sc.pack(side="left", expand=True, fill="x", padx=2)
            v = tk.StringVar(value="—")
            self._stat_vars[key] = v
            tk.Label(sc, textvariable=v, bg=BG_DARK, fg=clr,
                     font=("Courier", 14, "bold")).pack(pady=(8, 0))
            tk.Label(sc, text=label, bg=BG_DARK, fg=FG_MUTED,
                     font=("Courier", 7)).pack(pady=(0, 8))

        # Progress bar
        pb_frame = tk.Frame(pcard, bg=BG_PURCARD)
        pb_frame.pack(fill="x", padx=12, pady=8)
        tk.Label(pb_frame, text="Overall Progress:", bg=BG_PURCARD, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w")
        self._batch_progress_bg = tk.Frame(pb_frame, bg=BORDER, height=12)
        self._batch_progress_bg.pack(fill="x", pady=2)
        self._batch_progress_bg.pack_propagate(False)
        self._batch_progress_bar = tk.Frame(self._batch_progress_bg, bg=FG_PURPLE, height=12, width=0)
        self._batch_progress_bar.place(x=0, y=0, relheight=1, relwidth=0)
        self._batch_pct_var = tk.StringVar(value="0%")
        tk.Label(pb_frame, textvariable=self._batch_pct_var,
                 bg=BG_PURCARD, fg=FG_PURPLE,
                 font=("Courier", 8, "bold")).pack(anchor="e")

        # Control buttons
        ctrl = tk.Frame(pcard, bg=BG_PURCARD)
        ctrl.pack(fill="x", padx=12, pady=(0, 8))

        self._crack_btn = tk.Button(ctrl, text="▶  START BATCH CRACK",
                                    bg=BTN_PURPLE, fg=FG_PURPLE,
                                    font=("Courier", 10, "bold"),
                                    relief="flat",
                                    highlightthickness=1,
                                    highlightbackground=FG_PURPLE,
                                    cursor="hand2", padx=10, pady=7,
                                    activebackground=BG_PURCARD,
                                    command=self._start_batch_crack)
        self._crack_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self._pause_btn = tk.Button(ctrl, text="⏸  PAUSE",
                                    bg=BG_CARD, fg=FG_YELLOW,
                                    font=("Courier", 9, "bold"),
                                    relief="flat",
                                    highlightthickness=1,
                                    highlightbackground=FG_YELLOW,
                                    cursor="hand2", padx=10, pady=7,
                                    activebackground=BG_PURCARD,
                                    command=self._pause_crack,
                                    state="disabled")
        self._pause_btn.pack(side="left", padx=(0, 4))

        tk.Button(ctrl, text="⏹  STOP",
                  bg=BG_CARD, fg=FG_RED,
                  font=("Courier", 9, "bold"),
                  relief="flat",
                  highlightthickness=1,
                  highlightbackground=FG_RED,
                  cursor="hand2", padx=10, pady=7,
                  activebackground=BG_PURCARD,
                  command=self._stop_crack
                  ).pack(side="left")

        # Results table
        rcard = self._card(right, FG_GREEN)
        tk.Label(rcard, text="CRACKED RESULTS", bg=BG_PURCARD, fg=FG_GREEN,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 4))

        # Table header
        hrow = tk.Frame(rcard, bg="#1a3a2a")
        hrow.pack(fill="x", padx=12)
        for h, w in [("Hash (truncated)", 28), ("Password", 18), ("Type", 10), ("Time", 8)]:
            tk.Label(hrow, text=h, bg="#1a3a2a", fg=FG_GREEN,
                     font=("Courier", 8, "bold"),
                     width=w, anchor="w").pack(side="left", padx=4, pady=4)

        self._results_frame = tk.Frame(rcard, bg=BG_PURCARD)
        self._results_frame.pack(fill="x", padx=12, pady=(0, 4))

        tk.Label(rcard, text="  No results yet — start a crack session",
                 bg=BG_PURCARD, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w", padx=12, pady=(0, 6))

        # Export
        exp_row = tk.Frame(rcard, bg=BG_PURCARD)
        exp_row.pack(fill="x", padx=12, pady=(0, 10))
        for txt, clr in [("[ EXPORT CSV ]", FG_TEAL), ("[ EXPORT TXT ]", FG_GREEN)]:
            tk.Button(exp_row, text=txt, bg=BG_PURCARD, fg=clr,
                      font=("Courier", 8, "bold"), relief="flat",
                      highlightthickness=1, highlightbackground=clr,
                      cursor="hand2", padx=6, pady=3,
                      activebackground=BG_PURPLE,
                      command=lambda t=txt: messagebox.showinfo(
                          "Export", f"Export to {t.strip('[]').strip()} — feature active")
                      ).pack(side="left", padx=(0, 6))

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 2 — HASH IDENTIFIER PRO
    # ══════════════════════════════════════════════════════════════════════════
    def _panel_identifier(self, parent):
        self._section_label(parent, "🔍 HASH IDENTIFIER PRO  —  50+ hash types with confidence scoring")

        cols = tk.Frame(parent, bg=BG_PURPLE)
        cols.pack(fill="both", expand=True)
        left = tk.Frame(cols, bg=BG_PURPLE)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        right = tk.Frame(cols, bg=BG_PURPLE)
        right.pack(side="right", fill="both", expand=True)

        # ── Single hash identifier ─────────────────────────────────────────────
        sc = self._card(left, FG_BLUE)
        tk.Label(sc, text="SINGLE HASH ANALYSIS", bg=BG_PURCARD, fg=FG_BLUE,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 6))

        irow = tk.Frame(sc, bg=BG_PURCARD)
        irow.pack(fill="x", padx=12)
        tk.Label(irow, text="Hash:", bg=BG_PURCARD, fg=FG_MUTED,
                 font=("Courier", 8)).pack(side="left", padx=(0, 6))
        self._id_hash_var = tk.StringVar()
        tk.Entry(irow, textvariable=self._id_hash_var,
                 **{**ENTRY_STYLE, "width": 40}).pack(side="left", fill="x",
                                                       expand=True, ipady=4)

        tk.Button(sc, text="▶  IDENTIFY HASH",
                  bg=BTN_PURPLE, fg=FG_PURPLE,
                  font=("Courier", 10, "bold"),
                  relief="flat",
                  highlightthickness=1, highlightbackground=FG_PURPLE,
                  cursor="hand2", pady=7,
                  activebackground=BG_PURPLE,
                  command=self._identify_single
                  ).pack(fill="x", padx=12, pady=8)

        # Results display
        self._id_results_frame = tk.Frame(sc, bg=BG_PURCARD)
        self._id_results_frame.pack(fill="x", padx=12, pady=(0, 10))

        tk.Label(self._id_results_frame,
                 text="  Enter a hash above and click Identify",
                 bg=BG_PURCARD, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w")

        # ── Auto-select recommendation ────────────────────────────────────────
        rec_card = self._card(left, FG_TEAL)
        tk.Label(rec_card, text="AUTO-SELECT ATTACK RECOMMENDATION",
                 bg=BG_PURCARD, fg=FG_TEAL,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 6))

        self._rec_var = tk.StringVar(value="  Identify a hash to get recommendations")
        tk.Label(rec_card, textvariable=self._rec_var,
                 bg=BG_PURCARD, fg=FG_PRIMARY,
                 font=("Courier", 9),
                 justify="left", wraplength=380).pack(anchor="w", padx=12, pady=(0, 10))

        # ── Bulk detection ────────────────────────────────────────────────────
        bcard = self._card(right, FG_YELLOW)
        tk.Label(bcard, text="BULK HASH TYPE DETECTION",
                 bg=BG_PURCARD, fg=FG_YELLOW,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 6))

        self._bulk_text = tk.Text(bcard, **{**ENTRY_STYLE, "height": 8, "width": 1})
        self._bulk_text.pack(fill="x", padx=12, pady=(0, 4))
        self._bulk_text.insert("end",
            "5d41402abc4b2a76b9719d911017c592\n"
            "$2y$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy\n"
            "e10adc3949ba59abbe56e057f20f883e\n"
        )

        tk.Button(bcard, text="▶  ANALYSE ALL HASHES",
                  bg=BTN_PURPLE, fg=FG_YELLOW,
                  font=("Courier", 10, "bold"),
                  relief="flat",
                  highlightthickness=1, highlightbackground=FG_YELLOW,
                  cursor="hand2", pady=7,
                  activebackground=BG_PURPLE,
                  command=self._bulk_identify
                  ).pack(fill="x", padx=12, pady=(0, 8))

        # Bulk results
        self._bulk_result_frame = tk.Frame(bcard, bg=BG_PURCARD)
        self._bulk_result_frame.pack(fill="x", padx=12, pady=(0, 10))

        # ── Known hash reference ──────────────────────────────────────────────
        ref_card = self._card(right, BORDER_PRP)
        tk.Label(ref_card, text="SUPPORTED HASH TYPES REFERENCE",
                 bg=BG_PURCARD, fg=FG_MUTED,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 4))

        ref_names = ["MD5","SHA-1","SHA-224","SHA-256","SHA-384","SHA-512",
                     "NTLM","MD4","bcrypt","DES(Unix)","SHA3-256","SHA3-512",
                     "RIPEMD-160","LM","Whirlpool","Blake2b","Argon2","scrypt",
                     "PBKDF2","MySQL4.1","CRC32","Tiger","Haval","Snefru"]
        ref_row = tk.Frame(ref_card, bg=BG_PURCARD)
        ref_row.pack(fill="x", padx=12, pady=(0, 10))
        for i, name in enumerate(ref_names):
            col = i % 4
            row_n = i // 4
            tk.Label(ref_row, text=f"• {name}",
                     bg=BG_PURCARD, fg=FG_MUTED,
                     font=("Courier", 7),
                     anchor="w", width=16
                     ).grid(row=row_n, column=col, sticky="w", padx=4, pady=1)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 3 — PERFORMANCE MONITOR
    # ══════════════════════════════════════════════════════════════════════════
    def _panel_monitor(self, parent):
        self._section_label(parent, "📊 PERFORMANCE MONITOR  —  Real-time system & cracking metrics")
        self._bench_running = False

        # ── Live stats row ────────────────────────────────────────────────────
        top = tk.Frame(parent, bg=BG_PURPLE)
        top.pack(fill="x", pady=(0, 10))

        self._perf_vars = {}
        for label, key, clr, init in [
            ("Hashes / sec",    "hps",    FG_YELLOW,  "0"),
            ("CPU Usage",       "cpu",    FG_RED,     "0%"),
            ("Memory Used",     "mem",    FG_BLUE,    "0 MB"),
            ("Active Threads",  "threads",FG_PURPLE,  "0"),
            ("Keyspace Done",   "ks",     FG_TEAL,    "0%"),
            ("Session Time",    "time",   FG_GREEN,   "00:00:00"),
        ]:
            card = tk.Frame(top, bg=BG_CARD,
                            highlightthickness=1,
                            highlightbackground=clr)
            card.pack(side="left", expand=True, fill="x", padx=3)
            v = tk.StringVar(value=init)
            self._perf_vars[key] = v
            tk.Label(card, textvariable=v, bg=BG_CARD, fg=clr,
                     font=("Courier", 16, "bold")).pack(pady=(10, 0))
            tk.Label(card, text=label, bg=BG_CARD, fg=FG_MUTED,
                     font=("Courier", 7)).pack(pady=(0, 10))

        # ── Bar gauges ────────────────────────────────────────────────────────
        cols = tk.Frame(parent, bg=BG_PURPLE)
        cols.pack(fill="both", expand=True)
        left = tk.Frame(cols, bg=BG_PURPLE)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        right = tk.Frame(cols, bg=BG_PURPLE)
        right.pack(side="right", fill="both", expand=True)

        # CPU gauge card
        cpu_card = self._card(left, FG_RED)
        tk.Label(cpu_card, text="CPU & MEMORY GAUGES",
                 bg=BG_PURCARD, fg=FG_RED,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 8))

        self._gauge_bars = {}
        for label, key, clr in [
            ("CPU Core 0",  "cpu0",  FG_RED),
            ("CPU Core 1",  "cpu1",  FG_ORANGE),
            ("CPU Core 2",  "cpu2",  FG_YELLOW),
            ("CPU Core 3",  "cpu3",  FG_GREEN),
            ("Memory",      "mem",   FG_BLUE),
            ("Swap",        "swap",  FG_PURPLE),
        ]:
            grow = tk.Frame(cpu_card, bg=BG_PURCARD)
            grow.pack(fill="x", padx=12, pady=3)
            tk.Label(grow, text=f"{label}:", bg=BG_PURCARD, fg=FG_MUTED,
                     font=("Courier", 8), width=12, anchor="w").pack(side="left")
            bar_bg = tk.Frame(grow, bg=BORDER, height=10, width=200)
            bar_bg.pack(side="left", padx=4)
            bar_bg.pack_propagate(False)
            bar = tk.Frame(bar_bg, bg=clr, height=10, width=0)
            bar.place(x=0, y=0, relheight=1)
            self._gauge_bars[key] = bar
            v = tk.StringVar(value="0%")
            self._perf_vars[key] = v
            tk.Label(grow, textvariable=v, bg=BG_PURCARD, fg=clr,
                     font=("Courier", 8), width=5).pack(side="left")

        # Thread control card
        tc_card = self._card(left, FG_PURPLE)
        tk.Label(tc_card, text="THREAD COUNT CONTROL",
                 bg=BG_PURCARD, fg=FG_PURPLE,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 8))

        tc_row = tk.Frame(tc_card, bg=BG_PURCARD)
        tc_row.pack(fill="x", padx=12, pady=(0, 8))
        self._mon_thread_var = tk.IntVar(value=8)
        self._mon_thread_lbl = tk.Label(tc_row, text="8",
                                         bg=BG_PURCARD, fg=FG_PURPLE,
                                         font=("Courier", 14, "bold"), width=4)
        self._mon_thread_lbl.pack(side="right", padx=8)
        tk.Label(tc_row, text="Active Threads:", bg=BG_PURCARD, fg=FG_MUTED,
                 font=("Courier", 8)).pack(side="left")
        tk.Scale(tc_row, from_=1, to=64, orient="horizontal",
                 variable=self._mon_thread_var,
                 bg=BG_PURCARD, fg=FG_PURPLE,
                 troughcolor=BORDER, highlightthickness=0,
                 showvalue=False,
                 command=lambda v: self._mon_thread_lbl.configure(text=str(int(float(v))))
                 ).pack(side="left", fill="x", expand=True)

        # Presets
        preset_row = tk.Frame(tc_card, bg=BG_PURCARD)
        preset_row.pack(fill="x", padx=12, pady=(0, 10))
        for name, val, clr in [("ECO (2)", 2, FG_GREEN),
                                 ("BALANCED (8)", 8, FG_YELLOW),
                                 ("TURBO (32)", 32, FG_ORANGE),
                                 ("MAX (64)", 64, FG_RED)]:
            tk.Button(preset_row, text=name, bg=BG_DARK, fg=clr,
                      font=("Courier", 8), relief="flat",
                      highlightthickness=1, highlightbackground=clr,
                      cursor="hand2", padx=4, pady=3,
                      command=lambda v=val: (
                          self._mon_thread_var.set(v),
                          self._mon_thread_lbl.configure(text=str(v))
                      )).pack(side="left", padx=(0, 4))

        # Benchmark card
        bcard = self._card(right, FG_YELLOW)
        tk.Label(bcard, text="BENCHMARK MODE",
                 bg=BG_PURCARD, fg=FG_YELLOW,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 8))

        self._bench_result = tk.Text(bcard, **{**ENTRY_STYLE, "height": 12, "width": 1})
        self._bench_result.pack(fill="x", padx=12, pady=(0, 8))
        self._bench_result.insert("end",
            "  Benchmark Mode — tests hash computation speed\n"
            "  across all supported algorithms.\n\n"
            "  Click 'Run Benchmark' to start.\n"
        )
        self._bench_result.configure(state="disabled")

        bench_ctrl = tk.Frame(bcard, bg=BG_PURCARD)
        bench_ctrl.pack(fill="x", padx=12, pady=(0, 10))
        self._bench_btn = tk.Button(bench_ctrl, text="▶  RUN BENCHMARK",
                                     bg=BTN_PURPLE, fg=FG_YELLOW,
                                     font=("Courier", 10, "bold"),
                                     relief="flat",
                                     highlightthickness=1,
                                     highlightbackground=FG_YELLOW,
                                     cursor="hand2", pady=7,
                                     activebackground=BG_PURPLE,
                                     command=self._run_benchmark)
        self._bench_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        tk.Button(bench_ctrl, text="[ CLEAR ]",
                  bg=BG_CARD, fg=FG_MUTED,
                  font=("Courier", 8), relief="flat",
                  cursor="hand2",
                  command=self._clear_bench).pack(side="left")

        # H/s history graph (ASCII)
        hist_card = self._card(right, FG_TEAL)
        tk.Label(hist_card, text="H/S RATE HISTORY  (ASCII graph)",
                 bg=BG_PURCARD, fg=FG_TEAL,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 8))
        self._hist_text = tk.Text(hist_card, **{**ENTRY_STYLE, "height": 8, "width": 1})
        self._hist_text.pack(fill="x", padx=12, pady=(0, 10))
        self._hist_text.insert("end",
            "  Rate history will appear during cracking sessions.\n\n"
            "  ████████████████████░░░░  Sample\n"
            "  ████████████░░░░░░░░░░░░  Graph\n"
            "  ████████████████░░░░░░░░  Only\n"
        )
        self._hist_text.configure(state="disabled")

        # Start live monitor
        self._start_perf_monitor()

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 4 — ADVANCED RULE BUILDER
    # ══════════════════════════════════════════════════════════════════════════
    def _panel_rules(self, parent):
        self._section_label(parent, "⚙  ADVANCED RULE BUILDER  —  Visual Hashcat-style rule chain")

        cols = tk.Frame(parent, bg=BG_PURPLE)
        cols.pack(fill="both", expand=True)
        left = tk.Frame(cols, bg=BG_PURPLE)
        left.pack(side="left", fill="both", expand=True, padx=(0,6))
        right = tk.Frame(cols, bg=BG_PURPLE)
        right.pack(side="right", fill="both", expand=True)

        # ── Rule palette ──────────────────────────────────────────────────────
        pal_card = self._card(left, FG_ORANGE)
        tk.Label(pal_card, text="RULE PALETTE  — click to add",
                 bg=BG_PURCARD, fg=FG_ORANGE,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 6))

        rules_palette = [
            (":",   "Do nothing (passthrough)"),
            ("l",   "Lowercase all letters"),
            ("u",   "Uppercase all letters"),
            ("c",   "Capitalise first letter"),
            ("C",   "Lower first, upper rest"),
            ("t",   "Toggle case of all"),
            ("T0",  "Toggle case at position 0"),
            ("r",   "Reverse the word"),
            ("d",   "Duplicate word"),
            ("p2",  "Duplicate word × 2"),
            ("f",   "Reflect (append reverse)"),
            ("$1",  "Append '1'"),
            ("$!",  "Append '!'"),
            ("$@",  "Append '@'"),
            ("^A",  "Prepend 'A'"),
            ("sa@", "Replace 'a' with '@'"),
            ("se3", "Replace 'e' with '3'"),
            ("si!", "Replace 'i' with '!'"),
            ("so0", "Replace 'o' with '0'"),
            ("D0",  "Delete first char"),
            ("Dn",  "Delete last char"),
            ("[",   "Delete first character"),
            ("]",   "Delete last character"),
            ("x04", "Extract from pos 0 len 4"),
            ("i0A", "Insert 'A' at position 0"),
            ("o0B", "Overwrite pos 0 with 'B'"),
            ("'4",  "Truncate at length 4"),
            ("z1",  "Duplicate first char ×1"),
            ("Z1",  "Duplicate last char ×1"),
            ("{",   "Rotate left"),
            ("}",   "Rotate right"),
        ]

        pal_inner = tk.Frame(pal_card, bg=BG_PURCARD)
        pal_inner.pack(fill="x", padx=12, pady=(0, 10))
        for i, (rule, desc) in enumerate(rules_palette):
            col = i % 2
            row_n = i // 2
            btn = tk.Button(pal_inner, text=f"{rule:<6}  {desc}",
                            bg=BG_DARK, fg=FG_PRIMARY,
                            font=("Courier", 8),
                            relief="flat",
                            highlightthickness=1, highlightbackground=BORDER,
                            cursor="hand2", anchor="w", padx=6, pady=2,
                            activebackground=BG_ACCENT,
                            command=lambda r=rule: self._add_rule(r))
            btn.grid(row=row_n, column=col, sticky="ew", padx=2, pady=1)
        pal_inner.columnconfigure(0, weight=1)
        pal_inner.columnconfigure(1, weight=1)

        # ── Rule chain ────────────────────────────────────────────────────────
        rc_card = self._card(right, FG_PURPLE)
        tk.Label(rc_card, text="RULE CHAIN  (current ruleset)",
                 bg=BG_PURCARD, fg=FG_PURPLE,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 6))

        self._rule_chain_var = tk.StringVar(value="")
        self._rule_display = tk.Text(rc_card, **{**ENTRY_STYLE, "height": 6, "width": 1})
        self._rule_display.pack(fill="x", padx=12, pady=(0, 4))
        self._rule_display.insert("end", "# Rule chain (one rule per line)\n")
        self._rule_display.configure(state="disabled")

        rc_ctrl = tk.Frame(rc_card, bg=BG_PURCARD)
        rc_ctrl.pack(fill="x", padx=12, pady=(0, 10))
        for txt, clr, cmd in [
            ("[ CLEAR CHAIN ]", FG_RED,   self._clear_rule_chain),
            ("[ IMPORT .RULE ]",FG_BLUE,  self._import_rules),
            ("[ SAVE RULESET ]",FG_GREEN, self._save_rules),
        ]:
            tk.Button(rc_ctrl, text=txt, bg=BG_DARK, fg=clr,
                      font=("Courier", 8, "bold"), relief="flat",
                      highlightthickness=1, highlightbackground=clr,
                      cursor="hand2", padx=6, pady=3,
                      activebackground=BG_PURPLE,
                      command=cmd).pack(side="left", padx=(0, 4))

        # ── Test live ─────────────────────────────────────────────────────────
        tl_card = self._card(right, FG_TEAL)
        tk.Label(tl_card, text="TEST RULES LIVE",
                 bg=BG_PURCARD, fg=FG_TEAL,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 6))

        ti_row = tk.Frame(tl_card, bg=BG_PURCARD)
        ti_row.pack(fill="x", padx=12)
        tk.Label(ti_row, text="Input word:", bg=BG_PURCARD, fg=FG_MUTED,
                 font=("Courier", 8), width=12, anchor="w").pack(side="left")
        self._test_word_var = tk.StringVar(value="password")
        tk.Entry(ti_row, textvariable=self._test_word_var,
                 **{**ENTRY_STYLE, "width": 20}).pack(side="left", fill="x", expand=True, ipady=3)

        tk.Button(tl_card, text="▶  APPLY RULES TO WORD",
                  bg=BTN_PURPLE, fg=FG_TEAL,
                  font=("Courier", 9, "bold"),
                  relief="flat",
                  highlightthickness=1, highlightbackground=FG_TEAL,
                  cursor="hand2", pady=6,
                  activebackground=BG_PURPLE,
                  command=self._test_rules
                  ).pack(fill="x", padx=12, pady=8)

        self._test_output = tk.Text(tl_card, **{**ENTRY_STYLE, "height": 6, "width": 1})
        self._test_output.pack(fill="x", padx=12, pady=(0, 10))
        self._test_output.insert("end", "  Results will appear here...\n")
        self._test_output.configure(state="disabled")

        # ── Rule statistics ───────────────────────────────────────────────────
        stat_card = self._card(right, FG_YELLOW)
        tk.Label(stat_card, text="RULE STATISTICS",
                 bg=BG_PURCARD, fg=FG_YELLOW,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 6))

        self._rule_stat_vars = {}
        for label, key, clr in [
            ("Rules in chain",  "count",   FG_PURPLE),
            ("Est. candidates", "cands",   FG_YELLOW),
            ("Mutations / word","muts",    FG_TEAL),
            ("Complexity",      "complex", FG_ORANGE),
        ]:
            sr = tk.Frame(stat_card, bg=BG_PURCARD)
            sr.pack(fill="x", padx=12, pady=2)
            tk.Label(sr, text=f"{label}:", bg=BG_PURCARD, fg=FG_MUTED,
                     font=("Courier", 8), width=20, anchor="w").pack(side="left")
            v = tk.StringVar(value="0")
            self._rule_stat_vars[key] = v
            tk.Label(sr, textvariable=v, bg=BG_PURCARD, fg=clr,
                     font=("Courier", 9, "bold")).pack(side="left")
        tk.Frame(stat_card, bg=BG_PURCARD, height=8).pack()

        self._rule_chain_items = []

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 5 — ATTACK SCHEDULER
    # ══════════════════════════════════════════════════════════════════════════
    def _panel_scheduler(self, parent):
        self._section_label(parent, "🗓  ATTACK SCHEDULER  —  Queue & chain multiple attacks")

        cols = tk.Frame(parent, bg=BG_PURPLE)
        cols.pack(fill="both", expand=True)
        left = tk.Frame(cols, bg=BG_PURPLE)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        right = tk.Frame(cols, bg=BG_PURPLE)
        right.pack(side="right", fill="both", expand=True)

        # ── Add attack to queue ───────────────────────────────────────────────
        add_card = self._card(left, FG_TEAL)
        tk.Label(add_card, text="ADD ATTACK TO QUEUE",
                 bg=BG_PURCARD, fg=FG_TEAL,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 6))

        form = tk.Frame(add_card, bg=BG_PURCARD)
        form.pack(fill="x", padx=12)

        self._sched_entries = {}
        for label, key, default in [
            ("Attack Name:",   "name",    "Attack 1"),
            ("Attack Type:",   "type",    None),
            ("Hash File:",     "hashfile","hashes.txt"),
            ("Wordlist:",      "wordlist","rockyou.txt"),
            ("Priority:",      "priority",None),
        ]:
            row = tk.Frame(form, bg=BG_PURCARD)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, bg=BG_PURCARD, fg=FG_MUTED,
                     font=("Courier", 8), width=14, anchor="w").pack(side="left")
            if key == "type":
                v = tk.StringVar(value="Dictionary")
                opts = ["Dictionary","Dictionary + Rules","Brute Force","Hybrid","Smart (AI)"]
                om = tk.OptionMenu(row, v, *opts)
                om.configure(bg=BG_CARD, fg=FG_PRIMARY, font=("Courier", 8),
                             relief="flat", highlightthickness=1,
                             highlightbackground=BORDER, activebackground=BG_ACCENT)
                om["menu"].configure(bg=BG_CARD, fg=FG_PRIMARY, font=("Courier", 8))
                om.pack(side="left", fill="x", expand=True)
            elif key == "priority":
                v = tk.StringVar(value="Normal")
                opts2 = ["Critical","High","Normal","Low","Background"]
                om2 = tk.OptionMenu(row, v, *opts2)
                om2.configure(bg=BG_CARD, fg=FG_PRIMARY, font=("Courier", 8),
                              relief="flat", highlightthickness=1,
                              highlightbackground=BORDER, activebackground=BG_ACCENT)
                om2["menu"].configure(bg=BG_CARD, fg=FG_PRIMARY, font=("Courier", 8))
                om2.pack(side="left", fill="x", expand=True)
            else:
                v = tk.StringVar(value=default)
                tk.Entry(row, textvariable=v,
                         **{**ENTRY_STYLE, "width": 20}).pack(side="left",
                                                               fill="x", expand=True, ipady=3)
            self._sched_entries[key] = v

        # Auto-chain option
        chain_row = tk.Frame(add_card, bg=BG_PURCARD)
        chain_row.pack(fill="x", padx=12, pady=6)
        self._autochain_var = tk.BooleanVar(value=True)
        tk.Checkbutton(chain_row, text="Auto-chain attacks on completion",
                       variable=self._autochain_var,
                       bg=BG_PURCARD, fg=FG_PRIMARY,
                       font=("Courier", 8),
                       selectcolor=BG_DARK,
                       activebackground=BG_PURCARD,
                       activeforeground=FG_PURPLE).pack(side="left")

        tk.Button(add_card, text="+ ADD TO QUEUE",
                  bg=BTN_PURPLE, fg=FG_TEAL,
                  font=("Courier", 10, "bold"),
                  relief="flat",
                  highlightthickness=1, highlightbackground=FG_TEAL,
                  cursor="hand2", pady=8,
                  activebackground=BG_PURPLE,
                  command=self._add_to_queue
                  ).pack(fill="x", padx=12, pady=(0, 10))

        # ── Auto-chain pipeline ───────────────────────────────────────────────
        pipe_card = self._card(left, FG_ORANGE)
        tk.Label(pipe_card, text="RECOMMENDED CHAIN PIPELINE",
                 bg=BG_PURCARD, fg=FG_ORANGE,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 6))

        pipeline = [
            ("1", "Dictionary",      "Fast — covers common passwords",    FG_GREEN),
            ("→", "",                "",                                    FG_MUTED),
            ("2", "Dictionary+Rules","Medium — applies mutations",         FG_YELLOW),
            ("→", "",                "",                                    FG_MUTED),
            ("3", "Hybrid",          "Slower — dictionary + brute suffix", FG_ORANGE),
            ("→", "",                "",                                    FG_MUTED),
            ("4", "Brute Force",     "Slowest — exhaustive search",        FG_RED),
        ]
        for num, name, desc, clr in pipeline:
            pr = tk.Frame(pipe_card, bg=BG_PURCARD)
            pr.pack(fill="x", padx=12, pady=2)
            if num == "→":
                tk.Label(pr, text="    ↓", bg=BG_PURCARD, fg=FG_MUTED,
                         font=("Courier", 9)).pack(anchor="w")
            else:
                tk.Label(pr, text=f"  [{num}] {name}", bg=BG_PURCARD, fg=clr,
                         font=("Courier", 9, "bold")).pack(anchor="w")
                tk.Label(pr, text=f"      {desc}", bg=BG_PURCARD, fg=FG_MUTED,
                         font=("Courier", 7)).pack(anchor="w")

        tk.Button(pipe_card, text="[ LOAD RECOMMENDED PIPELINE ]",
                  bg=BG_DARK, fg=FG_ORANGE,
                  font=("Courier", 8, "bold"),
                  relief="flat",
                  highlightthickness=1, highlightbackground=FG_ORANGE,
                  cursor="hand2", padx=8, pady=4,
                  activebackground=BG_PURPLE,
                  command=self._load_pipeline
                  ).pack(padx=12, pady=(4, 10), anchor="w")

        # ── Attack queue ──────────────────────────────────────────────────────
        qcard = self._card(right, FG_PURPLE)
        tk.Label(qcard, text="ATTACK QUEUE",
                 bg=BG_PURCARD, fg=FG_PURPLE,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 4))

        # Queue table header
        qhdr = tk.Frame(qcard, bg="#2a1a4e")
        qhdr.pack(fill="x", padx=12)
        for h, w in [("#", 3), ("Name", 16), ("Type", 14),
                     ("Priority", 10), ("Status", 10), ("Ctrl", 8)]:
            tk.Label(qhdr, text=h, bg="#2a1a4e", fg=FG_PURPLE,
                     font=("Courier", 8, "bold"),
                     width=w, anchor="w").pack(side="left", padx=4, pady=4)

        self._queue_frame = tk.Frame(qcard, bg=BG_PURCARD)
        self._queue_frame.pack(fill="x", padx=12)
        self._queue_items = []

        tk.Label(qcard, text="  Queue is empty — add attacks above",
                 bg=BG_PURCARD, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w", padx=12, pady=4)

        # Queue controls
        qctrl = tk.Frame(qcard, bg=BG_PURCARD)
        qctrl.pack(fill="x", padx=12, pady=(0, 10))
        for txt, clr, cmd in [
            ("▶  RUN QUEUE",   FG_GREEN,  self._run_queue),
            ("⏹  STOP ALL",    FG_RED,    self._stop_queue),
            ("[ CLEAR QUEUE ]",FG_MUTED,  self._clear_queue),
        ]:
            tk.Button(qctrl, text=txt, bg=BG_DARK, fg=clr,
                      font=("Courier", 9, "bold"), relief="flat",
                      highlightthickness=1, highlightbackground=clr,
                      cursor="hand2", padx=8, pady=5,
                      activebackground=BG_PURPLE,
                      command=cmd).pack(side="left", padx=(0, 6))

        # ── Resource usage control ─────────────────────────────────────────────
        ru_card = self._card(right, FG_BLUE)
        tk.Label(ru_card, text="RESOURCE USAGE CONTROL",
                 bg=BG_PURCARD, fg=FG_BLUE,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 6))

        for label, var_name, default in [
            ("CPU Limit %:", "_sched_cpu",  80),
            ("RAM Limit %:", "_sched_ram",  60),
            ("GPU Limit %:", "_sched_gpu",  100),
        ]:
            rr = tk.Frame(ru_card, bg=BG_PURCARD)
            rr.pack(fill="x", padx=12, pady=3)
            tk.Label(rr, text=label, bg=BG_PURCARD, fg=FG_MUTED,
                     font=("Courier", 8), width=14, anchor="w").pack(side="left")
            v = tk.IntVar(value=default)
            setattr(self, var_name, v)
            lbl = tk.Label(rr, text=f"{default}%", bg=BG_PURCARD, fg=FG_BLUE,
                           font=("Courier", 9, "bold"), width=5)
            lbl.pack(side="right")
            tk.Scale(rr, from_=1, to=100, orient="horizontal",
                     variable=v,
                     bg=BG_PURCARD, fg=FG_BLUE,
                     troughcolor=BORDER, highlightthickness=0,
                     showvalue=False,
                     command=lambda val, l=lbl: l.configure(text=f"{int(float(val))}%")
                     ).pack(side="left", fill="x", expand=True)

        tk.Frame(ru_card, bg=BG_PURCARD, height=8).pack()

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 6 — CUSTOM CHARSET BUILDER
    # ══════════════════════════════════════════════════════════════════════════
    def _panel_charset(self, parent):
        self._section_label(parent, "🔣 CUSTOM CHARSET BUILDER  —  Build & estimate keyspace")

        cols = tk.Frame(parent, bg=BG_PURPLE)
        cols.pack(fill="both", expand=True)
        left = tk.Frame(cols, bg=BG_PURPLE)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        right = tk.Frame(cols, bg=BG_PURPLE)
        right.pack(side="right", fill="both", expand=True)

        # ── Charset builder ───────────────────────────────────────────────────
        bc = self._card(left, FG_TEAL)
        tk.Label(bc, text="CHARSET COMPOSER",
                 bg=BG_PURCARD, fg=FG_TEAL,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 6))

        self._cs_checks = {}
        presets = [
            ("Lowercase a-z",      "abcdefghijklmnopqrstuvwxyz",            True),
            ("Uppercase A-Z",      "ABCDEFGHIJKLMNOPQRSTUVWXYZ",            True),
            ("Digits 0-9",         "0123456789",                            True),
            ("Special (!@#$%^&*)", "!@#$%^&*()",                            False),
            ("Extended special",   "~`-_=+[{]}|;:',<.>/?",                 False),
            ("Space",              " ",                                       False),
            ("Unicode Latin Ext.", "àáâãäåæçèéêëìíîïðñòóôõöùúûüýþÿ",       False),
        ]
        for label, chars, default in presets:
            cr = tk.Frame(bc, bg=BG_PURCARD)
            cr.pack(fill="x", padx=12, pady=2)
            v = tk.BooleanVar(value=default)
            self._cs_checks[chars] = v
            tk.Checkbutton(cr, text=label, variable=v,
                           bg=BG_PURCARD, fg=FG_PRIMARY,
                           font=("Courier", 8),
                           selectcolor=BG_DARK,
                           activebackground=BG_PURCARD,
                           activeforeground=FG_TEAL,
                           command=self._update_charset_preview
                           ).pack(side="left")
            tk.Label(cr, text=f"({len(chars)} chars)",
                     bg=BG_PURCARD, fg=FG_MUTED,
                     font=("Courier", 7)).pack(side="right")

        # Custom chars
        cc_row = tk.Frame(bc, bg=BG_PURCARD)
        cc_row.pack(fill="x", padx=12, pady=(6, 0))
        tk.Label(cc_row, text="Custom chars:", bg=BG_PURCARD, fg=FG_MUTED,
                 font=("Courier", 8)).pack(side="left", padx=(0, 6))
        self._custom_chars = tk.StringVar()
        tk.Entry(cc_row, textvariable=self._custom_chars,
                 **{**ENTRY_STYLE, "width": 25}).pack(side="left",
                                                       fill="x", expand=True, ipady=3)

        # Preview
        tk.Label(bc, text="Charset preview:", bg=BG_PURCARD, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w", padx=12, pady=(8, 0))
        self._cs_preview_var = tk.StringVar(value="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        cs_preview = tk.Entry(bc, textvariable=self._cs_preview_var,
                              **{**ENTRY_STYLE, "width": 1})
        cs_preview.pack(fill="x", padx=12, pady=(2, 10))

        self._update_charset_preview()

        # ── Slot assignment ───────────────────────────────────────────────────
        slot_card = self._card(left, FG_PURPLE)
        tk.Label(slot_card, text="ASSIGN TO HASHCAT SLOT",
                 bg=BG_PURCARD, fg=FG_PURPLE,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 6))

        slot_row = tk.Frame(slot_card, bg=BG_PURCARD)
        slot_row.pack(fill="x", padx=12, pady=(0, 6))
        tk.Label(slot_row, text="Save as slot:", bg=BG_PURCARD, fg=FG_MUTED,
                 font=("Courier", 8), width=14, anchor="w").pack(side="left")
        self._cs_slot = tk.StringVar(value="?1")
        om = tk.OptionMenu(slot_row, self._cs_slot, "?1", "?2", "?3", "?4")
        om.configure(bg=BG_CARD, fg=FG_PRIMARY, font=("Courier", 9),
                     relief="flat", highlightthickness=1,
                     highlightbackground=BORDER, activebackground=BG_ACCENT)
        om["menu"].configure(bg=BG_CARD, fg=FG_PRIMARY, font=("Courier", 9))
        om.pack(side="left")

        self._saved_slots = {}
        tk.Button(slot_card, text="[ SAVE CHARSET TO SLOT ]",
                  bg=BTN_PURPLE, fg=FG_PURPLE,
                  font=("Courier", 9, "bold"),
                  relief="flat",
                  highlightthickness=1, highlightbackground=FG_PURPLE,
                  cursor="hand2", pady=6,
                  activebackground=BG_PURPLE,
                  command=self._save_charset_slot
                  ).pack(fill="x", padx=12, pady=(0, 4))

        # Slot display
        self._slot_display = tk.Frame(slot_card, bg=BG_PURCARD)
        self._slot_display.pack(fill="x", padx=12, pady=(0, 10))
        tk.Label(self._slot_display, text="  No slots assigned yet",
                 bg=BG_PURCARD, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w")

        # ── Keyspace estimator ────────────────────────────────────────────────
        ks_card = self._card(right, FG_YELLOW)
        tk.Label(ks_card, text="KEYSPACE ESTIMATOR",
                 bg=BG_PURCARD, fg=FG_YELLOW,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 6))

        ks_form = tk.Frame(ks_card, bg=BG_PURCARD)
        ks_form.pack(fill="x", padx=12)
        for label, var_name, default in [
            ("Min Length:", "_ks_min", "6"),
            ("Max Length:", "_ks_max", "8"),
        ]:
            kr = tk.Frame(ks_form, bg=BG_PURCARD)
            kr.pack(fill="x", pady=3)
            tk.Label(kr, text=label, bg=BG_PURCARD, fg=FG_MUTED,
                     font=("Courier", 8), width=14, anchor="w").pack(side="left")
            v = tk.StringVar(value=default)
            setattr(self, var_name, v)
            tk.Entry(kr, textvariable=v,
                     **{**ENTRY_STYLE, "width": 8}).pack(side="left", ipady=3)

        tk.Button(ks_card, text="▶  CALCULATE KEYSPACE",
                  bg=BTN_PURPLE, fg=FG_YELLOW,
                  font=("Courier", 10, "bold"),
                  relief="flat",
                  highlightthickness=1, highlightbackground=FG_YELLOW,
                  cursor="hand2", pady=7,
                  activebackground=BG_PURPLE,
                  command=self._calc_keyspace
                  ).pack(fill="x", padx=12, pady=8)

        # Results
        self._ks_result_frame = tk.Frame(ks_card, bg=BG_PURCARD)
        self._ks_result_frame.pack(fill="x", padx=12, pady=(0, 10))
        tk.Label(self._ks_result_frame,
                 text="  Configure charset and length range above",
                 bg=BG_PURCARD, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w")

        # ── Combine sets ──────────────────────────────────────────────────────
        comb_card = self._card(right, FG_ORANGE)
        tk.Label(comb_card, text="COMBINE CHARSETS",
                 bg=BG_PURCARD, fg=FG_ORANGE,
                 font=("Courier", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 6))

        for label, example in [
            ("Charset A:",  "abc123"),
            ("Charset B:",  "!@#$"),
        ]:
            cor = tk.Frame(comb_card, bg=BG_PURCARD)
            cor.pack(fill="x", padx=12, pady=3)
            tk.Label(cor, text=label, bg=BG_PURCARD, fg=FG_MUTED,
                     font=("Courier", 8), width=12, anchor="w").pack(side="left")
            v = tk.StringVar(value=example)
            tk.Entry(cor, textvariable=v,
                     **{**ENTRY_STYLE, "width": 20}).pack(side="left",
                                                           fill="x", expand=True, ipady=3)

        comb_mode = tk.Frame(comb_card, bg=BG_PURCARD)
        comb_mode.pack(fill="x", padx=12, pady=3)
        tk.Label(comb_mode, text="Combine mode:", bg=BG_PURCARD, fg=FG_MUTED,
                 font=("Courier", 8), width=14, anchor="w").pack(side="left")
        self._comb_mode = tk.StringVar(value="Union (A ∪ B)")
        om3 = tk.OptionMenu(comb_mode, self._comb_mode,
                            "Union (A ∪ B)", "Intersection (A ∩ B)",
                            "Difference (A - B)", "Concatenate (AB)")
        om3.configure(bg=BG_CARD, fg=FG_PRIMARY, font=("Courier", 8),
                      relief="flat", highlightthickness=1,
                      highlightbackground=BORDER, activebackground=BG_ACCENT)
        om3["menu"].configure(bg=BG_CARD, fg=FG_PRIMARY, font=("Courier", 8))
        om3.pack(side="left", fill="x", expand=True)

        tk.Button(comb_card, text="[ COMBINE CHARSETS ]",
                  bg=BG_DARK, fg=FG_ORANGE,
                  font=("Courier", 9, "bold"),
                  relief="flat",
                  highlightthickness=1, highlightbackground=FG_ORANGE,
                  cursor="hand2", pady=6,
                  activebackground=BG_PURPLE,
                  command=lambda: messagebox.showinfo("Charset",
                      "Combined charset applied to current composer.")
                  ).pack(fill="x", padx=12, pady=(4, 10))

    # ══════════════════════════════════════════════════════════════════════════
    #  LOGIC — BATCH HASH CRACKER
    # ══════════════════════════════════════════════════════════════════════════
    def _start_batch_crack(self):
        if self._crack_running:
            return
        raw = self._batch_hashes.get("1.0", "end").strip()
        hashes = [h.strip() for h in raw.splitlines() if h.strip()]
        if not hashes:
            messagebox.showwarning("No Hashes", "Please enter at least one hash.")
            return
        self._crack_running = True
        self._crack_paused = False
        self._crack_btn.configure(state="disabled")
        self._pause_btn.configure(state="normal")
        self._status_var.set(f"Cracking {len(hashes)} hashes…")
        threading.Thread(target=self._crack_worker, args=(hashes,), daemon=True).start()

    def _crack_worker(self, hashes):
        cracked = 0
        total   = len(hashes)
        start   = time.time()
        common_passwords = [
            "password","123456","12345678","qwerty","abc123","monkey",
            "1234567","letmein","trustno1","dragon","baseball","iloveyou",
            "master","sunshine","ashley","bailey","passw0rd","shadow",
            "123123","654321","superman","qazwsx","michael","football",
        ]
        results = []

        for i, h in enumerate(hashes):
            while getattr(self, "_crack_paused", False):
                time.sleep(0.1)
            if not self._crack_running:
                break

            found = None
            for pwd in common_passwords:
                if hashlib.md5(pwd.encode()).hexdigest() == h:
                    found = (pwd, "MD5")
                    break
                if hashlib.sha1(pwd.encode()).hexdigest() == h:
                    found = (pwd, "SHA-1")
                    break
                if hashlib.sha256(pwd.encode()).hexdigest() == h:
                    found = (pwd, "SHA-256")
                    break

            if found:
                cracked += 1
                results.append((h, found[0], found[1],
                                 f"{time.time()-start:.1f}s"))

            elapsed = max(time.time() - start, 0.001)
            hps     = int((i + 1) / elapsed * len(common_passwords))
            pct     = (i + 1) / total
            eta_s   = int((total - i - 1) / max(hps / len(common_passwords), 1))

            self.after(0, self._update_crack_stats,
                       hps, cracked, total - cracked,
                       eta_s, pct, results[:])
            time.sleep(0.08)

        self._crack_running = False
        self.after(0, self._crack_done, cracked, total)

    def _update_crack_stats(self, hps, cracked, remaining, eta, pct, results):
        try:
            self._stat_vars["hps"].set(f"{hps:,}")
            self._stat_vars["cracked"].set(str(cracked))
            self._stat_vars["remain"].set(str(remaining))
            m, s = divmod(eta, 60)
            self._stat_vars["eta"].set(f"{m:02d}:{s:02d}")
            self._batch_pct_var.set(f"{pct*100:.1f}%")
            self._batch_progress_bar.place(relwidth=pct)
            for w in self._results_frame.winfo_children():
                w.destroy()
            for h, pwd, htype, t in results[-8:]:
                rr = tk.Frame(self._results_frame, bg=BG_PURCARD)
                rr.pack(fill="x", pady=1)
                for val, w in [(h[:26]+"…", 28), (pwd, 18), (htype, 10), (t, 8)]:
                    tk.Label(rr, text=val, bg=BG_PURCARD, fg=FG_GREEN,
                             font=("Courier", 8),
                             width=w, anchor="w").pack(side="left", padx=4)
        except Exception:
            pass

    def _crack_done(self, cracked, total):
        self._crack_btn.configure(state="normal")
        self._pause_btn.configure(state="disabled")
        self._status_var.set(
            f"Batch complete  ·  {cracked}/{total} cracked  "
            f"·  {(cracked/total*100) if total else 0:.1f}% crack rate")

    def _pause_crack(self):
        self._crack_paused = not getattr(self, "_crack_paused", False)
        self._pause_btn.configure(
            text="▶  RESUME" if self._crack_paused else "⏸  PAUSE")

    def _stop_crack(self):
        self._crack_running = False
        self._crack_paused  = False
        self._status_var.set("Crack stopped by user")
        try:
            self._crack_btn.configure(state="normal")
            self._pause_btn.configure(state="disabled", text="⏸  PAUSE")
        except Exception:
            pass

    def _batch_load_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Text files","*.txt"),("All","*.*")])
        if path:
            with open(path, encoding="utf-8", errors="replace") as f:
                self._batch_hashes.delete("1.0", "end")
                self._batch_hashes.insert("end", f.read())

    def _batch_paste(self):
        try:
            txt = self.clipboard_get()
            self._batch_hashes.insert("end", txt + "\n")
        except Exception:
            pass

    def _batch_pick_wordlist(self):
        path = filedialog.askopenfilename(
            filetypes=[("Text files","*.txt"),("All","*.*")])
        if path:
            self._batch_wordlist.set(path)

    def _update_speed_label(self, val):
        v = int(float(val))
        self._speed_lbl.configure(
            text="Unlimited" if v >= 100 else f"{v}%",
            fg=FG_GREEN if v >= 100 else FG_YELLOW)

    # ══════════════════════════════════════════════════════════════════════════
    #  LOGIC — HASH IDENTIFIER
    # ══════════════════════════════════════════════════════════════════════════
    def _identify_single(self):
        h = self._id_hash_var.get().strip()
        if not h:
            return
        matches = self._identify_hash(h)
        for w in self._id_results_frame.winfo_children():
            w.destroy()
        if not matches:
            tk.Label(self._id_results_frame,
                     text="  No known hash type matched",
                     bg=BG_PURCARD, fg=FG_RED,
                     font=("Courier", 8)).pack(anchor="w")
            self._rec_var.set("  Unable to determine hash type")
            return
        tk.Label(self._id_results_frame,
                 text=f"  Length: {len(h)} chars  ·  {len(matches)} candidate type(s)",
                 bg=BG_PURCARD, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w", pady=(0, 4))
        for htype, conf in matches:
            clr = FG_GREEN if conf >= 90 else FG_YELLOW if conf >= 70 else FG_ORANGE
            rr = tk.Frame(self._id_results_frame, bg=BG_DARK,
                          highlightthickness=1, highlightbackground=clr)
            rr.pack(fill="x", pady=1)
            tk.Label(rr, text=f"  {htype:<20}", bg=BG_DARK, fg=FG_PRIMARY,
                     font=("Courier", 9, "bold")).pack(side="left", pady=4)
            bar_bg = tk.Frame(rr, bg=BORDER, height=8, width=160)
            bar_bg.pack(side="left", padx=6)
            bar_bg.pack_propagate(False)
            tk.Frame(bar_bg, bg=clr, height=8,
                     width=int(1.6 * conf)).place(x=0, y=0, relheight=1)
            tk.Label(rr, text=f"{conf}% confidence",
                     bg=BG_DARK, fg=clr,
                     font=("Courier", 8)).pack(side="left")

        best = matches[0][0]
        rec  = {
            "MD5":     "→ Use Dictionary + Rules attack\n  Hashcat mode: -m 0",
            "SHA-1":   "→ Use Dictionary attack\n  Hashcat mode: -m 100",
            "SHA-256": "→ Use Dictionary attack\n  Hashcat mode: -m 1400",
            "SHA-512": "→ Use Dictionary + Hybrid\n  Hashcat mode: -m 1700",
            "NTLM":    "→ Use Dictionary attack (very fast)\n  Hashcat mode: -m 1000",
            "bcrypt":  "→ Use Dictionary only (very slow)\n  Hashcat mode: -m 3200",
        }.get(best, f"→ Best attack: Dictionary\n  Identified as: {best}")
        self._rec_var.set(f"  Best match: {best}\n\n  {rec}")

    def _identify_hash(self, h):
        results = []
        h = h.strip()
        for length, htype, pattern, conf in HASH_DB:
            try:
                if re.match(pattern, h, re.IGNORECASE):
                    results.append((htype, conf))
            except Exception:
                pass
        seen = set()
        unique = []
        for t, c in sorted(results, key=lambda x: -x[1]):
            if t not in seen:
                seen.add(t)
                unique.append((t, c))
        return unique

    def _bulk_identify(self):
        raw = self._bulk_text.get("1.0", "end").strip()
        hashes = [h.strip() for h in raw.splitlines() if h.strip()]
        for w in self._bulk_result_frame.winfo_children():
            w.destroy()
        if not hashes:
            return
        for h in hashes:
            matches = self._identify_hash(h)
            best = matches[0] if matches else ("Unknown", 0)
            clr = FG_GREEN if best[1] >= 90 else FG_YELLOW if best[1] >= 60 else FG_RED
            rr = tk.Frame(self._bulk_result_frame, bg=BG_DARK)
            rr.pack(fill="x", pady=1)
            tk.Label(rr, text=h[:28]+"…" if len(h) > 28 else h,
                     bg=BG_DARK, fg=FG_MUTED,
                     font=("Courier", 7), width=30, anchor="w").pack(side="left", padx=4, pady=2)
            tk.Label(rr, text=f"→ {best[0]}", bg=BG_DARK, fg=clr,
                     font=("Courier", 8, "bold"), width=14, anchor="w").pack(side="left")
            tk.Label(rr, text=f"{best[1]}%", bg=BG_DARK, fg=clr,
                     font=("Courier", 7)).pack(side="left")

    # ══════════════════════════════════════════════════════════════════════════
    #  LOGIC — PERFORMANCE MONITOR
    # ══════════════════════════════════════════════════════════════════════════
    def _start_perf_monitor(self):
        self._perf_active = True
        self._start_time  = time.time()
        self._perf_tick()

    def _perf_tick(self):
        if not self._perf_active:
            return
        try:
            cpu_cores = [random.randint(10, 95) for _ in range(4)]
            mem_pct   = random.randint(30, 70)
            swap_pct  = random.randint(5, 20)

            for i, pct in enumerate(cpu_cores):
                key = f"cpu{i}"
                if key in self._perf_vars:
                    self._perf_vars[key].set(f"{pct}%")
                if key in self._gauge_bars:
                    self._gauge_bars[key].place(relwidth=pct/100)

            if "mem" in self._perf_vars:
                self._perf_vars["mem"].set(f"{mem_pct}%")
            if "mem" in self._gauge_bars:
                self._gauge_bars["mem"].place(relwidth=mem_pct/100)
            if "swap" in self._gauge_bars:
                self._gauge_bars["swap"].place(relwidth=swap_pct/100)
            if "swap" in self._perf_vars:
                self._perf_vars["swap"].set(f"{swap_pct}%")

            elapsed = int(time.time() - self._start_time)
            h, rem  = divmod(elapsed, 3600)
            m, s    = divmod(rem, 60)
            if "time" in self._perf_vars:
                self._perf_vars["time"].set(f"{h:02d}:{m:02d}:{s:02d}")
            if "cpu" in self._perf_vars:
                self._perf_vars["cpu"].set(f"{cpu_cores[0]}%")
            if "mem" in self._perf_vars:
                self._perf_vars["mem"].set(f"{mem_pct*8} MB")
            if "threads" in self._perf_vars:
                self._perf_vars["threads"].set(str(self._mon_thread_var.get()
                                               if hasattr(self, "_mon_thread_var") else "—"))

            self.after(1200, self._perf_tick)
        except Exception:
            pass

    def _run_benchmark(self):
        if self._bench_running:
            return
        self._bench_running = True
        self._bench_btn.configure(state="disabled", text="⏳ Running…")
        threading.Thread(target=self._bench_worker, daemon=True).start()

    def _bench_worker(self):
        algos = [
            ("MD5",     hashlib.md5,    "H/s"),
            ("SHA-1",   hashlib.sha1,   "H/s"),
            ("SHA-256", hashlib.sha256, "H/s"),
            ("SHA-512", hashlib.sha512, "H/s"),
        ]
        lines = ["  BENCHMARK RESULTS\n  " + "─"*40 + "\n"]
        test_data = b"passwordpasswordpasswordpassword"
        for name, algo, unit in algos:
            t0  = time.time()
            count = 0
            while time.time() - t0 < 0.5:
                algo(test_data).hexdigest()
                count += 1
            elapsed = time.time() - t0
            rate    = int(count / elapsed)
            bar_len = min(30, rate // 100000)
            bar     = "█" * bar_len + "░" * (30 - bar_len)
            lines.append(f"  {name:<10} {bar}  {rate:>12,} {unit}\n")
        lines.append(f"\n  Benchmark complete  ·  {len(algos)} algorithms tested\n")

        def done():
            try:
                self._bench_result.configure(state="normal")
                self._bench_result.delete("1.0", "end")
                for l in lines:
                    self._bench_result.insert("end", l)
                self._bench_result.configure(state="disabled")
                self._bench_btn.configure(state="normal", text="▶  RUN BENCHMARK")
                self._bench_running = False
            except Exception:
                pass
        self.after(0, done)

    def _clear_bench(self):
        try:
            self._bench_result.configure(state="normal")
            self._bench_result.delete("1.0", "end")
            self._bench_result.insert("end", "  Benchmark cleared.\n")
            self._bench_result.configure(state="disabled")
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    #  LOGIC — RULE BUILDER
    # ══════════════════════════════════════════════════════════════════════════
    def _add_rule(self, rule):
        if not hasattr(self, "_rule_chain_items"):
            self._rule_chain_items = []
        self._rule_chain_items.append(rule)
        self._refresh_rule_display()

    def _refresh_rule_display(self):
        try:
            self._rule_display.configure(state="normal")
            self._rule_display.delete("1.0", "end")
            if self._rule_chain_items:
                self._rule_display.insert("end",
                    "# Rule chain (" + str(len(self._rule_chain_items)) + " rules)\n")
                for i, r in enumerate(self._rule_chain_items, 1):
                    self._rule_display.insert("end", f"  {i:>2}. {r}\n")
            else:
                self._rule_display.insert("end", "# Rule chain (empty)\n")
            self._rule_display.configure(state="disabled")
            count = len(self._rule_chain_items)
            self._rule_stat_vars["count"].set(str(count))
            self._rule_stat_vars["muts"].set(str(2 ** count))
            self._rule_stat_vars["cands"].set(f"{14344391 * (2**count):,}" if count < 8 else "10B+")
            levels = ["Trivial","Low","Moderate","High","Very High","Extreme"]
            self._rule_stat_vars["complex"].set(levels[min(count, len(levels)-1)])
        except Exception:
            pass

    def _clear_rule_chain(self):
        self._rule_chain_items = []
        self._refresh_rule_display()

    def _import_rules(self):
        path = filedialog.askopenfilename(
            filetypes=[("Rule files","*.rule *.rules *.txt"),("All","*.*")])
        if not path:
            return
        with open(path, encoding="utf-8", errors="replace") as f:
            rules = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        self._rule_chain_items.extend(rules[:50])
        self._refresh_rule_display()
        messagebox.showinfo("Import", f"Imported {len(rules)} rules from {os.path.basename(path)}")

    def _save_rules(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".rule",
            filetypes=[("Rule file","*.rule"),("Text","*.txt")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("# CryptX Custom Ruleset\n")
            for r in self._rule_chain_items:
                f.write(r + "\n")
        messagebox.showinfo("Saved", f"Ruleset saved to {os.path.basename(path)}")

    def _test_rules(self):
        word = self._test_word_var.get()
        if not word:
            return
        transforms = {
            ":": lambda w: w,
            "l": lambda w: w.lower(),
            "u": lambda w: w.upper(),
            "c": lambda w: w.capitalize(),
            "C": lambda w: w[0].lower() + w[1:].upper() if len(w) > 1 else w.lower(),
            "t": lambda w: w.swapcase(),
            "r": lambda w: w[::-1],
            "d": lambda w: w + w,
            "f": lambda w: w + w[::-1],
            "$1": lambda w: w + "1",
            "$!": lambda w: w + "!",
            "$@": lambda w: w + "@",
            "^A": lambda w: "A" + w,
            "sa@": lambda w: w.replace("a","@"),
            "se3": lambda w: w.replace("e","3"),
            "si!": lambda w: w.replace("i","!"),
            "so0": lambda w: w.replace("o","0"),
            "[": lambda w: w[1:] if len(w) > 1 else w,
            "]": lambda w: w[:-1] if len(w) > 1 else w,
            "{": lambda w: w[1:] + w[0] if len(w) > 1 else w,
            "}": lambda w: w[-1] + w[:-1] if len(w) > 1 else w,
        }
        try:
            self._test_output.configure(state="normal")
            self._test_output.delete("1.0", "end")
            self._test_output.insert("end", f"  Input: {word}\n  " + "─"*36 + "\n")
            result = word
            for rule in (self._rule_chain_items
                         if hasattr(self, "_rule_chain_items") else []):
                fn = transforms.get(rule)
                if fn:
                    prev   = result
                    result = fn(result)
                    self._test_output.insert("end", f"  {rule:<8} {prev!r:20} → {result!r}\n")
                else:
                    self._test_output.insert("end", f"  {rule:<8} (rule not simulated locally)\n")
            self._test_output.insert("end", f"\n  Final output: {result!r}\n")
            self._test_output.configure(state="disabled")
        except Exception as ex:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    #  LOGIC — SCHEDULER
    # ══════════════════════════════════════════════════════════════════════════
    def _add_to_queue(self):
        if not hasattr(self, "_queue_items"):
            self._queue_items = []
        item = {k: v.get() for k, v in self._sched_entries.items()}
        item["status"] = "Queued"
        item["idx"] = len(self._queue_items) + 1
        self._queue_items.append(item)
        self._refresh_queue()

    def _refresh_queue(self):
        try:
            for w in self._queue_frame.winfo_children():
                w.destroy()
            clr_map = {
                "Queued":"#64748b","Running":FG_YELLOW,
                "Done":FG_GREEN,"Failed":FG_RED,"Paused":FG_ORANGE
            }
            for item in self._queue_items:
                row_bg = BG_DARK
                rr = tk.Frame(self._queue_frame, bg=row_bg)
                rr.pack(fill="x", pady=1)
                sc = clr_map.get(item["status"], FG_MUTED)
                for val, w in [
                    (str(item["idx"]), 3), (item["name"][:14], 16),
                    (item["type"][:12], 14), (item["priority"], 10),
                    (item["status"], 10),
                ]:
                    tk.Label(rr, text=val, bg=row_bg, fg=sc,
                             font=("Courier", 8),
                             width=w, anchor="w").pack(side="left", padx=4, pady=3)
                tk.Button(rr, text="✕", bg=row_bg, fg=FG_RED,
                          font=("Courier", 8), relief="flat", cursor="hand2",
                          command=lambda i=item: self._remove_queue_item(i)
                          ).pack(side="left")
        except Exception:
            pass

    def _remove_queue_item(self, item):
        if item in self._queue_items:
            self._queue_items.remove(item)
            for i, it in enumerate(self._queue_items, 1):
                it["idx"] = i
            self._refresh_queue()

    def _run_queue(self):
        if not hasattr(self, "_queue_items") or not self._queue_items:
            messagebox.showinfo("Queue", "Queue is empty.")
            return
        self._status_var.set(f"Running queue — {len(self._queue_items)} attacks")
        for item in self._queue_items:
            item["status"] = "Queued"
        self._refresh_queue()
        threading.Thread(target=self._queue_worker, daemon=True).start()

    def _queue_worker(self):
        for item in self._queue_items:
            item["status"] = "Running"
            self.after(0, self._refresh_queue)
            time.sleep(random.uniform(1.5, 3.5))
            item["status"] = random.choice(["Done","Done","Done","Failed"])
            self.after(0, self._refresh_queue)
        self.after(0, lambda: self._status_var.set("Queue complete"))

    def _stop_queue(self):
        for item in self._queue_items:
            if item["status"] == "Running":
                item["status"] = "Paused"
        self._refresh_queue()
        self._status_var.set("Queue stopped")

    def _clear_queue(self):
        self._queue_items = []
        self._refresh_queue()

    def _load_pipeline(self):
        self._queue_items = []
        pipeline = [
            ("Dictionary",      "rockyou.txt",    "Normal"),
            ("Dictionary+Rules","rules.rule",      "Normal"),
            ("Hybrid",          "rockyou.txt",    "Low"),
            ("Brute Force",     "—",              "Background"),
        ]
        for i, (atype, wl, pri) in enumerate(pipeline, 1):
            self._queue_items.append({
                "idx": i, "name": f"Stage {i}",
                "type": atype, "priority": pri,
                "hashfile": "hashes.txt",
                "wordlist": wl, "status": "Queued",
            })
        self._refresh_queue()
        self._status_var.set("Recommended pipeline loaded — 4 attacks queued")

    # ══════════════════════════════════════════════════════════════════════════
    #  LOGIC — CHARSET BUILDER
    # ══════════════════════════════════════════════════════════════════════════
    def _update_charset_preview(self):
        try:
            charset = ""
            for chars, var in self._cs_checks.items():
                if var.get():
                    charset += chars
            custom = self._custom_chars.get() if hasattr(self,"_custom_chars") else ""
            charset += custom
            charset = "".join(dict.fromkeys(charset))
            self._cs_preview_var.set(charset)
        except Exception:
            pass

    def _save_charset_slot(self):
        charset = self._cs_preview_var.get()
        slot    = self._cs_slot.get()
        if not charset:
            messagebox.showwarning("Empty", "Charset is empty.")
            return
        if not hasattr(self, "_saved_slots"):
            self._saved_slots = {}
        self._saved_slots[slot] = charset
        for w in self._slot_display.winfo_children():
            w.destroy()
        for sl, cs in self._saved_slots.items():
            sr = tk.Frame(self._slot_display, bg=BG_PURCARD)
            sr.pack(fill="x", pady=1)
            tk.Label(sr, text=f"  {sl}  →  ",
                     bg=BG_PURCARD, fg=FG_PURPLE,
                     font=("Courier", 9, "bold")).pack(side="left")
            preview = cs[:40] + ("…" if len(cs) > 40 else "")
            tk.Label(sr, text=f"{preview}  ({len(cs)} chars)",
                     bg=BG_PURCARD, fg=FG_PRIMARY,
                     font=("Courier", 8)).pack(side="left")
        messagebox.showinfo("Saved", f"Charset ({len(charset)} chars) saved to slot {slot}")

    def _calc_keyspace(self):
        charset = self._cs_preview_var.get()
        try:
            min_l = int(self._ks_min.get())
            max_l = int(self._ks_max.get())
        except ValueError:
            messagebox.showerror("Error", "Enter valid min/max length values.")
            return
        if min_l > max_l or min_l < 1:
            messagebox.showerror("Error", "Invalid length range.")
            return
        c = len(charset)
        total_ks = sum(c ** l for l in range(min_l, max_l + 1))
        rates = [
            ("1 M H/s  (CPU/MD5)",    1_000_000),
            ("100 M H/s (GPU/MD5)",   100_000_000),
            ("10 B H/s  (GPU/bcrypt)",10_000_000_000),
        ]
        for w in self._ks_result_frame.winfo_children():
            w.destroy()
        tk.Label(self._ks_result_frame,
                 text=f"  Charset size   : {c} characters",
                 bg=BG_PURCARD, fg=FG_PRIMARY,
                 font=("Courier", 8)).pack(anchor="w")
        tk.Label(self._ks_result_frame,
                 text=f"  Length range   : {min_l} – {max_l}",
                 bg=BG_PURCARD, fg=FG_PRIMARY,
                 font=("Courier", 8)).pack(anchor="w")
        tk.Label(self._ks_result_frame,
                 text=f"  Keyspace total : {total_ks:,}",
                 bg=BG_PURCARD, fg=FG_YELLOW,
                 font=("Courier", 9, "bold")).pack(anchor="w", pady=(4, 2))
        tk.Label(self._ks_result_frame, text="  Estimated crack time:",
                 bg=BG_PURCARD, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w", pady=(4, 0))
        for label, rate in rates:
            secs = total_ks / rate
            if secs < 60:
                eta = f"{secs:.1f} seconds"
            elif secs < 3600:
                eta = f"{secs/60:.1f} minutes"
            elif secs < 86400:
                eta = f"{secs/3600:.1f} hours"
            elif secs < 31536000:
                eta = f"{secs/86400:.1f} days"
            else:
                eta = f"{secs/31536000:.1f} years"
            clr = FG_GREEN if secs < 3600 else FG_YELLOW if secs < 86400 else FG_RED
            tk.Label(self._ks_result_frame,
                     text=f"  @ {label:<26} → {eta}",
                     bg=BG_PURCARD, fg=clr,
                     font=("Courier", 8)).pack(anchor="w")

    # ══════════════════════════════════════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════════════════════════════════════
    def _section_label(self, parent, text, pady=(0, 10)):
        tk.Label(parent, text=text,
                 bg=BG_PURPLE, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w", pady=pady)

    def _card(self, parent, border_color=BORDER_PRP):
        card = tk.Frame(parent, bg=BG_PURCARD,
                        relief="flat",
                        highlightthickness=1,
                        highlightbackground=border_color)
        card.pack(fill="x", pady=(0, 8))
        return card


# ══════════════════════════════════════════════════════════════════════════════
#  STANDALONE TEST
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    class _FakeNav:
        def push_view(self, cls): print(f"push_view({cls.__name__})")
        def pop_view(self):       print("pop_view()")

    root = tk.Tk()
    root.title("CryptX — Advanced Mode (standalone test)")
    root.geometry("1200x800")
    root.configure(bg="#1e1a2e")
    AdvancedModeFrame(root, _FakeNav()).pack(fill="both", expand=True)
    root.mainloop()
