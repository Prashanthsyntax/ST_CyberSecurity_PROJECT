import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import json
import os
import re
import math
from collections import Counter
from datetime import datetime

BG_DARK   = "#1e1e2e"
BG_CARD   = "#2a2a3e"
BG_ACCENT = "#1e3a4a"
BG_EDITOR = "#0f0f1e"
FG_PRIMARY= "#cbd5e1"
FG_MUTED  = "#64748b"
FG_BLUE   = "#7dd3fc"
FG_GREEN  = "#22c55e"
FG_RED    = "#ef4444"
FG_ORANGE = "#f97316"
FG_PURPLE = "#a78bfa"
FG_AMBER  = "#fbbf24"
BORDER    = "#3a3a50"
BTN_BLUE  = "#185FA5"

STRENGTH_COLORS = {
    "Very Weak":   FG_RED,
    "Weak":        FG_ORANGE,
    "Medium":      FG_AMBER,
    "Strong":      FG_GREEN,
    "Very Strong": FG_BLUE,
}


def score_password(pwd: str) -> tuple[str, int]:
    """
    Score a password 0-100 and return
    (strength_label, score).
    """
    if not pwd or pwd == "—":
        return "—", 0

    score = 0
    length = len(pwd)

    # Length scoring
    if length >= 16:  score += 30
    elif length >= 12: score += 22
    elif length >= 8:  score += 14
    elif length >= 6:  score += 8
    else:              score += 2

    # Character variety
    if re.search(r"[a-z]", pwd): score += 10
    if re.search(r"[A-Z]", pwd): score += 10
    if re.search(r"\d",    pwd): score += 10
    if re.search(r"[!@#$%^&*()_+=\-\[\]{};':\",.<>?/\\|`~]",
                 pwd):            score += 15

    # Pattern penalties
    if re.match(r"^[a-z]+$", pwd):    score -= 10
    if re.match(r"^\d+$",    pwd):    score -= 15
    if pwd.lower() in {
        "password","123456","qwerty",
        "abc123","letmein","admin",
        "welcome","monkey","dragon",
        "test","hello","iloveyou",
    }:
        score -= 20

    # Sequential chars penalty
    seqs = ["0123456789","abcdefghijklmnopqrstuvwxyz",
            "qwertyuiop","asdfghjkl","zxcvbnm"]
    for seq in seqs:
        for i in range(len(seq)-2):
            if seq[i:i+3] in pwd.lower():
                score -= 5
                break

    score = max(0, min(100, score))

    if score < 20:   label = "Very Weak"
    elif score < 40: label = "Weak"
    elif score < 60: label = "Medium"
    elif score < 80: label = "Strong"
    else:            label = "Very Strong"

    return label, score


