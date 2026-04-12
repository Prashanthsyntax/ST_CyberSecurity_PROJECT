import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import hashlib
import json
import os
import time

BG_DARK   = "#1e1e2e"
BG_CARD   = "#2a2a3e"
BG_ACCENT = "#1e3a4a"
BG_EDITOR = "#0f0f1e"
FG_PRIMARY= "#cbd5e1"
FG_MUTED  = "#64748b"
FG_BLUE   = "#7dd3fc"
FG_GREEN  = "#22c55e"
FG_RED    = "#ef4444"
FG_PURPLE = "#a78bfa"
FG_AMBER  = "#fbbf24"
BORDER    = "#3a3a50"
BTN_BLUE  = "#185FA5"

DATA_DIR = os.path.join(
    os.path.dirname(__file__),
    "..", "data")

ALGORITHMS = {
    "MD5":    lambda w: hashlib.md5(
        w.encode("latin-1")).hexdigest(),
    "SHA1":   lambda w: hashlib.sha1(
        w.encode("latin-1")).hexdigest(),
    "SHA256": lambda w: hashlib.sha256(
        w.encode("latin-1")).hexdigest(),
    "NTLM":   lambda w: hashlib.new(
        "md4", w.encode("utf-16-le")).hexdigest(),
}


class RainbowTableFrame(tk.Frame):
    def __init__(self, parent, nav=None):
        super().__init__(parent, bg=BG_DARK)
        self.nav = nav

        # Combined table: hash → plaintext
        self.combined_table = {}
        # List of loaded table info dicts
        self.loaded_tables  = []
        self.running        = False
        self.selected_algo  = tk.StringVar(
            value="MD5")
        self.wordlist_var   = tk.StringVar()
        self.output_name    = tk.StringVar(
            value="my_rainbow_table.json")
        self.lookup_var     = tk.StringVar()

        self._build_titlebar()
        self._build_tables_section()
        self._build_lookup_bar()
        self._build_stats_bar()
        self._build_progress()
        self._build_buttons()
        self._build_statusbar()
        self._build_log()

        # Auto-load default rainbow table
        self._auto_load_default()

    # ── Title bar ────────────────────────────────────
    def _build_titlebar(self):
        bar = tk.Frame(self, bg=BG_CARD,
                       height=36)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        for color in ["#ff5f57", "#febc2e", "#28c840"]:
            tk.Label(bar, bg=color, width=2).pack(
                side="left",
                padx=(8 if color == "#ff5f57"
                      else 4, 0),
                pady=10)
        tk.Label(bar,
                 text="Window 6 — Rainbow Table Manager",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 10)).pack(
                 side="left", padx=12)

    # ── Top 2-column section ──────────────────────────
    def _build_tables_section(self):
        outer = tk.Frame(self, bg=BG_DARK)
        outer.pack(fill="x", padx=16, pady=(12, 0))
        outer.columnconfigure(0, weight=1)
        outer.columnconfigure(1, weight=1)

        self._build_loaded_tables(outer)
        self._build_builder(outer)

    # ── Left: loaded tables list ──────────────────────
    def _build_loaded_tables(self, parent):
        frame = tk.Frame(parent, bg=BG_DARK)
        frame.grid(row=0, column=0,
                   sticky="nsew", padx=(0, 8))

        tk.Label(frame,
                 text="LOADED RAINBOW TABLES",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(
                 anchor="w", pady=(0, 5))

        card = tk.Frame(frame, bg=BG_CARD,
                        highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill="both", expand=True)

        # Table header
        hdr = tk.Frame(card, bg="#1a1a2e")
        hdr.pack(fill="x", padx=8, pady=(6, 2))
        for txt, w in [
            ("File name",  22),
            ("Algorithm",  10),
            ("Entries",     8),
            ("Size",        8),
        ]:
            tk.Label(hdr, text=txt,
                     bg="#1a1a2e", fg=FG_MUTED,
                     font=("Courier", 8),
                     width=w, anchor="w"
                     ).pack(side="left", padx=2)

        # Treeview for table list
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Rainbow.Treeview",
                        background=BG_CARD,
                        foreground=FG_PRIMARY,
                        fieldbackground=BG_CARD,
                        rowheight=26,
                        font=("Courier", 9))
        style.configure(
            "Rainbow.Treeview.Heading",
            background=BG_DARK,
            foreground=FG_MUTED,
            font=("Courier", 8))
        style.map("Rainbow.Treeview",
                  background=[
                      ("selected", BG_ACCENT)])

        cols = ("file", "algo", "entries", "size")
        self.table_tree = ttk.Treeview(
            card,
            columns=cols,
            show="headings",
            style="Rainbow.Treeview",
            height=6)

        for col, txt, w in [
            ("file",    "File",      200),
            ("algo",    "Algorithm",  80),
            ("entries", "Entries",    80),
            ("size",    "Size",       70),
        ]:
            self.table_tree.heading(col, text=txt)
            self.table_tree.column(
                col, width=w, anchor="w")

        self.table_tree.pack(
            fill="both", expand=True,
            padx=4, pady=4)

        # Remove selected table button
        tk.Button(card,
                  text="Remove selected table",
                  bg=BG_DARK, fg=FG_RED,
                  relief="flat",
                  font=("Courier", 8),
                  cursor="hand2",
                  command=self._remove_table
                  ).pack(anchor="w",
                         padx=8, pady=(0, 6))

    # ── Right: builder ────────────────────────────────
    def _build_builder(self, parent):
        frame = tk.Frame(parent, bg=BG_DARK)
        frame.grid(row=0, column=1, sticky="nsew")

        tk.Label(frame,
                 text="BUILD NEW RAINBOW TABLE",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(
                 anchor="w", pady=(0, 5))

        card = tk.Frame(frame, bg=BG_CARD,
                        highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill="both", expand=True)

        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(fill="x", padx=12, pady=10)

        # Wordlist input
        tk.Label(inner, text="INPUT WORDLIST",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 8)).pack(
                 anchor="w", pady=(0, 3))

        wl_row = tk.Frame(inner, bg=BG_CARD)
        wl_row.pack(fill="x", pady=(0, 8))

        tk.Entry(wl_row,
                 textvariable=self.wordlist_var,
                 bg=BG_EDITOR, fg=FG_PRIMARY,
                 insertbackground=FG_BLUE,
                 relief="flat",
                 highlightthickness=1,
                 highlightbackground=BORDER,
                 font=("Courier", 9),
                 width=36).pack(side="left",
                                fill="x",
                                expand=True,
                                ipady=5,
                                padx=(0, 8))

        tk.Button(wl_row, text="Browse",
                  bg=BG_CARD, fg=FG_BLUE,
                  relief="flat",
                  font=("Courier", 9),
                  activebackground=BG_ACCENT,
                  cursor="hand2",
                  padx=8, pady=3,
                  command=self._browse_wordlist
                  ).pack(side="left")

        # Algorithm selector
        tk.Label(inner,
                 text="HASH ALGORITHM",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 8)).pack(
                 anchor="w", pady=(0, 4))

        algo_row = tk.Frame(inner, bg=BG_CARD)
        algo_row.pack(fill="x", pady=(0, 8))

        self.algo_btns = {}
        for algo in ALGORITHMS:
            btn = tk.Button(
                algo_row, text=algo,
                bg=BG_DARK, fg=FG_MUTED,
                relief="flat",
                font=("Courier", 9),
                highlightthickness=1,
                highlightbackground=BORDER,
                cursor="hand2",
                padx=10, pady=4,
                command=lambda a=algo:
                self._select_algo(a))
            btn.pack(side="left", padx=(0, 6))
            self.algo_btns[algo] = btn

        self._select_algo("MD5")

        # Output filename
        tk.Label(inner,
                 text="OUTPUT FILENAME",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 8)).pack(
                 anchor="w", pady=(0, 3))

        tk.Entry(inner,
                 textvariable=self.output_name,
                 bg=BG_EDITOR, fg=FG_PRIMARY,
                 insertbackground=FG_BLUE,
                 relief="flat",
                 highlightthickness=1,
                 highlightbackground=BORDER,
                 font=("Courier", 9),
                 width=36).pack(fill="x",
                                ipady=5,
                                pady=(0, 8))

        # Max entries limit
        tk.Label(inner,
                 text="MAX ENTRIES (0 = unlimited)",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 8)).pack(
                 anchor="w", pady=(0, 3))

        self.max_entries = tk.IntVar(value=0)
        tk.Spinbox(inner,
                   from_=0, to=10000000,
                   increment=10000,
                   textvariable=self.max_entries,
                   bg=BG_EDITOR, fg=FG_PRIMARY,
                   buttonbackground=BG_CARD,
                   relief="flat",
                   font=("Courier", 9),
                   width=16).pack(anchor="w",
                                  ipady=4)

    def _browse_wordlist(self):
        path = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"),
                       ("All files", "*.*")])
        if path:
            self.wordlist_var.set(path)

    def _select_algo(self, algo):
        self.selected_algo.set(algo)
        for a, btn in self.algo_btns.items():
            if a == algo:
                btn.configure(
                    bg=BG_ACCENT, fg=FG_GREEN,
                    highlightbackground=FG_GREEN)
            else:
                btn.configure(
                    bg=BG_DARK, fg=FG_MUTED,
                    highlightbackground=BORDER)

    # ── Lookup bar ────────────────────────────────────
    def _build_lookup_bar(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(12, 0))

        tk.Label(frame,
                 text="INSTANT LOOKUP — "
                      "test any hash against "
                      "all loaded tables",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(
                 anchor="w", pady=(0, 5))

        row = tk.Frame(frame, bg=BG_DARK)
        row.pack(fill="x")

        tk.Entry(row,
                 textvariable=self.lookup_var,
                 bg=BG_EDITOR, fg=FG_PRIMARY,
                 insertbackground=FG_BLUE,
                 relief="flat",
                 highlightthickness=1,
                 highlightbackground=BORDER,
                 font=("Courier", 10),
                 width=56).pack(side="left",
                                ipady=6,
                                padx=(0, 8))

        tk.Button(row, text="Lookup Hash",
                  bg=BTN_BLUE, fg="#e0f0ff",
                  relief="flat",
                  font=("Courier", 10, "bold"),
                  activebackground="#1a6fbf",
                  cursor="hand2",
                  padx=12, pady=5,
                  command=self._lookup_hash
                  ).pack(side="left", padx=(0, 8))

        self.lookup_result = tk.Label(
            row, text="",
            bg=BG_DARK, fg=FG_GREEN,
            font=("Courier", 10, "bold"))
        self.lookup_result.pack(side="left")

        # Bind Enter key
        self.bind(
            "<Return>",
            lambda e: self._lookup_hash())

    def _lookup_hash(self):
        h = self.lookup_var.get().strip().lower()
        if not h:
            return
        if not self.combined_table:
            self.lookup_result.configure(
                text="No tables loaded yet",
                fg=FG_AMBER)
            return

        start = time.perf_counter()
        result = self.combined_table.get(h)
        elapsed_ms = round(
            (time.perf_counter() - start) * 1000, 3)

        if result is not None:
            self.lookup_result.configure(
                text=f"FOUND  →  '{result}'  "
                     f"({elapsed_ms}ms)",
                fg=FG_GREEN)
            self._log(
                f"[LOOKUP] {h[:20]}...  →  "
                f"'{result}'  ({elapsed_ms}ms)",
                "found")
        else:
            self.lookup_result.configure(
                text=f"Not found in "
                     f"{len(self.combined_table):,}"
                     f" entries",
                fg=FG_RED)
            self._log(
                f"[LOOKUP] {h[:20]}...  →  "
                f"Not found",
                "notfound")

        if hasattr(self, "stat_vars"):
            self.stat_vars["Lookup ms"].set(
                f"{elapsed_ms}ms")

    # ── Stats bar ─────────────────────────────────────
    def _build_stats_bar(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(12, 0))

        self.stat_vars = {
            "Total entries": tk.StringVar(value="0"),
            "Tables loaded": tk.StringVar(value="0"),
            "Total size":    tk.StringVar(value="0 B"),
            "Algorithms":    tk.StringVar(value="—"),
            "Lookup ms":     tk.StringVar(value="—"),
        }
        colors = {
            "Total entries": FG_BLUE,
            "Tables loaded": FG_GREEN,
            "Total size":    FG_PURPLE,
            "Algorithms":    FG_AMBER,
            "Lookup ms":     FG_PRIMARY,
        }
        for label, var in self.stat_vars.items():
            card = tk.Frame(frame, bg=BG_CARD,
                            highlightthickness=1,
                            highlightbackground=BORDER)
            card.pack(side="left", expand=True,
                      fill="x", padx=4)
            tk.Label(card, textvariable=var,
                     bg=BG_CARD,
                     fg=colors[label],
                     font=("Courier", 12, "bold")
                     ).pack(pady=(8, 2))
            tk.Label(card, text=label,
                     bg=BG_CARD, fg=FG_MUTED,
                     font=("Courier", 8)
                     ).pack(pady=(0, 8))

    # ── Progress bar ──────────────────────────────────
    def _build_progress(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(8, 0))

        style = ttk.Style()
        style.configure("TProgressbar",
                        troughcolor=BG_CARD,
                        background=BTN_BLUE,
                        thickness=8)

        self.progress = ttk.Progressbar(
            frame, mode="determinate",
            maximum=100, value=0)
        self.progress.pack(fill="x")

        self.progress_label = tk.Label(
            frame,
            text="0%  ·  waiting...",
            bg=BG_DARK, fg=FG_MUTED,
            font=("Courier", 8))
        self.progress_label.pack(
            anchor="w", pady=2)

    # ── Buttons ───────────────────────────────────────
    def _build_buttons(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(10, 8))

        self.build_btn = tk.Button(
            frame,
            text="▶  Build Rainbow Table",
            bg=BTN_BLUE, fg="#e0f0ff",
            font=("Courier", 12, "bold"),
            relief="flat",
            highlightthickness=1,
            highlightbackground=BTN_BLUE,
            activebackground="#1a6fbf",
            activeforeground="#ffffff",
            cursor="hand2",
            command=self._build_table)
        self.build_btn.pack(
            side="left", expand=True,
            fill="x", padx=(0, 6), ipady=11) # increased ipady

        tk.Button(frame,
                  text="Load Table",
                  bg=BG_DARK, fg=FG_PRIMARY,
                  font=("Courier", 11),
                  relief="flat",
                  highlightthickness=1,
                  highlightbackground=BORDER,
                  activebackground=BG_CARD,
                  cursor="hand2",
                  command=self._load_table
                  ).pack(side="left", expand=True,
                         fill="x", padx=3,
                         ipady=10)

        tk.Button(frame,
                  text="Export Table",
                  bg=BG_DARK, fg=FG_PRIMARY,
                  font=("Courier", 11),
                  relief="flat",
                  highlightthickness=1,
                  highlightbackground=BORDER,
                  activebackground=BG_CARD,
                  cursor="hand2",
                  command=self._export_table
                  ).pack(side="left", expand=True,
                         fill="x", padx=3,
                         ipady=10)

        tk.Button(frame,
                  text="Clear All",
                  bg=BG_DARK, fg=FG_RED,
                  font=("Courier", 11),
                  relief="flat",
                  highlightthickness=1,
                  highlightbackground=BORDER,
                  activebackground=BG_CARD,
                  cursor="hand2",
                  command=self._clear_all
                  ).pack(side="left", expand=True,
                         fill="x", padx=(3, 0),
                         ipady=11)

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
            value="Ready · Load a table or "
                  "build a new one")
        tk.Label(bar,
                 textvariable=self.status_var,
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 9)).pack(
                 side="left")

        tk.Label(bar,
                 text="JSON format · instant lookup",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 9)).pack(
                 side="right", padx=12)

    def _set_status(self, msg):
        self.status_var.set(msg)

    # ── Log box ───────────────────────────────────────
    def _build_log(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="both", expand=True,
                   padx=16, pady=(4, 4))

        tk.Label(frame,
                 text="BUILD LOG & LOOKUP HISTORY",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(
                 anchor="w", pady=(0, 4))

        log_frame = tk.Frame(
            frame, bg=BG_CARD,
            highlightthickness=1,
            highlightbackground=BORDER)
        log_frame.pack(fill="both", expand=True)

        self.log_box = tk.Text(
            log_frame,
            bg=BG_EDITOR, fg=FG_PRIMARY,
            font=("Courier", 10),
            relief="flat",
            state="disabled",
            wrap="word",
            padx=10, pady=8)

        sb = tk.Scrollbar(
            log_frame,
            command=self.log_box.yview,
            bg=BG_CARD,
            troughcolor=BG_DARK)
        self.log_box.configure(
            yscrollcommand=sb.set)
        self.log_box.pack(side="left",
                          fill="both",
                          expand=True)
        sb.pack(side="right", fill="y")

        self.log_box.tag_configure(
            "found",    foreground=FG_GREEN)
        self.log_box.tag_configure(
            "notfound", foreground=FG_RED)
        self.log_box.tag_configure(
            "info",     foreground=FG_MUTED)
        self.log_box.tag_configure(
            "build",    foreground=FG_BLUE)
        self.log_box.tag_configure(
            "success",  foreground=FG_GREEN)

    def _log(self, msg, tag="info"):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n", tag)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # ── Auto-load default table ───────────────────────
    def _auto_load_default(self):
        default = os.path.join(
            DATA_DIR, "rainbow_table.json")
        if os.path.exists(default):
            self._load_table_from_path(default)
        else:
            self._log(
                "No default rainbow_table.json "
                "found in data/ folder.\n"
                "Build one or load an existing "
                "table.", "info")

    # ── Load table from path ──────────────────────────
    def _load_table_from_path(self, path):
        try:
            with open(path, "r",
                      encoding="utf-8") as f:
                table = json.load(f)

            # Merge into combined table
            self.combined_table.update(table)

            # Detect algorithms from hash lengths
            algos = set()
            for h in list(table.keys())[:20]:
                length = len(h)
                if length == 32:
                    algos.add("MD5")
                elif length == 40:
                    algos.add("SHA1")
                elif length == 64:
                    algos.add("SHA256")
                elif length == 128:
                    algos.add("SHA512")

            # File size
            size_bytes = os.path.getsize(path)
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes // 1024} KB"
            else:
                size_str = (
                    f"{size_bytes // (1024 * 1024)} MB")

            info = {
                "path":    path,
                "name":    os.path.basename(path),
                "entries": len(table),
                "size":    size_str,
                "algos":   ", ".join(algos)
                           if algos else "Mixed",
            }
            self.loaded_tables.append(info)

            # Add to treeview
            self.table_tree.insert(
                "", "end", values=(
                    info["name"],
                    info["algos"],
                    f"{info['entries']:,}",
                    info["size"],
                ))

            self._update_stats()
            self._log(
                f"[LOAD] {info['name']}  ·  "
                f"{info['entries']:,} entries  ·  "
                f"{info['size']}", "build")
            self._set_status(
                f"Loaded: {info['name']}  ·  "
                f"{info['entries']:,} entries")

        except Exception as e:
            self._log(
                f"[ERROR] Could not load "
                f"{path}: {e}", "notfound")

    # ── Update stats cards ────────────────────────────
    def _update_stats(self):
        total  = len(self.combined_table)
        tables = len(self.loaded_tables)

        # Total size
        total_bytes = sum(
            os.path.getsize(t["path"])
            for t in self.loaded_tables
            if os.path.exists(t["path"]))
        if total_bytes < 1024:
            size_str = f"{total_bytes} B"
        elif total_bytes < 1024 * 1024:
            size_str = f"{total_bytes // 1024} KB"
        else:
            size_str = (
                f"{total_bytes // (1024 * 1024)} MB")

        # Unique algorithms
        all_algos = set()
        for t in self.loaded_tables:
            for a in t["algos"].split(", "):
                all_algos.add(a.strip())

        self.stat_vars["Total entries"].set(
            f"{total:,}")
        self.stat_vars["Tables loaded"].set(
            str(tables))
        self.stat_vars["Total size"].set(size_str)
        self.stat_vars["Algorithms"].set(
            " · ".join(sorted(all_algos))
            if all_algos else "—")

    # ── Build new rainbow table ───────────────────────
    def _build_table(self):
        if self.running:
            return
        wf = self.wordlist_var.get().strip()
        if not wf:
            messagebox.showwarning(
                "No Wordlist",
                "Please select a wordlist file.")
            return
        algo = self.selected_algo.get()
        name = self.output_name.get().strip()
        if not name.endswith(".json"):
            name += ".json"

        self.running = True
        self.build_btn.configure(
            state="disabled",
            text="⏳  Building...")
        self.progress["value"] = 0

        threading.Thread(
            target=self._build_worker,
            args=(wf, algo, name),
            daemon=True).start()

    def _build_worker(self, wordlist_path,
                      algo, output_name):
        start   = time.time()
        algo_fn = ALGORITHMS[algo]
        max_e   = self.max_entries.get()

        self.after(0, self._log,
            f"[BUILD] Starting {algo} table "
            f"from {os.path.basename(wordlist_path)}"
            f"  ·  max: "
            f"{'unlimited' if not max_e else max_e}",
            "build")

        try:
            with open(wordlist_path, "r",
                      encoding="latin-1") as f:
                words = [
                    w.strip() for w in f
                    if w.strip()]
        except Exception as e:
            messagebox.showerror(
                "File Error", str(e))
            self.running = False
            self.after(
                0, lambda: self.build_btn.configure(
                    state="normal",
                    text="▶  Build Rainbow Table"))
            return

        if max_e and max_e > 0:
            words = words[:max_e]

        total   = len(words)
        table   = {}
        skipped = 0

        self.after(0, self._log,
            f"[BUILD] Processing {total:,} words...",
            "build")

        for i, word in enumerate(words):
            try:
                h = algo_fn(word)
                if h not in table:
                    table[h] = word
                else:
                    skipped += 1
            except Exception:
                skipped += 1

            if i % 1000 == 0 or i == total - 1:
                pct     = int(((i + 1) / total) * 100) \
                          if total else 100
                elapsed = round(time.time() - start, 1)
                self.after(
                    0, self._update_build_progress,
                    pct, len(table),
                    total, elapsed, algo)

        # Save to data folder
        out_path = os.path.join(DATA_DIR, output_name)
        os.makedirs(DATA_DIR, exist_ok=True)

        with open(out_path, "w",
                  encoding="utf-8") as f:
            json.dump(table, f, indent=None,
                      separators=(",", ":"))

        elapsed = round(time.time() - start, 2)

        # Calculate size
        size_bytes = os.path.getsize(out_path)
        if size_bytes < 1024:
            size_str = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes // 1024} KB"
        else:
            size_str = (
                f"{size_bytes // (1024 * 1024)} MB")

        self.after(0, self._log,
            f"[BUILD] Complete!  {len(table):,} "
            f"entries  ·  {size_str}  ·  "
            f"{elapsed}s  ·  saved: {out_path}",
            "success")

        # Load into combined table
        self.combined_table.update(table)

        info = {
            "path":    out_path,
            "name":    output_name,
            "entries": len(table),
            "size":    size_str,
            "algos":   algo,
        }
        self.loaded_tables.append(info)

        # ── FIX: use lambda for all keyword-arg calls ──
        self.after(
            0, lambda: self.table_tree.insert(
                "", "end",
                values=(
                    output_name, algo,
                    f"{len(table):,}", size_str)))

        self.after(0, self._update_stats)

        self.after(
            0, lambda: self.progress.__setitem__(
                "value", 100))

        self.after(
            0, lambda: self.progress_label.configure(
                text=(f"100%  ·  Done  ·  "
                      f"{len(table):,} entries  ·  "
                      f"{elapsed}s")))

        self.after(
            0, lambda: self._set_status(
                f"Built: {output_name}  ·  "
                f"{len(table):,} entries  ·  "
                f"{size_str}"))

        self.after(
            0, lambda: self.build_btn.configure(
                state="normal",
                text="▶  Build Rainbow Table"))

        self.running = False

    def _update_build_progress(
            self, pct, count, total,
            elapsed, algo):
        self.progress["value"] = pct
        self.progress_label.configure(
            text=(f"{pct}%  ·  "
                  f"{count:,} {algo} hashes  ·  "
                  f"{elapsed}s elapsed"))
        self._set_status(
            f"Building {algo} table...  "
            f"{pct}%  ·  {count:,} entries")

    # ── Load existing table ───────────────────────────
    def _load_table(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("JSON tables", "*.json"),
                ("All files",   "*.*")])
        if path:
            self._load_table_from_path(path)

    # ── Export combined table ─────────────────────────
    def _export_table(self):
        if not self.combined_table:
            messagebox.showwarning(
                "Empty",
                "No tables loaded to export.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile="combined_rainbow.json")
        if not path:
            return
        with open(path, "w",
                  encoding="utf-8") as f:
            json.dump(self.combined_table, f,
                      separators=(",", ":"))
        size     = os.path.getsize(path)
        size_str = (f"{size // 1024} KB"
                    if size < 1024 * 1024
                    else f"{size // (1024 * 1024)} MB")
        messagebox.showinfo(
            "Exported",
            f"Combined table exported:\n{path}\n"
            f"{len(self.combined_table):,} entries"
            f"  ·  {size_str}")
        self._log(
            f"[EXPORT] Combined table  ·  "
            f"{len(self.combined_table):,} entries"
            f"  ·  {size_str}  →  {path}",
            "success")

    # ── Remove selected table ─────────────────────────
    def _remove_table(self):
        selected = self.table_tree.selection()
        if not selected:
            messagebox.showwarning(
                "None selected",
                "Select a table from the list.")
            return
        item   = selected[0]
        values = self.table_tree.item(item, "values")
        name   = values[0] if values else ""

        self.table_tree.delete(item)

        # Remove from loaded_tables list
        self.loaded_tables = [
            t for t in self.loaded_tables
            if t["name"] != name]

        # Rebuild combined table from remaining
        self.combined_table = {}
        for t in self.loaded_tables:
            try:
                with open(t["path"], "r",
                          encoding="utf-8") as f:
                    self.combined_table.update(
                        json.load(f))
            except Exception:
                pass

        self._update_stats()
        self._log(
            f"[REMOVE] {name} removed from "
            f"session", "info")
        self._set_status(
            f"Removed {name}  ·  "
            f"{len(self.combined_table):,} "
            f"entries remaining")

    # ── Clear all ─────────────────────────────────────
    def _clear_all(self):
        if not messagebox.askyesno(
                "Clear All",
                "Remove all loaded tables "
                "from this session?\n"
                "(Files on disk are NOT deleted)"):
            return
        self.combined_table = {}
        self.loaded_tables  = []
        self.table_tree.delete(
            *self.table_tree.get_children())
        for v in self.stat_vars.values():
            v.set("0")
        self.stat_vars["Algorithms"].set("—")
        self.stat_vars["Lookup ms"].set("—")
        self.progress["value"] = 0
        self.progress_label.configure(
            text="0%  ·  waiting...")
        self.lookup_result.configure(text="")
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self._set_status("Cleared · Ready")