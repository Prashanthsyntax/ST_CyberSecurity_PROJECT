import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time

from core.rule_engine import (
    apply_rule,
    apply_rules_to_wordlist,
    parse_rule_file,
    BUILT_IN_RULESETS,
)

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

# All clickable rule tokens with descriptions
RULE_TOKENS = [
    ("l",    "Lowercase all",      "Pass→pass"),
    ("u",    "Uppercase all",      "pass→PASS"),
    ("c",    "Capitalise",         "pass→Pass"),
    ("C",    "Lower first, up rest","Pass→pASS"),
    ("t",    "Toggle case",        "Pass→pASS"),
    ("r",    "Reverse",            "pass→ssap"),
    ("d",    "Duplicate",          "pass→passpass"),
    ("f",    "Reflect",            "pass→passssap"),
    ("q",    "Double each char",   "pass→ppaassss"),
    ("$1",   "Append '1'",         "pass→pass1"),
    ("$2",   "Append '2'",         "pass→pass2"),
    ("$3",   "Append '3'",         "pass→pass3"),
    ("$!",   "Append '!'",         "pass→pass!"),
    ("$@",   "Append '@'",         "pass→pass@"),
    ("$#",   "Append '#'",         "pass→pass#"),
    ("^1",   "Prepend '1'",        "pass→1pass"),
    ("^!",   "Prepend '!'",        "pass→!pass"),
    ("sa@",  "Replace a→@",        "pass→p@ss"),
    ("se3",  "Replace e→3",        "test→t3st"),
    ("si1",  "Replace i→1",        "miss→m1ss"),
    ("so0",  "Replace o→0",        "boot→b00t"),
    ("ss$",  "Replace s→$",        "pass→pa$$"),
    ("st7",  "Replace t→7",        "test→7es7"),
    (">6",   "Keep if len>6",      "filter short"),
    ("<10",  "Keep if len<10",     "filter long"),
    ("$1$2$3","Append '123'",      "pass→pass123"),
    ("$2$0$2$4","Append '2024'",   "pass→pass2024"),
    ("$2$0$2$3","Append '2023'",   "pass→pass2023"),
]


