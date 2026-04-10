import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import csv
import time
import hashlib

from core.rainbow import RainbowPasswordCracker
from core.hash_identifier import identify_hash

BG_DARK   = "#1e1e2e"
BG_CARD   = "#2a2a3e"
BG_ACCENT = "#1e3a4a"
FG_PRIMARY= "#cbd5e1"
FG_MUTED  = "#64748b"
FG_BLUE   = "#7dd3fc"
FG_GREEN  = "#22c55e"
FG_RED    = "#ef4444"
FG_PURPLE = "#a78bfa"
BORDER    = "#3a3a50"
BTN_BLUE  = "#185FA5"

ALGORITHMS = {
    "md5":    lambda w: hashlib.md5(w.encode("latin-1")).hexdigest(),
    "sha1":   lambda w: hashlib.sha1(w.encode("latin-1")).hexdigest(),
    "sha256": lambda w: hashlib.sha256(w.encode("latin-1")).hexdigest(),
    "sha512": lambda w: hashlib.sha512(w.encode("latin-1")).hexdigest(),
    "ntlm":   lambda w: hashlib.new("md4", w.encode("utf-16-le")).hexdigest(),
    "md4":    lambda w: hashlib.new("md4", w.encode("latin-1")).hexdigest(),
}

rainbow = RainbowPasswordCracker()


