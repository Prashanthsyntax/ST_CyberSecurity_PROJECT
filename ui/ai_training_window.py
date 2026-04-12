import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

from ui.hash_cracker_window import FG_PURPLE

BG_DARK  = "#1e1e2e"
BG_CARD  = "#2a2a3e"
FG_PRIMARY="#cbd5e1"
FG_MUTED = "#64748b"
FG_BLUE  = "#7dd3fc"
FG_GREEN = "#22c55e"
FG_RED   = "#ef4444"
FG_AMBER = "#fbbf24"
BORDER   = "#3a3a50"
BTN_BLUE = "#185FA5"


class AITrainingFrame(tk.Frame):
    def __init__(self, parent, nav=None):
        super().__init__(parent, bg=BG_DARK)
        self.nav = nav

        self.wordlist_var = tk.StringVar()
        self.running      = False

        self._build_titlebar()
        self._build_body()
        self._build_buttons()
        self._build_statusbar()
        self._build_log()
        self._load_existing_stats()

    def _build_titlebar(self):
        bar = tk.Frame(self, bg=BG_CARD, height=36)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        for color in ["#ff5f57","#febc2e","#28c840"]:
            tk.Label(bar, bg=color, width=2).pack(
                side="left",
                padx=(8 if color=="#ff5f57" else 4, 0),
                pady=10)
        tk.Label(bar,
                 text="AI Engine — Train Markov + "
                      "N-gram Models",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 10)).pack(
                 side="left", padx=12)

    def _build_body(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(12, 0))

        tk.Label(frame,
                 text="TRAINING WORDLIST",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(
                 anchor="w", pady=(0, 4))

        row = tk.Frame(frame, bg=BG_DARK)
        row.pack(fill="x")
        tk.Entry(row, textvariable=self.wordlist_var,
                 bg=BG_CARD, fg=FG_PRIMARY,
                 insertbackground=FG_BLUE,
                 relief="flat",
                 highlightthickness=1,
                 highlightbackground=BORDER,
                 font=("Courier", 10),
                 width=60).pack(side="left", fill="x",
                                expand=True,
                                padx=(0,8), ipady=6)
        tk.Button(row, text="Browse",
                  bg=BG_CARD, fg=FG_BLUE,
                  relief="flat", font=("Courier",10),
                  command=self._browse
                  ).pack(side="left")

        # Stats cards
        tk.Label(frame, text="MODEL STATS",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(
                 anchor="w", pady=(12, 4))

        self.stat_vars = {
            "Trained on":    tk.StringVar(value="0"),
            "Markov states": tk.StringVar(value="0"),
            "2-grams":       tk.StringVar(value="0"),
            "Self-learned":  tk.StringVar(value="0"),
        }
        colors = {
            "Trained on":    FG_BLUE,
            "Markov states": FG_AMBER,
            "2-grams":       FG_GREEN,
            "Self-learned":  FG_PURPLE
                             if hasattr(self, 'FG_PURPLE')
                             else "#a78bfa",
        }
        srow = tk.Frame(frame, bg=BG_DARK)
        srow.pack(fill="x")
        for label, var in self.stat_vars.items():
            card = tk.Frame(srow, bg=BG_CARD,
                            highlightthickness=1,
                            highlightbackground=BORDER)
            card.pack(side="left", expand=True,
                      fill="x", padx=4)
            tk.Label(card, textvariable=var,
                     bg=BG_CARD,
                     fg=colors.get(label, FG_BLUE),
                     font=("Courier",14,"bold")
                     ).pack(pady=(12,6))
            tk.Label(card, text=label,
                     bg=BG_CARD, fg=FG_MUTED,
                     font=("Courier",8)
                     ).pack(pady=(0,12))

        # Progress
        self.progress = ttk.Progressbar(
            frame, mode="determinate",
            maximum=100, value=0)
        self.progress.pack(fill="x", pady=(16,0))
        self.prog_label = tk.Label(
            frame, text="0%  ·  waiting...",
            bg=BG_DARK, fg=FG_MUTED,
            font=("Courier",8))
        self.prog_label.pack(anchor="w", pady=4)

    def _browse(self):
        path = filedialog.askopenfilename(
            filetypes=[("Text files","*.txt"),
                       ("All files","*.*")])
        if path:
            self.wordlist_var.set(path)

    def _build_buttons(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(10, 8))

        self.train_btn = tk.Button(
            frame,
            text="▶  Train AI Models",
            bg=BTN_BLUE, fg="#e0f0ff",
            font=("Courier",12,"bold"),
            relief="flat", cursor="hand2",
            command=self._train)
        self.train_btn.pack(side="left", expand=True,
                            fill="x", padx=(0,6),
                            ipady=11)

        tk.Button(frame, text="Reset Models",
                  bg=BG_DARK, fg=FG_RED,
                  font=("Courier",10),
                  relief="flat",
                  highlightthickness=1,
                  highlightbackground=BORDER,
                  cursor="hand2",
                  command=self._reset
                  ).pack(side="left", ipady=10,
                         ipadx=14)

    def _build_statusbar(self):
        bar = tk.Frame(self, bg=BG_CARD, height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Label(bar, text="●",
                 bg=BG_CARD, fg=FG_GREEN,
                 font=("Courier",10)).pack(
                 side="left", padx=(12,4))
        self.status_var = tk.StringVar(
            value="Ready · Select a wordlist to train")
        tk.Label(bar, textvariable=self.status_var,
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier",9)).pack(side="left")

    def _build_log(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="both", expand=True,
                   padx=16, pady=(6,8))
        tk.Label(frame, text="TRAINING LOG",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier",8)).pack(
                 anchor="w", pady=(0,4))
        lf = tk.Frame(frame, bg=BG_CARD,
                      highlightthickness=1,
                      highlightbackground=BORDER)
        lf.pack(fill="both", expand=True)
        self.log = tk.Text(lf, bg=BG_CARD,
                           fg=FG_PRIMARY,
                           font=("Courier",9),
                           relief="flat",
                           state="disabled",
                           padx=8, pady=6)
        sb = tk.Scrollbar(lf,
                          command=self.log.yview,
                          bg=BG_CARD)
        self.log.configure(yscrollcommand=sb.set)
        self.log.pack(side="left", fill="both",
                      expand=True)
        sb.pack(side="right", fill="y")

    def _log(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _load_existing_stats(self):
        try:
            from core.ai_engine.trainer import AITrainer
            t = AITrainer()
            if t.is_trained():
                t.load_models()
                s = t.get_stats()
                self.stat_vars["Trained on"].set(
                    f"{s['total_trained']:,}")
                self.stat_vars["Markov states"].set(
                    f"{s['markov_states']:,}")
                self.stat_vars["2-grams"].set(
                    f"{s['ngram_2_count']:,}")
                self.stat_vars["Self-learned"].set(
                    f"{s['self_learned']:,}")
                self._log(
                    f"Existing models found · "
                    f"trained on {s['total_trained']:,}"
                    f" passwords")
            else:
                self._log(
                    "No trained models yet · "
                    "select a wordlist and train")
        except Exception as e:
            self._log(f"Could not load stats: {e}")

    def _train(self):
        if self.running:
            return
        path = self.wordlist_var.get().strip()
        if not path:
            messagebox.showwarning(
                "No File",
                "Please select a wordlist file.")
            return
        self.running = True
        self.train_btn.configure(
            state="disabled", text="⏳  Training...")
        self.progress["value"] = 0
        self._log(f"Starting training on: {path}")
        threading.Thread(
            target=self._train_worker,
            args=(path,), daemon=True).start()

    def _train_worker(self, path):
        from core.ai_engine.trainer import AITrainer
        trainer = AITrainer()

        def cb(pct, count):
            self.after(0,
                lambda p=pct, c=count: (
                    self.progress.__setitem__(
                        "value", p),
                    self.prog_label.configure(
                        text=f"{p}%  ·  "
                             f"{c:,} passwords"),
                    self.status_var.set(
                        f"Training...  {p}%  ·  "
                        f"{c:,} processed")
                ))

        count = trainer.train_from_file(path, cb)
        stats = trainer.get_stats()

        self.after(0, lambda: (
            self.stat_vars["Trained on"].set(
                f"{stats['total_trained']:,}"),
            self.stat_vars["Markov states"].set(
                f"{stats['markov_states']:,}"),
            self.stat_vars["2-grams"].set(
                f"{stats['ngram_2_count']:,}"),
            self.progress.__setitem__("value", 100),
            self.prog_label.configure(
                text=f"100%  ·  Done  ·  "
                     f"{count:,} passwords trained"),
            self.status_var.set(
                f"Training complete  ·  "
                f"{count:,} passwords"),
            self.train_btn.configure(
                state="normal",
                text="▶  Train AI Models"),
            self._log(
                f"Done! Trained on {count:,} "
                f"passwords\n"
                f"Markov states: "
                f"{stats['markov_states']:,}\n"
                f"2-grams: "
                f"{stats['ngram_2_count']:,}\n"
                f"Models saved to data/ai_models/")
        ))
        self.running = False

    def _reset(self):
        if not messagebox.askyesno(
                "Reset Models",
                "Delete all trained AI models?\n"
                "This cannot be undone."):
            return
        import os
        from core.ai_engine.trainer import (
            MARKOV_PATH, NGRAM_PATH, STATS_PATH)
        for p in [MARKOV_PATH, NGRAM_PATH,
                  STATS_PATH]:
            if os.path.exists(p):
                os.remove(p)
        for var in self.stat_vars.values():
            var.set("0")
        self.progress["value"] = 0
        self._log("Models reset · ready to retrain")
        self.status_var.set(
            "Models deleted · ready to retrain")