class RuleEngineFrame(tk.Frame):
    def __init__(self, parent, nav=None):
        super().__init__(parent, bg=BG_DARK)
        self.nav = nav

        self.wordlist_file = tk.StringVar()
        self.running       = False
        self.output_words  = []

        self._build_titlebar()
        self._build_files_section()
        self._build_main_area()
        self._build_stats_bar()
        self._build_progress()
        self._build_buttons()
        self._build_statusbar()
        self._build_output()

        # Load default preview word
        self._update_live_preview()

    # ── Title bar ────────────────────────────────────
    def _build_titlebar(self):
        bar = tk.Frame(self, bg=BG_CARD, height=36)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        for color in ["#ff5f57","#febc2e","#28c840"]:
            tk.Label(bar, bg=color, width=2).pack(
                side="left",
                padx=(8 if color=="#ff5f57" else 4,0),
                pady=8)
        tk.Label(bar,
                 text="Window 5 — Rule Engine  "
                      "(Hashcat-compatible syntax)",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier",10)).pack(
                 side="left", padx=12)

    # ── File + ruleset selector ───────────────────────
    def _build_files_section(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(12, 0))

        row = tk.Frame(frame, bg=BG_DARK)
        row.pack(fill="x")

        tk.Label(row, text="WORDLIST:",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier",9)).pack(
                 side="left", padx=(0,6))

        tk.Entry(row, textvariable=self.wordlist_file,
                 bg=BG_CARD, fg=FG_PRIMARY,
                 insertbackground=FG_BLUE,
                 relief="flat",
                 highlightthickness=1,
                 highlightbackground=BORDER,
                 font=("Courier",10),
                 width=50).pack(side="left",
                                ipady=5, padx=(0,8))

        tk.Button(row, text="Browse",
                  bg=BG_CARD, fg=FG_BLUE,
                  relief="flat", font=("Courier",9),
                  activebackground=BG_ACCENT,
                  cursor="hand2",
                  command=self._browse_wordlist
                  ).pack(side="left", padx=(0,16))

        # Preset ruleset selector
        tk.Label(row, text="PRESET:",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier",9)).pack(
                 side="left", padx=(0,6))

        self.preset_var = tk.StringVar(
            value="— select preset —")
        preset_menu = ttk.Combobox(
            row,
            textvariable=self.preset_var,
            values=["— select preset —"]
                   + list(BUILT_IN_RULESETS.keys()),
            state="readonly",
            font=("Courier",9),
            width=20)
        preset_menu.pack(side="left", padx=(0,8))
        preset_menu.bind("<<ComboboxSelected>>",
                         self._load_preset)

    def _browse_wordlist(self):
        path = filedialog.askopenfilename(
            filetypes=[("Text files","*.txt"),
                       ("All files","*.*")])
        if path:
            self.wordlist_file.set(path)

    def _load_preset(self, event=None):
        name = self.preset_var.get()
        if name in BUILT_IN_RULESETS:
            rules = BUILT_IN_RULESETS[name]
            self.rule_editor.delete("1.0", "end")
            self.rule_editor.insert(
                "end", "\n".join(rules))
            self._update_live_preview()
            self._set_status(
                f"Loaded preset: {name} · "
                f"{len(rules)} rules")

    # ── Main 2-column area ────────────────────────────
    def _build_main_area(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="both", expand=True, padx=16, pady=(12, 0))
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        # ── Left: rule token library ──────────────────
        left = tk.Frame(frame, bg=BG_DARK)
        left.grid(row=0, column=0,
                  sticky="nsew", padx=(0,6))

        tk.Label(left,
                 text="RULE TOKENS — click to add "
                      "to editor",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier",8)).pack(
                 anchor="w", pady=(0,5))

        # Scrollable token list
        token_frame = tk.Frame(left, bg=BG_CARD,
                                highlightthickness=1,
                                highlightbackground=BORDER)
        token_frame.pack(fill="both")

        canvas = tk.Canvas(token_frame,
                           bg=BG_CARD,
                           highlightthickness=0,
                           height=220)
        vsb = tk.Scrollbar(token_frame,
                           orient="vertical",
                           command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both",
                    expand=True)
        vsb.pack(side="right", fill="y")

        inner = tk.Frame(canvas, bg=BG_CARD)
        canvas.create_window((0,0), window=inner,
                              anchor="nw")

        for token, desc, example in RULE_TOKENS:
            row = tk.Frame(inner, bg=BG_CARD)
            row.pack(fill="x", padx=6, pady=1)

            tk.Label(row, text=token,
                     bg=BG_CARD, fg=FG_PURPLE,
                     font=("Courier",9,"bold"),
                     width=10, anchor="w"
                     ).pack(side="left")

            tk.Label(row, text=desc,
                     bg=BG_CARD, fg=FG_PRIMARY,
                     font=("Courier",9),
                     width=18, anchor="w"
                     ).pack(side="left")

            tk.Label(row, text=example,
                     bg=BG_CARD, fg=FG_GREEN,
                     font=("Courier",8),
                     width=18, anchor="w"
                     ).pack(side="left")

            tk.Button(row, text="+",
                      bg=BG_ACCENT, fg=FG_BLUE,
                      relief="flat",
                      font=("Courier",9,"bold"),
                      cursor="hand2",
                      padx=6,
                      command=lambda t=token:
                      self._add_token(t)
                      ).pack(side="right", padx=4)

        # Delayed update ensures the scrollregion is calculated after the transition
        self.after(200, lambda: (
            inner.update_idletasks(),
            canvas.configure(scrollregion=canvas.bbox("all"))
        ))

        # ── Right: rule editor + live preview ─────────
        right = tk.Frame(frame, bg=BG_DARK)
        right.grid(row=0, column=1,
                   sticky="nsew", padx=(6,0))

        tk.Label(right,
                 text="RULE EDITOR — one rule per line",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier",8)).pack(
                 anchor="w", pady=(0,4))

        editor_frame = tk.Frame(right, bg=BG_CARD,
                                 highlightthickness=1,
                                 highlightbackground=BORDER)
        editor_frame.pack(fill="both")

        self.rule_editor = tk.Text(
            editor_frame,
            bg=BG_EDITOR, fg=FG_PURPLE,
            insertbackground=FG_BLUE,
            font=("Courier",11),
            relief="flat",
            height=10,
            padx=10, pady=8)

        esb = tk.Scrollbar(editor_frame,
                           command=self.rule_editor.yview,
                           bg=BG_CARD)
        self.rule_editor.configure(
            yscrollcommand=esb.set)
        self.rule_editor.pack(side="left",
                              fill="both", expand=True)
        esb.pack(side="right", fill="y")

        # Default rules
        default_rules = "\n".join([
            "l", "u", "c", "$1", "$2", "$3",
            "$!", "c $1", "c $!", "sa@ se3",
            "r", "$2$0$2$4",
        ])
        self.rule_editor.insert("1.0", default_rules)
        self.rule_editor.bind(
            "<KeyRelease>",
            lambda e: self._update_live_preview())

        # Rule file load/save buttons
        btn_row = tk.Frame(right, bg=BG_DARK)
        btn_row.pack(fill="x", pady=(6,0))

        for txt, cmd in [
            ("Load .rule", self._load_rule_file),
            ("Save ruleset", self._save_rule_file),
            ("Clear editor", self._clear_editor),
        ]:
            tk.Button(btn_row, text=txt,
                      bg=BG_CARD, fg=FG_BLUE,
                      relief="flat",
                      font=("Courier",9),
                      highlightthickness=1,
                      highlightbackground=BORDER,
                      activebackground=BG_ACCENT,
                      cursor="hand2",
                      command=cmd
                      ).pack(side="left",
                             padx=(0,4), ipady=4,
                             ipadx=6)

        # Live preview
        tk.Label(right,
                 text="LIVE PREVIEW — "
                      "test word + rules",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier",8)).pack(
                 anchor="w", pady=(10,4))

        preview_top = tk.Frame(right, bg=BG_DARK)
        preview_top.pack(fill="x")

        tk.Label(preview_top,
                 text="Test word:",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier",9)).pack(
                 side="left")

        self.preview_word = tk.StringVar(
            value="password")
        tk.Entry(preview_top,
                 textvariable=self.preview_word,
                 bg=BG_CARD, fg=FG_PRIMARY,
                 insertbackground=FG_BLUE,
                 relief="flat",
                 highlightthickness=1,
                 highlightbackground=BORDER,
                 font=("Courier",10),
                 width=16).pack(side="left",
                                padx=6, ipady=4)

        self.preview_word.trace_add(
            "write",
            lambda *a: self._update_live_preview())

        preview_frame = tk.Frame(
            right, bg=BG_CARD,
            highlightthickness=1,
            highlightbackground=BORDER)
        preview_frame.pack(fill="both",
                           expand=True, pady=(4,0))

        self.preview_box = tk.Text(
            preview_frame,
            bg="#0f0f1e", fg=FG_GREEN,
            font=("Courier",9),
            relief="flat",
            state="disabled",
            height=6,
            padx=8, pady=6)
        self.preview_box.pack(
            fill="both", expand=True)

    def _add_token(self, token: str):
        """Add a token to the rule editor."""
        self.rule_editor.insert("end",
                                f"\n{token}")
        self.rule_editor.see("end")
        self._update_live_preview()

    def _update_live_preview(self):
        """Live preview of rules applied to test word."""
        word    = self.preview_word.get().strip() \
                  or "password"
        content = self.rule_editor.get(
            "1.0", "end").strip()
        rules   = [r.strip() for r in
                   content.splitlines()
                   if r.strip()
                   and not r.strip().startswith("#")]

        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")

        seen = set()
        for rule in rules[:20]:
            out = apply_rule(word, rule)
            if out is not None and out not in seen:
                seen.add(out)
                self.preview_box.insert(
                    "end",
                    f"  {word}  →  [{rule}]  "
                    f"→  {out}\n")

        self.preview_box.configure(state="disabled")

        # Update rule count stat
        if hasattr(self, "stat_vars"):
            self.stat_vars["Rules"].set(
                str(len(rules)))

    # ── Stats bar ─────────────────────────────────────
    def _build_stats_bar(self):
        outer = tk.Frame(self, bg=BG_DARK)
        outer.pack(fill="x", padx=16, pady=(12, 0))

        self.stat_vars = {
            "Rules":      tk.StringVar(value="0"),
            "Words in":   tk.StringVar(value="0"),
            "Words out":  tk.StringVar(value="0"),
            "Multiplier": tk.StringVar(value="0x"),
            "Time":       tk.StringVar(value="0.0s"),
        }
        colors = {
            "Rules":      FG_BLUE,
            "Words in":   FG_GREEN,
            "Words out":  FG_PURPLE,
            "Multiplier": FG_AMBER,
            "Time":       FG_PRIMARY,
        }
        for label, var in self.stat_vars.items():
            card = tk.Frame(frame, bg=BG_CARD,
                            highlightthickness=1,
                            highlightbackground=BORDER)
            card.pack(side="left", expand=True,
                      fill="x", padx=4)
            tk.Label(card, textvariable=var,
                     bg=BG_CARD, fg=colors[label],
                     font=("Courier",14,"bold")
                     ).pack(pady=(8,2))
            tk.Label(card, text=label,
                     bg=BG_CARD, fg=FG_MUTED,
                     font=("Courier",8)
                     ).pack(pady=(0,8))

    # ── Progress bar ──────────────────────────────────
    def _build_progress(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(6,0))

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
            frame, text="0%  ·  waiting...",
            bg=BG_DARK, fg=FG_MUTED,
            font=("Courier",8))
        self.progress_label.pack(anchor="w", pady=2)

    # ── Buttons ───────────────────────────────────────
    def _build_buttons(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(6,6))

        self.apply_btn = tk.Button(
            frame,
            text="▶  Apply Rules & Generate",
            bg=BTN_BLUE, fg="#e0f0ff",
            font=("Courier",12,"bold"),
            relief="flat",
            highlightthickness=1,
            highlightbackground=BTN_BLUE,
            activebackground="#1a6fbf",
            activeforeground="#ffffff",
            cursor="hand2",
            command=self._apply_rules)
        self.apply_btn.pack(
            side="left", expand=True,
            fill="x", padx=(0,6), ipady=10)

        tk.Button(frame,
                  text="Save Output",
                  bg=BG_DARK, fg=FG_PRIMARY,
                  font=("Courier",11),
                  relief="flat",
                  highlightthickness=1,
                  highlightbackground=BORDER,
                  activebackground=BG_CARD,
                  cursor="hand2",
                  command=self._save_output
                  ).pack(side="left", expand=True,
                         fill="x", padx=3, ipady=10)

        tk.Button(frame,
                  text="Send to Cracker",
                  bg=BG_DARK, fg=FG_GREEN,
                  font=("Courier",11),
                  relief="flat",
                  highlightthickness=1,
                  highlightbackground=BORDER,
                  activebackground=BG_CARD,
                  cursor="hand2",
                  command=self._send_to_cracker
                  ).pack(side="left", expand=True,
                         fill="x", padx=3, ipady=10)

        tk.Button(frame,
                  text="Clear",
                  bg=BG_DARK, fg=FG_MUTED,
                  font=("Courier",11),
                  relief="flat",
                  highlightthickness=1,
                  highlightbackground=BORDER,
                  activebackground=BG_CARD,
                  cursor="hand2",
                  command=self._clear
                  ).pack(side="left", expand=True,
                         fill="x", padx=(3,0),
                         ipady=10)

    # ── Status bar ────────────────────────────────────
    def _build_statusbar(self):
        bar = tk.Frame(self, bg=BG_CARD,
                       height=25)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        tk.Label(bar, text="●",
                 bg=BG_CARD, fg=FG_GREEN,
                 font=("Courier",10)).pack(
                 side="left", padx=(12,4))

        self.status_var = tk.StringVar(
            value="Ready · Load wordlist, "
                  "set rules, click Apply")
        tk.Label(bar,
                 textvariable=self.status_var,
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier",9)).pack(side="left")

        tk.Label(bar,
                 text="Hashcat-compatible rule syntax",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier",9)).pack(
                 side="right", padx=12)

    def _set_status(self, msg):
        self.status_var.set(msg)

    # ── Output box — fills remaining space ────────────
    def _build_output(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="both", expand=True,
                   padx=16, pady=(4,4))

        tk.Label(frame,
                 text="OUTPUT — mutated wordlist",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier",8)).pack(
                 anchor="w", pady=(0,4))

        out_frame = tk.Frame(frame, bg=BG_CARD,
                              highlightthickness=1,
                              highlightbackground=BORDER)
        out_frame.pack(fill="both", expand=True)

        self.output_box = tk.Text(
            out_frame,
            bg=BG_EDITOR, fg=FG_GREEN,
            font=("Courier",10),
            relief="flat",
            state="disabled",
            wrap="none",
            padx=10, pady=8)

        sb_v = tk.Scrollbar(out_frame,
                             orient="vertical",
                             command=self.output_box.yview,
                             bg=BG_CARD)
        sb_h = tk.Scrollbar(out_frame,
                             orient="horizontal",
                             command=self.output_box.xview,
                             bg=BG_CARD)
        self.output_box.configure(
            yscrollcommand=sb_v.set,
            xscrollcommand=sb_h.set)
        sb_v.pack(side="right", fill="y")
        sb_h.pack(side="bottom", fill="x")
        self.output_box.pack(side="left",
                             fill="both",
                             expand=True)

    # ── Apply rules core ──────────────────────────────
    def _apply_rules(self):
        if self.running:
            return

        wf = self.wordlist_file.get().strip()
        if not wf:
            messagebox.showwarning(
                "No Wordlist",
                "Please select a wordlist file.")
            return

        content = self.rule_editor.get(
            "1.0", "end").strip()
        rules   = [r.strip() for r in
                   content.splitlines()
                   if r.strip()
                   and not r.strip().startswith("#")]

        if not rules:
            messagebox.showwarning(
                "No Rules",
                "Please add at least one rule "
                "in the editor.")
            return

        self._clear_output()
        self.running = True
        self.apply_btn.configure(
            state="disabled",
            text="⏳  Applying rules...")

        threading.Thread(
            target=self._apply_worker,
            args=(wf, rules),
            daemon=True).start()

    def _apply_worker(self, wordlist_file, rules):
        start = time.time()

        try:
            with open(wordlist_file, "r",
                      encoding="latin-1") as f:
                wordlist = [
                    w.strip() for w in f
                    if w.strip()]
        except Exception as e:
            messagebox.showerror(
                "File Error", str(e))
            self.running = False
            return

        words_in = len(wordlist)
        self.after(0, lambda:
            self.stat_vars["Words in"].set(
                f"{words_in:,}"))
        self.after(0, lambda:
            self.stat_vars["Rules"].set(
                str(len(rules))))
        self.after(0, self._set_status,
                       f"Applying {len(rules)} rules "
                       f"to {words_in:,} words...")

        def cb(pct, count):
            elapsed = round(time.time() - start, 2)
            self.after(0,
                self._update_progress,
                pct, count, words_in, elapsed)

        results = apply_rules_to_wordlist(
            wordlist, rules, callback=cb)

        self.output_words = results
        elapsed = round(time.time() - start, 2)

        # Populate output box
        self.after(0,
            self._populate_output, results)

        # Update stats
        mult = (round(len(results) / words_in, 1)
                if words_in else 0)

        self.after(0, lambda: (
            self.stat_vars["Words out"].set(
                f"{len(results):,}"),
            self.stat_vars["Multiplier"].set(
                f"{mult}x"),
            self.stat_vars["Time"].set(
                f"{elapsed}s"),
            self.progress.__setitem__("value", 100),
            self.progress_label.configure(
                text=f"100%  ·  Done  ·  "
                     f"{len(results):,} words"),
            self._set_status(
                f"Done  ·  {len(results):,} words "
                f"generated  ·  {elapsed}s  ·  "
                f"{mult}x multiplier"),
            self.apply_btn.configure(
                state="normal",
                text="▶  Apply Rules & Generate"),
        ))
        self.running = False

    def _populate_output(self, results):
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        # Show first 5000 to keep UI responsive
        preview = results[:5000]
        self.output_box.insert(
            "end", "\n".join(preview))
        if len(results) > 5000:
            self.output_box.insert(
                "end",
                f"\n\n... and "
                f"{len(results)-5000:,} more "
                f"(save to file to see all)")
        self.output_box.configure(state="disabled")

    def _update_progress(self, pct, count,
                         total, elapsed):
        self.progress["value"] = pct
        self.progress_label.configure(
            text=f"{pct}%  ·  "
                 f"{count:,} words  ·  "
                 f"{elapsed}s")
        self.stat_vars["Words out"].set(
            f"{count:,}")
        self._set_status(
            f"Applying rules...  {pct}%  ·  "
            f"{count:,} words so far")

    # ── Load / save rule files ────────────────────────
    def _load_rule_file(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("Rule files","*.rule *.rules *.txt"),
                ("All files","*.*")])
        if not path:
            return
        with open(path, "r",
                  encoding="utf-8") as f:
            content = f.read()
        rules = parse_rule_file(content)
        self.rule_editor.delete("1.0", "end")
        self.rule_editor.insert(
            "end", "\n".join(rules))
        self._update_live_preview()
        self._set_status(
            f"Loaded {len(rules)} rules from "
            f"{path}")

    def _save_rule_file(self):
        content = self.rule_editor.get(
            "1.0", "end").strip()
        if not content:
            messagebox.showwarning(
                "Empty", "No rules to save.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".rule",
            filetypes=[
                ("Rule files","*.rule"),
                ("Text files","*.txt")],
            initialfile="custom.rule")
        if not path:
            return
        with open(path, "w",
                  encoding="utf-8") as f:
            f.write(content)
        messagebox.showinfo(
            "Saved", f"Rules saved to:\n{path}")

    # ── Save output ───────────────────────────────────
    def _save_output(self):
        if not self.output_words:
            messagebox.showwarning(
                "No Output",
                "Apply rules first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files","*.txt")],
            initialfile="mutated_wordlist.txt")
        if not path:
            return
        with open(path, "w",
                  encoding="utf-8") as f:
            f.write("\n".join(self.output_words))
        messagebox.showinfo(
            "Saved",
            f"{len(self.output_words):,} words "
            f"saved to:\n{path}")

    # ── Send to cracker ───────────────────────────────
    def _send_to_cracker(self):
        if not self.output_words:
            messagebox.showwarning(
                "No Output",
                "Apply rules first.")
            return
        import tempfile, os
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt",
            delete=False, encoding="utf-8")
        tmp.write("\n".join(self.output_words))
        tmp.close()
        messagebox.showinfo(
            "Ready for Cracker",
            f"Output saved to temp file:\n"
            f"{tmp.name}\n\n"
            f"Copy this path into Hash Cracker "
            f"or Hybrid Attack wordlist field.")

    def _clear_editor(self):
        self.rule_editor.delete("1.0", "end")
        self._update_live_preview()

    def _clear_output(self):
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.configure(state="disabled")

    def _clear(self):
        self.output_words = []
        self._clear_output()
        for k in self.stat_vars:
            self.stat_vars[k].set(
                "0x" if k == "Multiplier"
                else "0.0s" if k == "Time"
                else "0")
        self.progress["value"] = 0
        self.progress_label.configure(
            text="0%  ·  waiting...")
        self._set_status("Cleared · Ready")