class HashCrackerFrame(tk.Frame):
    def __init__(self, parent, nav=None):
        super().__init__(parent, bg=BG_DARK)
        self.nav = nav

        self.hash_file     = tk.StringVar()
        self.wordlist_file = tk.StringVar()
        self.results       = []
        self.running       = False

        self.algo_vars = {a: tk.BooleanVar(value=(a in ["md5","sha1","sha256"]))
                          for a in ALGORITHMS}

        self._build_titlebar()
        self._build_files_section()
        self._build_algo_section()
        self._build_hash_preview()
        self._build_stats_bar()
        self._build_progress()
        self._build_buttons()
        self._build_statusbar()
        self._build_results_table()

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
                 text="Window 2 — Multi-Algorithm Hash Cracker",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 10)).pack(side="left", padx=12)

    # ── File selectors ───────────────────────────────────────
    def _build_files_section(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(12, 0))

        for label, var in [
            ("Hash File",     self.hash_file),
            ("Wordlist File", self.wordlist_file),
        ]:
            row = tk.Frame(frame, bg=BG_DARK)
            row.pack(fill="x", pady=3)

            tk.Label(row, text=label,
                     bg=BG_DARK, fg=FG_MUTED,
                     font=("Courier", 9),
                     width=12, anchor="w").pack(side="left")

            tk.Entry(row, textvariable=var,
                     bg=BG_CARD, fg=FG_PRIMARY,
                     insertbackground=FG_BLUE,
                     relief="flat",
                     highlightthickness=1,
                     highlightbackground=BORDER,
                     font=("Courier", 10),
                     width=58).pack(side="left", padx=6)

            tk.Button(row, text="Browse",
                      bg=BG_CARD, fg=FG_BLUE,
                      relief="flat",
                      font=("Courier", 9),
                      activebackground=BG_ACCENT,
                      activeforeground=FG_BLUE,
                      command=lambda v=var: self._browse(v)).pack(side="left")

        tk.Button(frame,
                  text="  Load & Auto-detect Hashes  ",
                  bg=BG_CARD, fg=FG_BLUE,
                  relief="flat",
                  highlightthickness=1,
                  highlightbackground=BORDER,
                  font=("Courier", 9),
                  activebackground=BG_ACCENT,
                  activeforeground=FG_BLUE,
                  command=self._load_hashes).pack(anchor="w", pady=(8, 0))

    def _browse(self, var):
        path = filedialog.askopenfilename()
        if path:
            var.set(path)

    # ── Algorithm toggles ────────────────────────────────────
    def _build_algo_section(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(10, 0))

        tk.Label(frame, text="ALGORITHMS — select which to try",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w", pady=(0, 5))

        row = tk.Frame(frame, bg=BG_DARK)
        row.pack(fill="x")

        for algo, var in self.algo_vars.items():
            tk.Checkbutton(row,
                           text=algo.upper(),
                           variable=var,
                           bg=BG_DARK,
                           fg=FG_PRIMARY,
                           selectcolor=BG_ACCENT,
                           activebackground=BG_DARK,
                           activeforeground=FG_BLUE,
                           font=("Courier", 9)).pack(side="left", padx=6)

    # ── Hash preview table ───────────────────────────────────
    def _build_hash_preview(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(10, 0))

        tk.Label(frame,
                 text="LOADED HASHES — AUTO-DETECTED TYPE",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w", pady=(0, 4))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background=BG_CARD,
                        foreground=FG_PRIMARY,
                        fieldbackground=BG_CARD,
                        rowheight=24,
                        font=("Courier", 9))
        style.configure("Treeview.Heading",
                        background=BG_DARK,
                        foreground=FG_MUTED,
                        font=("Courier", 9))
        style.map("Treeview",
                  background=[("selected", BG_ACCENT)])

        cols = ("Hash Value", "Detected Algorithm", "Length")
        self.preview_tree = ttk.Treeview(frame, columns=cols,
                                          show="headings", height=3)
        self.preview_tree.heading("Hash Value",          text="Hash Value")
        self.preview_tree.heading("Detected Algorithm",  text="Detected Algorithm")
        self.preview_tree.heading("Length",              text="Length")
        self.preview_tree.column("Hash Value",         width=500)
        self.preview_tree.column("Detected Algorithm", width=160)
        self.preview_tree.column("Length",             width=70)
        self.preview_tree.pack(fill="x")

    def _load_hashes(self):
        path = self.hash_file.get().strip()
        if not path:
            messagebox.showwarning("Error",
                "Please select a hash file first.")
            return
        try:
            with open(path, "r", encoding="latin-1") as f:
                hashes = [h.strip() for h in f if h.strip()]
            self.preview_tree.delete(*self.preview_tree.get_children())
            for h in hashes:
                algo = identify_hash(h)
                self.preview_tree.insert("", "end",
                    values=(h, algo.upper(), len(h)))
            self._set_status(
                f"Loaded {len(hashes)} hash(es) — types auto-detected")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ── Stats bar ────────────────────────────────────────────
    def _build_stats_bar(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(10, 0))

        self.stat_vars = {
            "Total":     tk.StringVar(value="0"),
            "Cracked":   tk.StringVar(value="0"),
            "Not Found": tk.StringVar(value="0"),
            "Elapsed":   tk.StringVar(value="0.0s"),
            "Rainbow":   tk.StringVar(value="0"),
        }
        colors = {
            "Total":     FG_BLUE,
            "Cracked":   FG_GREEN,
            "Not Found": FG_RED,
            "Elapsed":   FG_PRIMARY,
            "Rainbow":   FG_PURPLE,
        }

        for label, var in self.stat_vars.items():
            card = tk.Frame(frame, bg=BG_CARD,
                            highlightthickness=1,
                            highlightbackground=BORDER)
            card.pack(side="left", expand=True, fill="x", padx=4)
            tk.Label(card, textvariable=var,
                     bg=BG_CARD, fg=colors[label],
                     font=("Courier", 16, "bold")).pack(pady=(8, 2))
            tk.Label(card, text=label,
                     bg=BG_CARD, fg=FG_MUTED,
                     font=("Courier", 8)).pack(pady=(0, 8))

    # ── Progress bar ─────────────────────────────────────────
    def _build_progress(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(10, 0))

        style = ttk.Style()
        style.configure("TProgressbar",
                        troughcolor=BG_CARD,
                        background=BTN_BLUE,
                        thickness=8)

        self.progress = ttk.Progressbar(frame,
                                         mode="determinate",
                                         maximum=100,
                                         value=0)
        self.progress.pack(fill="x")

        self.progress_label = tk.Label(frame,
                                        text="0%  ·  waiting...",
                                        bg=BG_DARK, fg=FG_MUTED,
                                        font=("Courier", 8))
        self.progress_label.pack(anchor="w", pady=2)

    # ── Buttons — packed BEFORE results so always visible ────
    def _build_buttons(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(10, 6))

        self.start_btn = tk.Button(
            frame,
            text="▶  Start Cracking",
            bg=BTN_BLUE,
            fg="#e0f0ff",
            font=("Courier", 12, "bold"),
            relief="flat",
            activebackground="#1a6fbf",
            activeforeground="#ffffff",
            cursor="hand2",
            command=self._start)
        self.start_btn.pack(side="left", expand=True,
                            fill="x", padx=(0, 6), ipady=10)

        tk.Button(frame,
                  text="Export CSV",
                  bg=BG_CARD, fg=FG_BLUE,
                  font=("Courier", 10),
                  relief="flat",
                  highlightthickness=1,
                  highlightbackground=BORDER,
                  activebackground=BG_ACCENT,
                  activeforeground=FG_BLUE,
                  cursor="hand2",
                  command=self._export_csv).pack(
                  side="left", padx=4, ipady=10, ipadx=14)

        tk.Button(frame,
                  text="Clear",
                  bg=BG_CARD, fg=FG_MUTED,
                  font=("Courier", 10),
                  relief="flat",
                  highlightthickness=1,
                  highlightbackground=BORDER,
                  activebackground=BG_CARD,
                  activeforeground=FG_PRIMARY,
                  cursor="hand2",
                  command=self._clear).pack(
                  side="left", ipady=10, ipadx=14)

    # ── Status bar — packed BEFORE results ───────────────────
    def _build_statusbar(self):
        bar = tk.Frame(self, bg=BG_CARD, height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        self.status_var = tk.StringVar(
            value="Ready · Select files and click Load, then Start Cracking")
        tk.Label(bar,
                 textvariable=self.status_var,
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 9)).pack(side="left", padx=12)

    def _set_status(self, msg):
        self.status_var.set(msg)

    # ── Results table — packed LAST so it fills remaining space
    def _build_results_table(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="both", expand=True, padx=16, pady=(4, 4))

        tk.Label(frame, text="RESULTS",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w", pady=(0, 4))

        cols = ("#", "Hash", "Algorithm", "Plaintext", "Method", "Status")
        self.results_tree = ttk.Treeview(frame, columns=cols,
                                          show="headings")

        self.results_tree.heading("#",          text="#")
        self.results_tree.heading("Hash",       text="Hash")
        self.results_tree.heading("Algorithm",  text="Algorithm")
        self.results_tree.heading("Plaintext",  text="Plaintext")
        self.results_tree.heading("Method",     text="Method")
        self.results_tree.heading("Status",     text="Status")

        self.results_tree.column("#",          width=35,  anchor="center")
        self.results_tree.column("Hash",       width=280)
        self.results_tree.column("Algorithm",  width=100, anchor="center")
        self.results_tree.column("Plaintext",  width=150)
        self.results_tree.column("Method",     width=100, anchor="center")
        self.results_tree.column("Status",     width=100, anchor="center")

        self.results_tree.tag_configure(
            "cracked",  foreground=FG_GREEN,  background="#0d1f0d")
        self.results_tree.tag_configure(
            "notfound", foreground=FG_RED,    background="#1f0d0d")
        self.results_tree.tag_configure(
            "rainbow",  foreground=FG_PURPLE, background="#130d1f")

        sb = ttk.Scrollbar(frame, orient="vertical",
                           command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=sb.set)
        self.results_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    # ── Core cracking logic ──────────────────────────────────
    def _start(self):
        if self.running:
            return
        hf = self.hash_file.get().strip()
        wf = self.wordlist_file.get().strip()
        if not hf or not wf:
            messagebox.showwarning("Input Error",
                "Please select both hash and wordlist files.")
            return
        active_algos = [a for a, v in self.algo_vars.items() if v.get()]
        if not active_algos:
            messagebox.showwarning("Input Error",
                "Please select at least one algorithm.")
            return
        self._clear()
        self.running = True
        self.start_btn.configure(state="disabled",
                                  text="⏳  Running...")
        threading.Thread(
            target=self._crack_worker,
            args=(hf, wf, active_algos),
            daemon=True).start()

    def _crack_worker(self, hash_file, wordlist_file, active_algos):
        start_time = time.time()
        try:
            with open(hash_file, "r", encoding="latin-1") as f:
                hashes = [h.strip() for h in f if h.strip()]
            with open(wordlist_file, "r", encoding="latin-1") as f:
                wordlist = [w.strip() for w in f if w.strip()]
        except Exception as e:
            messagebox.showerror("File Error", str(e))
            self.running = False
            return

        total = len(hashes)
        cracked = not_found = rainbow_hits = 0
        self.after(0, lambda: self.stat_vars["Total"].set(str(total)))

        for idx, hash_val in enumerate(hashes):
            detected_algo = identify_hash(hash_val)
            found         = False
            method        = ""
            plaintext     = ""
            tag           = "notfound"

            # 1 — Rainbow table lookup
            result = rainbow.lookup(hash_val)
            if result is not None:
                found        = True
                plaintext    = result
                method       = "Rainbow"
                rainbow_hits += 1
                cracked      += 1
                tag           = "rainbow"
            else:
                # 2 — Dictionary attack
                for word in wordlist:
                    for algo in active_algos:
                        try:
                            if ALGORITHMS[algo](word) == hash_val.lower():
                                found     = True
                                plaintext = word
                                method    = algo.upper()
                                cracked  += 1
                                tag       = "cracked"
                                break
                        except Exception:
                            pass
                    if found:
                        break

            if not found:
                plaintext  = "—"
                method     = "—"
                not_found += 1
                tag        = "notfound"

            elapsed = round(time.time() - start_time, 2)
            pct     = int(((idx + 1) / total) * 100)

            row = {
                "idx":    idx + 1,
                "hash":   hash_val[:38] + "..." if len(hash_val) > 38
                          else hash_val,
                "algo":   detected_algo.upper(),
                "plain":  plaintext,
                "method": method,
                "status": "Cracked" if found else "Not Found",
                "tag":    tag,
            }
            self.results.append(row)

            self.after(0, self._update_ui,
                           row, cracked, not_found,
                           rainbow_hits, elapsed, pct, total)

        self.after(0, self._done)

    def _update_ui(self, row, cracked, not_found,
                   rainbow_hits, elapsed, pct, total):
        self.results_tree.insert("", "end", values=(
            row["idx"],
            row["hash"],
            row["algo"],
            row["plain"],
            row["method"],
            row["status"],
        ), tags=(row["tag"],))
        self.results_tree.yview_moveto(1)

        self.stat_vars["Cracked"].set(str(cracked))
        self.stat_vars["Not Found"].set(str(not_found))
        self.stat_vars["Elapsed"].set(f"{elapsed}s")
        self.stat_vars["Rainbow"].set(str(rainbow_hits))

        self.progress["value"] = pct
        self.progress_label.configure(
            text=f"{pct}%  ·  {cracked}/{total} cracked  ·  {elapsed}s elapsed")
        self._set_status(
            f"Running...  {pct}%  ·  {cracked} cracked  ·  {elapsed}s")

    def _done(self):
        self.running = False
        self.start_btn.configure(
            state="normal",
            text="▶  Start Cracking")
        total   = len(self.results)
        cracked = sum(
            1 for r in self.results
            if r["status"] == "Cracked")
        self.progress["value"] = 100
        self.progress_label.configure(
            text="100%  ·  Complete")
        self._set_status(
            f"Done  ·  {cracked}/{total} "
            f"cracked  ·  "
            f"{self.stat_vars['Elapsed'].get()}")
        
        # Auto-log the session
        from core.session_logger import log_session
        cracked = sum(
            1 for r in self.results
            if r["status"] == "Cracked")
        log_session("Hash Crack", {
            "cracked":  cracked,
            "total":    len(self.results),
            "elapsed":  self.stat_vars[
                "Elapsed"].get(),
            "summary":
                f"{cracked}/{len(self.results)}"
                f" cracked · "
                f"{self.stat_vars['Elapsed'].get()}",
            "algorithms": list(set(
                r["algo"] for r in self.results)),
        })

    # ── Export CSV ───────────────────────────────────────────
    def _export_csv(self):
        if not self.results:
            messagebox.showwarning("No Data",
                "No results to export yet.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="crack_results.csv")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "idx", "hash", "algo", "plain",
                "method", "status", "tag"])
            writer.writeheader()
            writer.writerows(self.results)
        messagebox.showinfo("Exported",
            f"Results saved to:\n{path}")

    # ── Clear ────────────────────────────────────────────────
    def _clear(self):
        self.results.clear()
        self.results_tree.delete(*self.results_tree.get_children())
        self.preview_tree.delete(*self.preview_tree.get_children())
        for k, v in self.stat_vars.items():
            v.set("0" if k != "Elapsed" else "0.0s")
        self.progress["value"] = 0
        self.progress_label.configure(text="0%  ·  waiting...")
        self._set_status("Cleared · Ready")