class AnalyticsFrame(tk.Frame):
    def __init__(self, parent, nav=None, results: list = None):
        super().__init__(parent, bg=BG_DARK)
        self.nav = nav

        # Accept results passed directly
        # or loaded from file
        self.results = results or []
        self.analysed = []

        self._build_titlebar()
        self._build_input_row()
        self._build_summary_cards()
        self._build_charts_area()
        self._build_top_passwords()
        self._build_buttons()
        self._build_statusbar()

        # Auto-analyse if results passed in
        if self.results:
            self.after(
                200, self._run_analysis)

    # ── Title bar ────────────────────────────────────
    def _build_titlebar(self):
        bar = tk.Frame(self, bg=BG_CARD,
                       height=36)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        for color in ["#ff5f57","#febc2e",
                      "#28c840"]:
            tk.Label(bar, bg=color,
                     width=2).pack(
                side="left",
                padx=(8 if color == "#ff5f57"
                      else 4, 0),
                pady=10)
        tk.Label(bar,
                 text="Window 7 — Password "
                      "Strength Analytics Dashboard",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 10)).pack(
                 side="left", padx=12)

    # ── Input row ─────────────────────────────────────
    def _build_input_row(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16,
                   pady=(10, 0))

        tk.Label(frame,
                 text="LOAD RESULTS — browse a "
                      "CSV exported from Hash "
                      "Cracker or Hybrid Attack",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(
                 anchor="w", pady=(0, 5))

        row = tk.Frame(frame, bg=BG_DARK)
        row.pack(fill="x")

        self.file_var = tk.StringVar()
        tk.Entry(row,
                 textvariable=self.file_var,
                 bg=BG_EDITOR, fg=FG_PRIMARY,
                 insertbackground=FG_BLUE,
                 relief="flat",
                 highlightthickness=1,
                 highlightbackground=BORDER,
                 font=("Courier", 10),
                 width=55).pack(
                 side="left", ipady=5,
                 padx=(0, 8))

        tk.Button(row, text="Browse CSV",
                  bg=BG_CARD, fg=FG_BLUE,
                  relief="flat",
                  font=("Courier", 9),
                  activebackground=BG_ACCENT,
                  cursor="hand2",
                  padx=10, pady=3,
                  command=self._browse_csv
                  ).pack(side="left",
                         padx=(0, 8))

        tk.Button(row,
                  text="▶  Analyse",
                  bg=BTN_BLUE, fg="#e0f0ff",
                  relief="flat",
                  font=("Courier", 10, "bold"),
                  activebackground="#1a6fbf",
                  cursor="hand2",
                  padx=12, pady=3,
                  command=self._load_and_analyse
                  ).pack(side="left")

    def _browse_csv(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")])
        if path:
            self.file_var.set(path)

    # ── Summary stat cards ────────────────────────────
    def _build_summary_cards(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16,
                   pady=(10, 0))

        self.summary_vars = {
            "Total":      tk.StringVar(value="0"),
            "Cracked":    tk.StringVar(value="0"),
            "Not cracked":tk.StringVar(value="0"),
            "Crack rate": tk.StringVar(value="0%"),
            "Avg score":  tk.StringVar(value="0"),
            "Avg length": tk.StringVar(value="0"),
        }
        colors = {
            "Total":       FG_BLUE,
            "Cracked":     FG_GREEN,
            "Not cracked": FG_RED,
            "Crack rate":  FG_AMBER,
            "Avg score":   FG_PURPLE,
            "Avg length":  FG_PRIMARY,
        }
        for label, var in \
                self.summary_vars.items():
            card = tk.Frame(
                frame, bg=BG_CARD,
                highlightthickness=1,
                highlightbackground=BORDER)
            card.pack(side="left",
                      expand=True, fill="x",
                      padx=3)
            tk.Label(card,
                     textvariable=var,
                     bg=BG_CARD,
                     fg=colors[label],
                     font=("Courier",
                           14, "bold")
                     ).pack(pady=(8, 2))
            tk.Label(card, text=label,
                     bg=BG_CARD, fg=FG_MUTED,
                     font=("Courier", 8)
                     ).pack(pady=(0, 8))

    # ── Charts area ───────────────────────────────────
    def _build_charts_area(self):
        outer = tk.Frame(self, bg=BG_DARK)
        outer.pack(fill="x", padx=16,
                   pady=(10, 0))
        outer.columnconfigure(0, weight=1)
        outer.columnconfigure(1, weight=1)
        outer.columnconfigure(2, weight=1)

        # Strength distribution
        sc = tk.Frame(outer, bg=BG_CARD,
                      highlightthickness=1,
                      highlightbackground=BORDER)
        sc.grid(row=0, column=0,
                sticky="nsew", padx=(0, 5))
        tk.Label(sc,
                 text="STRENGTH DISTRIBUTION",
                 bg=BG_CARD, fg=FG_BLUE,
                 font=("Courier", 8)).pack(
                 anchor="w", padx=10,
                 pady=(8, 4))

        self.strength_canvas = tk.Canvas(
            sc, bg=BG_CARD,
            highlightthickness=0,
            height=140)
        self.strength_canvas.pack(
            fill="x", padx=10, pady=(0, 8))

        # Algorithm breakdown
        ac = tk.Frame(outer, bg=BG_CARD,
                      highlightthickness=1,
                      highlightbackground=BORDER)
        ac.grid(row=0, column=1,
                sticky="nsew", padx=5)
        tk.Label(ac,
                 text="ALGORITHM BREAKDOWN",
                 bg=BG_CARD, fg=FG_PURPLE,
                 font=("Courier", 8)).pack(
                 anchor="w", padx=10,
                 pady=(8, 4))

        self.algo_canvas = tk.Canvas(
            ac, bg=BG_CARD,
            highlightthickness=0,
            height=140)
        self.algo_canvas.pack(
            fill="x", padx=10, pady=(0, 8))

        # Length distribution
        lc = tk.Frame(outer, bg=BG_CARD,
                      highlightthickness=1,
                      highlightbackground=BORDER)
        lc.grid(row=0, column=2,
                sticky="nsew", padx=(5, 0))
        tk.Label(lc,
                 text="LENGTH DISTRIBUTION",
                 bg=BG_CARD, fg=FG_AMBER,
                 font=("Courier", 8)).pack(
                 anchor="w", padx=10,
                 pady=(8, 4))

        self.length_canvas = tk.Canvas(
            lc, bg=BG_CARD,
            highlightthickness=0,
            height=140)
        self.length_canvas.pack(
            fill="x", padx=10, pady=(0, 8))

    # ── Top passwords + password tester ───────────────
    def _build_top_passwords(self):
        outer = tk.Frame(self, bg=BG_DARK)
        outer.pack(fill="x", padx=16,
                   pady=(10, 0))
        outer.columnconfigure(0, weight=1)
        outer.columnconfigure(1, weight=1)

        # Top cracked passwords
        left = tk.Frame(outer, bg=BG_CARD,
                        highlightthickness=1,
                        highlightbackground=BORDER)
        left.grid(row=0, column=0,
                  sticky="nsew",
                  padx=(0, 5))

        tk.Label(left,
                 text="TOP CRACKED PASSWORDS",
                 bg=BG_CARD, fg=FG_BLUE,
                 font=("Courier", 8)).pack(
                 anchor="w", padx=10,
                 pady=(8, 4))

        cols = ("rank", "password",
                "strength", "algorithm",
                "score")
        style = ttk.Style()
        style.configure(
            "Analytics.Treeview",
            background=BG_CARD,
            foreground=FG_PRIMARY,
            fieldbackground=BG_CARD,
            rowheight=24,
            font=("Courier", 9))
        style.configure(
            "Analytics.Treeview.Heading",
            background=BG_DARK,
            foreground=FG_MUTED,
            font=("Courier", 8))
        style.map(
            "Analytics.Treeview",
            background=[
                ("selected", BG_ACCENT)])

        self.top_tree = ttk.Treeview(
            left,
            columns=cols,
            show="headings",
            style="Analytics.Treeview",
            height=6)

        for col, txt, w in [
            ("rank",      "#",          30),
            ("password",  "Password",  140),
            ("strength",  "Strength",   80),
            ("algorithm", "Algorithm",  80),
            ("score",     "Score",      50),
        ]:
            self.top_tree.heading(col, text=txt)
            self.top_tree.column(
                col, width=w, anchor="w")

        self.top_tree.tag_configure(
            "vweak", foreground=FG_RED)
        self.top_tree.tag_configure(
            "weak",  foreground=FG_ORANGE)
        self.top_tree.tag_configure(
            "med",   foreground=FG_AMBER)
        self.top_tree.tag_configure(
            "strong",foreground=FG_GREEN)
        self.top_tree.tag_configure(
            "vstrong",foreground=FG_BLUE)

        self.top_tree.pack(
            fill="x", padx=6, pady=(0, 8))

        # Password strength tester
        right = tk.Frame(outer, bg=BG_CARD,
                         highlightthickness=1,
                         highlightbackground=BORDER)
        right.grid(row=0, column=1,
                   sticky="nsew",
                   padx=(5, 0))

        tk.Label(right,
                 text="LIVE PASSWORD STRENGTH"
                      " TESTER",
                 bg=BG_CARD, fg=FG_GREEN,
                 font=("Courier", 8)).pack(
                 anchor="w", padx=10,
                 pady=(8, 4))

        inner = tk.Frame(right, bg=BG_CARD)
        inner.pack(fill="x", padx=10,
                   pady=(0, 10))

        tk.Label(inner, text="Enter password:",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 9)).pack(
                 anchor="w", pady=(0, 4))

        self.test_var = tk.StringVar()
        tk.Entry(inner,
                 textvariable=self.test_var,
                 bg=BG_EDITOR, fg=FG_GREEN,
                 insertbackground=FG_GREEN,
                 relief="flat",
                 highlightthickness=1,
                 highlightbackground=BORDER,
                 font=("Courier", 12),
                 show="*").pack(
                 fill="x", ipady=8)
        self.test_var.trace_add(
            "write",
            lambda *a: self._test_password())

        # Show/hide toggle
        self.show_pwd = tk.BooleanVar(
            value=False)
        tk.Checkbutton(
            inner, text="Show password",
            variable=self.show_pwd,
            bg=BG_CARD, fg=FG_MUTED,
            selectcolor=BG_ACCENT,
            activebackground=BG_CARD,
            font=("Courier", 8),
            command=self._toggle_show
        ).pack(anchor="w", pady=(4, 0))

        # Strength meter
        self.strength_label = tk.Label(
            inner, text="—",
            bg=BG_CARD, fg=FG_MUTED,
            font=("Courier", 14, "bold"))
        self.strength_label.pack(
            pady=(10, 4))

        self.meter_canvas = tk.Canvas(
            inner, bg=BG_CARD,
            highlightthickness=0,
            height=18)
        self.meter_canvas.pack(fill="x")

        # Score details
        self.score_details = tk.Label(
            inner, text="",
            bg=BG_CARD, fg=FG_MUTED,
            font=("Courier", 8),
            justify="left",
            wraplength=300)
        self.score_details.pack(
            anchor="w", pady=(8, 0))

    # ── Buttons ───────────────────────────────────────
    def _build_buttons(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16,
                   pady=(10, 6))

        self.analyse_btn = tk.Button(
            frame,
            text="▶  Analyse Results File",
            bg=BTN_BLUE, fg="#e0f0ff",
            font=("Courier", 12, "bold"),
            relief="flat",
            highlightthickness=1,
            highlightbackground=BTN_BLUE,
            activebackground="#1a6fbf",
            cursor="hand2",
            command=self._load_and_analyse)
        self.analyse_btn.pack(
            side="left", expand=True,
            fill="x", padx=(0, 6),
            ipady=10)

        tk.Button(frame,
                  text="Export PDF Report",
                  bg=BG_DARK, fg=FG_PRIMARY,
                  font=("Courier", 11),
                  relief="flat",
                  highlightthickness=1,
                  highlightbackground=BORDER,
                  activebackground=BG_CARD,
                  cursor="hand2",
                  command=self._export_pdf
                  ).pack(side="left",
                         expand=True, fill="x",
                         padx=3, ipady=10)

        tk.Button(frame,
                  text="Export CSV",
                  bg=BG_DARK, fg=FG_PRIMARY,
                  font=("Courier", 11),
                  relief="flat",
                  highlightthickness=1,
                  highlightbackground=BORDER,
                  activebackground=BG_CARD,
                  cursor="hand2",
                  command=self._export_csv
                  ).pack(side="left",
                         expand=True, fill="x",
                         padx=3, ipady=10)

        tk.Button(frame,
                  text="Clear",
                  bg=BG_DARK, fg=FG_MUTED,
                  font=("Courier", 11),
                  relief="flat",
                  highlightthickness=1,
                  highlightbackground=BORDER,
                  activebackground=BG_CARD,
                  cursor="hand2",
                  command=self._clear
                  ).pack(side="left",
                         expand=True, fill="x",
                         padx=(3, 0), ipady=10)

    # ── Status bar ────────────────────────────────────
    def _build_statusbar(self):
        bar = tk.Frame(self, bg=BG_CARD,
                       height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        tk.Label(bar, text="●",
                 bg=BG_CARD, fg=FG_GREEN,
                 font=("Courier", 10)).pack(
                 side="left", padx=(12, 4))

        self.status_var = tk.StringVar(
            value="Ready · Load a CSV "
                  "results file to analyse")
        tk.Label(bar,
                 textvariable=self.status_var,
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 9)).pack(
                 side="left")

        tk.Label(bar,
                 text="Strength · Algorithm"
                      " · Length analytics",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 9)).pack(
                 side="right", padx=12)

    def _set_status(self, msg):
        self.status_var.set(msg)

    # ── Load and analyse ──────────────────────────────
    def _load_and_analyse(self):
        path = self.file_var.get().strip()
        if not path and not self.results:
            messagebox.showwarning(
                "No File",
                "Browse a CSV results file "
                "or run a crack session first.")
            return
        if path:
            self._load_csv(path)
        self._run_analysis()

    def _load_csv(self, path):
        try:
            self.results = []
            with open(path, "r",
                      encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.results.append(row)
            self._set_status(
                f"Loaded {len(self.results)}"
                f" rows from CSV")
        except Exception as e:
            messagebox.showerror(
                "Load Error", str(e))

    def _run_analysis(self):
        if not self.results:
            return

        self.analysed = []
        for r in self.results:
            plain  = r.get("plain", "—")
            status = r.get("status", "")
            method = r.get("method", "—")
            algo   = r.get("algo",
                           r.get("algorithm",
                                 method))

            strength, score = score_password(
                plain if status == "Cracked"
                else "")

            self.analysed.append({
                "plain":    plain,
                "status":   status,
                "algo":     algo,
                "strength": strength,
                "score":    score,
                "length":   len(plain)
                            if plain != "—"
                            else 0,
            })

        self._update_summary()
        self._draw_strength_chart()
        self._draw_algo_chart()
        self._draw_length_chart()
        self._populate_top_passwords()
        self._set_status(
            f"Analysed {len(self.analysed)}"
            f" passwords · "
            f"{sum(1 for a in self.analysed if a['status']=='Cracked')}"
            f" cracked")

    # ── Update summary cards ──────────────────────────
    def _update_summary(self):
        total   = len(self.analysed)
        cracked = sum(
            1 for a in self.analysed
            if a["status"] == "Cracked")
        not_c   = total - cracked
        rate    = round(
            (cracked / total * 100), 1) \
            if total else 0

        scores = [
            a["score"] for a in self.analysed
            if a["score"] > 0]
        avg_score = round(
            sum(scores) / len(scores), 1) \
            if scores else 0

        lengths = [
            a["length"] for a in self.analysed
            if a["length"] > 0]
        avg_len = round(
            sum(lengths) / len(lengths), 1) \
            if lengths else 0

        self.summary_vars["Total"].set(
            str(total))
        self.summary_vars["Cracked"].set(
            str(cracked))
        self.summary_vars["Not cracked"].set(
            str(not_c))
        self.summary_vars["Crack rate"].set(
            f"{rate}%")
        self.summary_vars["Avg score"].set(
            str(avg_score))
        self.summary_vars["Avg length"].set(
            str(avg_len))

    # ── Draw bar chart on canvas ──────────────────────
    def _draw_bar_chart(self, canvas,
                        data: dict,
                        colors: dict,
                        max_val: int):
        canvas.delete("all")
        canvas.update_idletasks()
        w = canvas.winfo_width() or 300
        h = 140
        bar_h    = 16
        gap      = 8
        label_w  = 75
        val_w    = 35
        bar_area = w - label_w - val_w - 10

        for i, (label, val) in \
                enumerate(data.items()):
            y = i * (bar_h + gap) + 4
            color = colors.get(label, FG_MUTED)
            pct = (val / max_val) \
                  if max_val > 0 else 0
            fill_w = int(bar_area * pct)

            # Label
            canvas.create_text(
                label_w - 4, y + bar_h // 2,
                text=label,
                anchor="e",
                fill=FG_MUTED,
                font=("Courier", 8))

            # Track
            canvas.create_rectangle(
                label_w, y,
                label_w + bar_area,
                y + bar_h,
                fill=BG_EDITOR,
                outline="")

            # Fill
            if fill_w > 0:
                canvas.create_rectangle(
                    label_w, y,
                    label_w + fill_w,
                    y + bar_h,
                    fill=color,
                    outline="")

            # Value
            canvas.create_text(
                label_w + bar_area + 4,
                y + bar_h // 2,
                text=str(val),
                anchor="w",
                fill=color,
                font=("Courier", 8))

    def _draw_strength_chart(self):
        counter = Counter(
            a["strength"]
            for a in self.analysed
            if a["status"] == "Cracked"
            and a["strength"] != "—")

        order  = ["Very Weak", "Weak",
                  "Medium", "Strong",
                  "Very Strong"]
        data   = {k: counter.get(k, 0)
                  for k in order}
        colors = STRENGTH_COLORS
        max_v  = max(data.values()) \
                 if data.values() else 1

        self.after(100, lambda:
            self._draw_bar_chart(
                self.strength_canvas,
                data, colors, max_v))

    def _draw_algo_chart(self):
        counter = Counter(
            a["algo"]
            for a in self.analysed
            if a["status"] == "Cracked")

        top4 = dict(
            counter.most_common(4))
        colors = {
            "MD5":     FG_BLUE,
            "SHA1":    FG_PURPLE,
            "SHA256":  FG_GREEN,
            "SHA512":  FG_AMBER,
            "NTLM":    FG_RED,
            "Rainbow": FG_AMBER,
            "—":       FG_MUTED,
        }
        max_v = max(top4.values()) \
                if top4 else 1

        self.after(100, lambda:
            self._draw_bar_chart(
                self.algo_canvas,
                top4, colors, max_v))

    def _draw_length_chart(self):
        buckets = {
            "1-4":   0,
            "5-6":   0,
            "7-8":   0,
            "9-10":  0,
            "11-12": 0,
            "13+":   0,
        }
        for a in self.analysed:
            l = a["length"]
            if l == 0:
                continue
            if l <= 4:   buckets["1-4"]   += 1
            elif l <= 6: buckets["5-6"]   += 1
            elif l <= 8: buckets["7-8"]   += 1
            elif l <= 10:buckets["9-10"]  += 1
            elif l <= 12:buckets["11-12"] += 1
            else:        buckets["13+"]   += 1

        colors = {k: FG_AMBER
                  for k in buckets}
        max_v = max(buckets.values()) \
                if buckets.values() else 1

        self.after(100, lambda:
            self._draw_bar_chart(
                self.length_canvas,
                buckets, colors, max_v))

    # ── Populate top passwords table ──────────────────
    def _populate_top_passwords(self):
        self.top_tree.delete(
            *self.top_tree.get_children())

        cracked = [
            a for a in self.analysed
            if a["status"] == "Cracked"
            and a["plain"] != "—"]

        # Sort by score ascending
        # (weakest first = most interesting)
        cracked.sort(
            key=lambda x: x["score"])

        tag_map = {
            "Very Weak":   "vweak",
            "Weak":        "weak",
            "Medium":      "med",
            "Strong":      "strong",
            "Very Strong": "vstrong",
        }

        for i, a in enumerate(
                cracked[:20], 1):
            tag = tag_map.get(
                a["strength"], "vweak")
            self.top_tree.insert(
                "", "end",
                values=(
                    i,
                    a["plain"][:24],
                    a["strength"],
                    a["algo"],
                    a["score"],
                ),
                tags=(tag,))

    # ── Live password tester ──────────────────────────
    def _test_password(self):
        pwd = self.test_var.get()
        if not pwd:
            self.strength_label.configure(
                text="—", fg=FG_MUTED)
            self.meter_canvas.delete("all")
            self.score_details.configure(
                text="")
            return

        label, score = score_password(pwd)
        color = STRENGTH_COLORS.get(
            label, FG_MUTED)

        self.strength_label.configure(
            text=f"{label}  ({score}/100)",
            fg=color)

        # Draw meter
        self.meter_canvas.delete("all")
        self.meter_canvas.update_idletasks()
        w = self.meter_canvas.winfo_width() \
            or 300
        fill_w = int(w * score / 100)

        # Track
        self.meter_canvas.create_rectangle(
            0, 0, w, 18,
            fill=BG_EDITOR, outline="")
        # Fill
        if fill_w > 0:
            self.meter_canvas.create_rectangle(
                0, 0, fill_w, 18,
                fill=color, outline="")

        # Details
        length = len(pwd)
        has_lower = bool(
            re.search(r"[a-z]", pwd))
        has_upper = bool(
            re.search(r"[A-Z]", pwd))
        has_digit = bool(
            re.search(r"\d", pwd))
        has_sym   = bool(re.search(
            r"[!@#$%^&*()_+=\-\[\]{};'\",.<>?/\\|`~]",
            pwd))

        checks = []
        checks.append(
            f"  Length: {length} chars"
            f"  {'✓' if length >= 8 else '✗'}")
        checks.append(
            f"  Lowercase: "
            f"{'✓' if has_lower else '✗'}")
        checks.append(
            f"  Uppercase: "
            f"{'✓' if has_upper else '✗'}")
        checks.append(
            f"  Numbers:   "
            f"{'✓' if has_digit else '✗'}")
        checks.append(
            f"  Symbols:   "
            f"{'✓' if has_sym else '✗'}")

        self.score_details.configure(
            text="\n".join(checks),
            fg=FG_MUTED)

    def _toggle_show(self):
        entry_widgets = []
        for w in self.winfo_children():
            self._find_entries(w,
                               entry_widgets)
        show = "" if self.show_pwd.get() \
               else "*"
        # Find the password test entry
        # by its variable
        for w in entry_widgets:
            try:
                if w.cget("show") in ("", "*"):
                    w.configure(show=show)
                    break
            except Exception:
                pass

    def _find_entries(self, widget, result):
        if isinstance(widget, tk.Entry):
            result.append(widget)
        for child in widget.winfo_children():
            self._find_entries(child, result)

    # ── Export PDF ────────────────────────────────────
    def _export_pdf(self):
        if not self.analysed:
            messagebox.showwarning(
                "No Data",
                "Analyse results first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text report", "*.txt"),
                ("All files", "*.*")],
            initialfile="analytics_report.txt")
        if not path:
            return

        total   = len(self.analysed)
        cracked = sum(
            1 for a in self.analysed
            if a["status"] == "Cracked")
        rate    = round(
            cracked / total * 100, 1) \
            if total else 0

        strength_counts = Counter(
            a["strength"]
            for a in self.analysed
            if a["status"] == "Cracked")
        algo_counts = Counter(
            a["algo"]
            for a in self.analysed
            if a["status"] == "Cracked")

        now = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S")

        lines = [
            "=" * 60,
            "  PASSWORD STRENGTH ANALYTICS REPORT",
            f"  Generated: {now}",
            "=" * 60,
            "",
            "SUMMARY",
            "-" * 40,
            f"  Total passwords:  {total}",
            f"  Cracked:          {cracked}",
            f"  Not cracked:      {total-cracked}",
            f"  Crack rate:       {rate}%",
            "",
            "STRENGTH DISTRIBUTION",
            "-" * 40,
        ]
        for s in ["Very Weak","Weak","Medium",
                  "Strong","Very Strong"]:
            c = strength_counts.get(s, 0)
            pct = round(c/cracked*100,1) \
                  if cracked else 0
            lines.append(
                f"  {s:<12}  {c:>5}  "
                f"({pct}%)")

        lines += [
            "",
            "ALGORITHM BREAKDOWN",
            "-" * 40,
        ]
        for algo, cnt in \
                algo_counts.most_common():
            pct = round(
                cnt/cracked*100,1) \
                if cracked else 0
            lines.append(
                f"  {algo:<10}  {cnt:>5}  "
                f"({pct}%)")

        lines += [
            "",
            "TOP 20 WEAKEST CRACKED PASSWORDS",
            "-" * 40,
        ]
        weak = sorted(
            [a for a in self.analysed
             if a["status"] == "Cracked"
             and a["plain"] != "—"],
            key=lambda x: x["score"])[:20]
        for i, a in enumerate(weak, 1):
            lines.append(
                f"  {i:>2}. {a['plain']:<20}"
                f"  {a['strength']:<12}"
                f"  score:{a['score']}")

        lines += ["", "=" * 60,
                  "End of report"]

        with open(path, "w",
                  encoding="utf-8") as f:
            f.write("\n".join(lines))

        messagebox.showinfo(
            "Report Saved",
            f"Report saved to:\n{path}")

    # ── Export CSV ────────────────────────────────────
    def _export_csv(self):
        if not self.analysed:
            messagebox.showwarning(
                "No Data",
                "Analyse results first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv")],
            initialfile="analytics.csv")
        if not path:
            return
        with open(path, "w", newline="",
                  encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=[
                    "plain", "status",
                    "algo", "strength",
                    "score", "length"])
            writer.writeheader()
            writer.writerows(self.analysed)
        messagebox.showinfo(
            "Exported",
            f"Analytics saved to:\n{path}")

    # ── Clear ─────────────────────────────────────────
    def _clear(self):
        self.results  = []
        self.analysed = []
        for v in self.summary_vars.values():
            v.set("0")
        self.top_tree.delete(
            *self.top_tree.get_children())
        self.strength_canvas.delete("all")
        self.algo_canvas.delete("all")
        self.length_canvas.delete("all")
        self.test_var.set("")
        self.strength_label.configure(
            text="—", fg=FG_MUTED)
        self.score_details.configure(text="")
        self.file_var.set("")
        self._set_status("Cleared · Ready")