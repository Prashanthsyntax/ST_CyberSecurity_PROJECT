import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time

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


class WordlistGeneratorFrame(tk.Frame):
    def __init__(self, parent, nav=None):
        super().__init__(parent, bg=BG_DARK)
        self.nav = nav

        # ── Target info fields ────────────────────────
        self.name_var     = tk.StringVar()
        self.username_var = tk.StringVar()
        self.birthday_var = tk.StringVar()
        self.company_var  = tk.StringVar()
        self.keywords_var = tk.StringVar()
        self.phone_var    = tk.StringVar()
        self.custom_var   = tk.StringVar()

        # ── Generation option toggles ─────────────────
        self.options = {
            "Name combos":       tk.BooleanVar(value=True),
            "Leet mutations":    tk.BooleanVar(value=True),
            "Year suffixes":     tk.BooleanVar(value=True),
            "Number padding":    tk.BooleanVar(value=True),
            "Symbol append":     tk.BooleanVar(value=True),
            "Birthday patterns": tk.BooleanVar(value=True),
            "Reverse words":     tk.BooleanVar(value=False),
            "Keyboard walks":    tk.BooleanVar(value=False),
        }

        # ── Mutation rules for core/mutator.py ────────
        self.mutation_rules = {
            "leet":       tk.BooleanVar(value=True),
            "capitalise": tk.BooleanVar(value=True),
            "numbers":    tk.BooleanVar(value=True),
            "symbols":    tk.BooleanVar(value=True),
            "reverse":    tk.BooleanVar(value=False),
            "year":       tk.BooleanVar(value=True),
            "duplicate":  tk.BooleanVar(value=False),
        }

        self.opt_btns  = {}
        self.word_list = []
        self.running   = False

        self._build_titlebar()
        self._build_target_section()
        self._build_options_section()
        self._build_stats_bar()
        self._build_progress()
        self._build_buttons()
        self._build_statusbar()
        self._build_preview()

    # ── Title bar ────────────────────────────────────
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
                 text="Window 4 — AI Smart Wordlist Generator",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 10)).pack(
                 side="left", padx=12)

    # ── Target info — 2 column grid ──────────────────
    def _build_target_section(self):
        outer = tk.Frame(self, bg=BG_DARK)
        outer.pack(fill="x", padx=16, pady=(12, 0))

        tk.Label(outer,
                 text="TARGET INFORMATION — fill what you know",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(
                 anchor="w", pady=(0, 6))

        grid = tk.Frame(outer, bg=BG_DARK)
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        # Left card
        left = tk.Frame(grid, bg=BG_CARD,
                        highlightthickness=1,
                        highlightbackground=BORDER)
        left.grid(row=0, column=0, sticky="nsew",
                  padx=(0, 6), pady=2)

        tk.Label(left, text="Personal details",
                 bg=BG_CARD, fg=FG_BLUE,
                 font=("Courier", 9, "bold")).pack(
                 anchor="w", padx=12, pady=(10, 4))

        for label, var, ph in [
            ("Full name",   self.name_var,
             "e.g. John Smith"),
            ("Username",    self.username_var,
             "e.g. jsmith"),
            ("Birthday",    self.birthday_var,
             "e.g. 15081990"),
            ("Company/Org", self.company_var,
             "e.g. Acme Corp"),
        ]:
            self._field(left, label, var, ph)

        tk.Label(left, bg=BG_CARD,
                 text="").pack(pady=4)

        # Right card
        right = tk.Frame(grid, bg=BG_CARD,
                         highlightthickness=1,
                         highlightbackground=BORDER)
        right.grid(row=0, column=1, sticky="nsew",
                   padx=(6, 0), pady=2)

        tk.Label(right, text="Keywords & extras",
                 bg=BG_CARD, fg=FG_BLUE,
                 font=("Courier", 9, "bold")).pack(
                 anchor="w", padx=12, pady=(10, 4))

        for label, var, ph in [
            ("Pet/hobby/city",  self.keywords_var,
             "e.g. rocky, chess, london"),
            ("Phone/ID",        self.phone_var,
             "e.g. 9876543210"),
            ("Custom words",    self.custom_var,
             "e.g. dragon, sunshine"),
        ]:
            self._field(right, label, var, ph)

        tk.Label(right, bg=BG_CARD,
                 text="").pack(pady=4)

    def _field(self, parent, label, var, placeholder):
        row = tk.Frame(parent, bg=BG_CARD)
        row.pack(fill="x", padx=12, pady=3)

        tk.Label(row, text=label,
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 8),
                 width=14, anchor="w").pack(side="left")

        entry = tk.Entry(row, textvariable=var,
                         bg="#1a1a2e", fg=FG_PRIMARY,
                         insertbackground=FG_BLUE,
                         relief="flat",
                         highlightthickness=1,
                         highlightbackground=BORDER,
                         font=("Courier", 9))
        entry.pack(side="left", fill="x",
                   expand=True, ipady=4)

        if placeholder:
            entry.insert(0, placeholder)
            entry.configure(fg=FG_MUTED)

            def on_in(e, ent=entry, ph=placeholder):
                if ent.get() == ph:
                    ent.delete(0, "end")
                    ent.configure(fg=FG_PRIMARY)

            def on_out(e, ent=entry, ph=placeholder):
                if not ent.get().strip():
                    ent.insert(0, ph)
                    ent.configure(fg=FG_MUTED)

            entry.bind("<FocusIn>",  on_in)
            entry.bind("<FocusOut>", on_out)

    # ── Generation options ────────────────────────────
    def _build_options_section(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(10, 0))

        tk.Label(frame, text="GENERATION OPTIONS",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(
                 anchor="w", pady=(0, 5))

        row = tk.Frame(frame, bg=BG_DARK)
        row.pack(fill="x")

        for opt, var in self.options.items():
            btn = tk.Button(row, text=opt,
                            font=("Courier", 9),
                            relief="flat",
                            cursor="hand2",
                            padx=8, pady=4)
            btn.pack(side="left", padx=3)
            self.opt_btns[opt] = btn
            self._refresh_opt_btn(opt)
            btn.configure(
                command=lambda o=opt:
                self._toggle_opt(o))

    def _refresh_opt_btn(self, opt):
        btn    = self.opt_btns[opt]
        active = self.options[opt].get()
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

    def _toggle_opt(self, opt):
        self.options[opt].set(
            not self.options[opt].get())
        self._refresh_opt_btn(opt)

    # ── Stats bar ─────────────────────────────────────
    def _build_stats_bar(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(10, 0))

        self.stat_vars = {
            "Words":  tk.StringVar(value="0"),
            "Base":   tk.StringVar(value="0"),
            "Rules":  tk.StringVar(value="0"),
            "Size":   tk.StringVar(value="0 B"),
        }
        colors = {
            "Words": FG_BLUE,
            "Base":  FG_GREEN,
            "Rules": FG_PURPLE,
            "Size":  FG_AMBER,
        }
        labels = {
            "Words": "Words generated",
            "Base":  "Base words",
            "Rules": "Rules applied",
            "Size":  "File size",
        }
        for key, var in self.stat_vars.items():
            card = tk.Frame(frame, bg=BG_CARD,
                            highlightthickness=1,
                            highlightbackground=BORDER)
            card.pack(side="left", expand=True,
                      fill="x", padx=4)
            tk.Label(card, textvariable=var,
                     bg=BG_CARD, fg=colors[key],
                     font=("Courier", 16, "bold")
                     ).pack(pady=(8, 2))
            tk.Label(card, text=labels[key],
                     bg=BG_CARD, fg=FG_MUTED,
                     font=("Courier", 8)
                     ).pack(pady=(0, 8))

    # ── Progress bar ──────────────────────────────────
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
            frame, mode="determinate",
            maximum=100, value=0)
        self.progress.pack(fill="x")

        self.progress_label = tk.Label(
            frame,
            text="0%  ·  waiting...",
            bg=BG_DARK, fg=FG_MUTED,
            font=("Courier", 8))
        self.progress_label.pack(anchor="w", pady=2)

    # ── Buttons ───────────────────────────────────────
    def _build_buttons(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(10, 6))

        self.gen_btn = tk.Button(
            frame,
            text="▶  Generate Wordlist",
            bg=BTN_BLUE, fg="#e0f0ff",
            font=("Courier", 12, "bold"),
            relief="flat",
            highlightthickness=1,
            highlightbackground=BTN_BLUE,
            activebackground="#1a6fbf",
            activeforeground="#ffffff",
            cursor="hand2",
            command=self._generate)
        self.gen_btn.pack(side="left", expand=True,
                          fill="x", padx=(0, 6),
                          ipady=10)

        tk.Button(frame,
                  text="Save to File",
                  bg=BG_DARK, fg=FG_PRIMARY,
                  font=("Courier", 11),
                  relief="flat",
                  highlightthickness=1,
                  highlightbackground=BORDER,
                  activebackground=BG_CARD,
                  activeforeground=FG_BLUE,
                  cursor="hand2",
                  command=self._save_file
                  ).pack(side="left", expand=True,
                         fill="x", padx=3, ipady=10)

        tk.Button(frame,
                  text="Copy to Clipboard",
                  bg=BG_DARK, fg=FG_PRIMARY,
                  font=("Courier", 11),
                  relief="flat",
                  highlightthickness=1,
                  highlightbackground=BORDER,
                  activebackground=BG_CARD,
                  activeforeground=FG_BLUE,
                  cursor="hand2",
                  command=self._copy_clipboard
                  ).pack(side="left", expand=True,
                         fill="x", padx=3, ipady=10)

        tk.Button(frame,
                  text="Clear",
                  bg=BG_DARK, fg=FG_PRIMARY,
                  font=("Courier", 11),
                  relief="flat",
                  highlightthickness=1,
                  highlightbackground=BORDER,
                  activebackground=BG_CARD,
                  cursor="hand2",
                  command=self._clear
                  ).pack(side="left", expand=True,
                         fill="x", padx=(3, 0),
                         ipady=10)

    # ── Status bar ────────────────────────────────────
    def _build_statusbar(self):
        bar = tk.Frame(self, bg=BG_CARD, height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        tk.Label(bar, text="●",
                 bg=BG_CARD, fg=FG_GREEN,
                 font=("Courier", 10)).pack(
                 side="left", padx=(12, 4))

        self.status_var = tk.StringVar(
            value="Ready · Fill target info "
                  "and click Generate Wordlist")
        tk.Label(bar, textvariable=self.status_var,
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 9)).pack(side="left")

        tk.Label(bar,
                 text="AI-assisted · Markov · N-gram",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 9)).pack(
                 side="right", padx=12)

    def _set_status(self, msg):
        self.status_var.set(msg)

    # ── Preview — fills remaining space ──────────────
    def _build_preview(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="both", expand=True,
                   padx=16, pady=(6, 4))

        tk.Label(frame,
                 text="AI LOG & PREVIEW — "
                      "generated wordlist",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(
                 anchor="w", pady=(0, 4))

        box_frame = tk.Frame(frame, bg=BG_CARD,
                              highlightthickness=1,
                              highlightbackground=BORDER)
        box_frame.pack(fill="both", expand=True)

        self.preview_box = tk.Text(
            box_frame,
            bg="#1a1a2e", fg=FG_PRIMARY,
            font=("Courier", 10),
            relief="flat",
            state="disabled",
            wrap="word",
            padx=10, pady=8)

        sb = tk.Scrollbar(box_frame,
                          command=self.preview_box.yview,
                          bg=BG_CARD,
                          troughcolor=BG_DARK)
        self.preview_box.configure(
            yscrollcommand=sb.set)
        self.preview_box.pack(
            side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Color tags for AI log
        self.preview_box.tag_configure(
            "ai",    foreground=FG_BLUE)
        self.preview_box.tag_configure(
            "word",  foreground=FG_GREEN)
        self.preview_box.tag_configure(
            "warn",  foreground=FG_AMBER)
        self.preview_box.tag_configure(
            "error", foreground=FG_RED)

    # ── Generation trigger ────────────────────────────
    def _generate(self):
        if self.running:
            return
        self._clear_preview()
        self.word_list = []
        self.running   = True
        self.gen_btn.configure(
            state="disabled",
            text="⏳  Generating...")
        threading.Thread(
            target=self._generate_worker,
            daemon=True).start()

    # ── Core generation worker ────────────────────────
    def _generate_worker(self):
        seen  = set()
        words = []

        def add(w):
            w = str(w).strip()
            if w and w not in seen \
                    and 3 <= len(w) <= 20:
                seen.add(w)
                words.append(w)

        def log(msg, tag="ai"):
            self.after(0,
                self._append_preview,
                msg + "\n", tag)

        # Placeholder detection
        PLACEHOLDERS = {
            "e.g. John Smith",
            "e.g. jsmith",
            "e.g. 15081990",
            "e.g. Acme Corp",
            "e.g. rocky, chess, london",
            "e.g. 9876543210",
            "e.g. dragon, sunshine",
        }

        def clean(val):
            v = val.strip()
            return "" if v in PLACEHOLDERS else v

        info = {
            "name":     clean(self.name_var.get()),
            "username": clean(self.username_var.get()),
            "birthday": clean(self.birthday_var.get()),
            "company":  clean(self.company_var.get()),
            "keywords": clean(self.keywords_var.get()),
            "phone":    clean(self.phone_var.get()),
            "custom":   clean(self.custom_var.get()),
        }

        # ── STEP 1: Context Analyser (AI) ─────────────
        self.after(0, self._set_status,
                       "AI: Analysing target context...")
        self.after(0,
            self.progress_label.configure,
            {"text": "Step 1/4 — Context analysis"})

        from core.ai_engine.context_analyser \
            import ContextAnalyser

        analyser = ContextAnalyser()
        analyser.load_target(info)

        explanations = analyser.explain()
        for exp in explanations:
            log(f"[AI] {exp}")

        if not explanations:
            log("[AI] No target info provided — "
                "fill in name, birthday etc. "
                "for better results", "warn")

        context_words = analyser.generate(count=500)
        for w in context_words:
            add(w)

        self.after(0, self._update_progress,
                       25, len(words))
        log(f"[AI] Context analysis done · "
            f"{len(context_words)} words generated")

        # ── STEP 2: Load trained AI models ────────────
        self.after(0, self._set_status,
                       "AI: Loading trained models...")
        self.after(0,
            self.progress_label.configure,
            {"text": "Step 2/4 — Loading AI models"})

        from core.ai_engine.trainer import AITrainer
        from core.ai_engine.scorer import PasswordScorer

        trainer = AITrainer()
        loaded  = trainer.load_models()

        if loaded:
            stats = trainer.get_stats()
            log(f"[AI] Models loaded · trained on "
                f"{stats['total_trained']:,} passwords"
                f" · self-learned: "
                f"{stats['self_learned']}")

            # ── STEP 3: Markov generation ──────────────
            self.after(0, self._set_status,
                           "AI: Markov chain "
                           "generating...")
            self.after(0,
                self.progress_label.configure,
                {"text":
                 "Step 3/4 — Markov generation"})

            markov_words = trainer.markov.generate(
                min_len=4, max_len=14, count=300)
            for w in markov_words:
                add(w)

            self.after(0,
                self._update_progress, 60, len(words))
            log(f"[AI] Markov chain generated "
                f"{len(markov_words)} new candidates")

            # ── STEP 4: N-gram + scoring ───────────────
            self.after(0, self._set_status,
                           "AI: N-gram analysis "
                           "+ scoring...")
            self.after(0,
                self.progress_label.configure,
                {"text":
                 "Step 4/4 — Scoring & ranking"})

            ngram_words = \
                trainer.ngram.generate_from_ngrams(
                    count=200)
            for w in ngram_words:
                add(w)

            # Score and rank all words
            scorer = PasswordScorer(trainer.ngram)
            ranked = scorer.rank(words)
            words  = [w for w, s in ranked]

            log(f"[AI] N-gram generated "
                f"{len(ngram_words)} candidates")
            log(f"[AI] Scored & ranked "
                f"{len(words):,} candidates "
                f"by probability")

        else:
            log("[AI] No trained models found.\n"
                "Open AI Training from the launcher "
                "and train on a wordlist "
                "(rockyou.txt recommended) "
                "to enable Markov + N-gram "
                "generation.", "warn")

        # ── STEP 5: Rule-based mutations ──────────────
        self.after(0, self._set_status,
                       "Applying mutation rules...")
        self.after(0,
            self.progress_label.configure,
            {"text": "Step 5 — Mutation rules"})

        base_words = []
        if info["name"]:
            parts = info["name"].lower().split()
            base_words += parts
        if info["username"]:
            base_words.append(
                info["username"].lower())
        if info["company"]:
            base_words.append(
                info["company"].lower().replace(
                    " ", ""))
        for field in ["keywords", "custom"]:
            if info[field]:
                base_words += [
                    k.strip().lower()
                    for k in info[field].split(",")
                    if k.strip()]

        base_words = list(set(
            b for b in base_words if b))

        from core.mutator import mutate
        active_rules = [
            r for r, v
            in self.mutation_rules.items()
            if v.get()]

        for bw in base_words:
            for variant in mutate(bw, active_rules):
                add(variant)

        log(f"[AI] Mutation rules applied · "
            f"{len(active_rules)} rules · "
            f"{len(base_words)} base words")

        # ── Finalise ───────────────────────────────────
        self.word_list = words

        total_bytes = sum(
            len(w) + 1 for w in self.word_list)
        if total_bytes < 1024:
            size_str = f"{total_bytes} B"
        elif total_bytes < 1024 * 1024:
            size_str = f"{total_bytes // 1024} KB"
        else:
            size_str = (f"{total_bytes // (1024*1024)}"
                        f" MB")

        # Write all words to preview
        log("\n--- GENERATED WORDLIST PREVIEW ---",
            "ai")
        preview_words = self.word_list[:200]
        preview_text  = "  ".join(preview_words)
        if len(self.word_list) > 200:
            preview_text += (
                f"\n... and "
                f"{len(self.word_list) - 200:,} more")

        self.after(0,
            self._append_preview,
            preview_text + "\n", "word")

        self.after(0,
            self._generation_done, size_str,
            len(active_rules), len(base_words))

    # ── UI helpers ────────────────────────────────────
    def _update_progress(self, pct, count):
        self.progress["value"] = pct
        self.progress_label.configure(
            text=f"{pct}%  ·  "
                 f"{count:,} words so far...")
        self.stat_vars["Words"].set(f"{count:,}")
        self._set_status(
            f"Generating...  {pct}%  ·  "
            f"{count:,} words")

    def _generation_done(self, size_str,
                         rules_used, base_count):
        self.running = False
        self.gen_btn.configure(
            state="normal",
            text="▶  Generate Wordlist")

        count = len(self.word_list)
        self.progress["value"] = 100
        self.progress_label.configure(
            text=f"100%  ·  Complete  ·  "
                 f"{count:,} words generated")
        self.stat_vars["Words"].set(f"{count:,}")
        self.stat_vars["Size"].set(size_str)
        self.stat_vars["Rules"].set(str(rules_used))
        self.stat_vars["Base"].set(str(base_count))
        self._set_status(
            f"Done  ·  {count:,} words  ·  "
            f"{size_str}")

        self._append_preview(
            f"\n[AI] Generation complete · "
            f"{count:,} words · {size_str}\n",
            "ai")

    def _append_preview(self, text, tag="ai"):
        self.preview_box.configure(state="normal")
        self.preview_box.insert("end", text, tag)
        self.preview_box.see("end")
        self.preview_box.configure(state="disabled")

    # ── Save to file ──────────────────────────────────
    def _save_file(self):
        if not self.word_list:
            messagebox.showwarning(
                "No Data",
                "Generate a wordlist first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile="smart_wordlist.txt")
        if not path:
            return
        with open(path, "w",
                  encoding="utf-8") as f:
            f.write("\n".join(self.word_list))
        messagebox.showinfo(
            "Saved",
            f"{len(self.word_list):,} words "
            f"saved to:\n{path}")

    # ── Copy to clipboard ─────────────────────────────
    def _copy_clipboard(self):
        if not self.word_list:
            messagebox.showwarning(
                "No Data",
                "Generate a wordlist first.")
            return
        self.clipboard_clear()
        self.clipboard_append(
            "\n".join(self.word_list))
        self._set_status(
            f"Copied {len(self.word_list):,} "
            f"words to clipboard!")

    # ── Clear ─────────────────────────────────────────
    def _clear(self):
        self.word_list = []
        self._clear_preview()
        for k in self.stat_vars:
            self.stat_vars[k].set(
                "0 B" if k == "Size" else "0")
        self.progress["value"] = 0
        self.progress_label.configure(
            text="0%  ·  waiting...")
        self._set_status("Cleared · Ready")

    def _clear_preview(self):
        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        self.preview_box.configure(state="disabled")