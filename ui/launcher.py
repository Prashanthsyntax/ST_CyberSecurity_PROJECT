import tkinter as tk
from tkinter import ttk, font
from PIL import Image, ImageTk, ImageFilter
import os
import webbrowser

BG_DARK    = "#1e1e2e"
BG_CARD    = "#2a2a3e"
BG_ACCENT  = "#1e3a4a"
FG_PRIMARY = "#cbd5e1"
FG_MUTED   = "#64748b"
FG_BLUE    = "#7dd3fc"
FG_GREEN   = "#22c55e"
BORDER     = "#3a3a50"
BTN_BLUE   = "#185FA5"


class LauncherFrame(tk.Frame):
    def __init__(self, parent, nav):
        super().__init__(parent, bg=BG_DARK)
        self.nav = nav
        self.mode = tk.StringVar(value="Beginner")
        
        # self._build_titlebar() # Navigation bar is now handled by nav_manager
        self._build_header()
        self._build_mode_selector()
        self._build_module_grid()
        self._build_quick_start()
        self._build_statusbar()

    def _build_header(self):
        # Container frame for logo and text
        header_container = tk.Frame(self, bg=BG_DARK)
        header_container.pack(fill="x", pady=(20, 0), padx=20)

        # Logo placement
        try:
            logo_path = os.path.join("resources", "logo.png")
            if os.path.exists(logo_path):
                img = Image.open(logo_path)
                # Larger size for better detail visibility
                img = img.resize((120, 120), Image.LANCZOS)
                # Apply sharpening for crisp edges
                img = img.filter(ImageFilter.SHARPEN)
                self.logo_img = ImageTk.PhotoImage(img)
                logo_label = tk.Label(header_container, image=self.logo_img, bg=BG_DARK)
                logo_label.pack(side="left", padx=(0, 25))
        except Exception as e:
            print(f"Error loading logo: {e}")

        # Text container
        text_frame = tk.Frame(header_container, bg=BG_DARK)
        text_frame.pack(side="left", fill="both")

        tk.Label(text_frame, text="CRYPTX",
                 bg=BG_DARK, fg=FG_BLUE,
                 font=("Courier", 24, "bold")).pack(anchor="w")
        tk.Label(text_frame,
                 text="AI-Powered Password Vulnerability Analyzer"
                      "\nEthical security testing toolkit  ·  Authorized use only",
                 bg=BG_DARK, fg=FG_MUTED, justify="left",
                 font=("Courier", 9)).pack(anchor="w", pady=(2, 0))

        # Project Info Button (Right side)
        info_btn = tk.Button(
            header_container,
            text="[ PROJECT INFO ]",
            bg=BG_DARK,
            fg=FG_BLUE,
            font=("Courier", 10, "bold"),
            relief="flat",
            highlightthickness=1,
            highlightbackground=FG_BLUE,
            cursor="hand2",
            padx=15,
            pady=8,
            activebackground=BG_ACCENT,
            activeforeground="#ffffff",
            command=self._open_project_info
        )
        info_btn.pack(side="right", anchor="n")
        tk.Frame(self, bg=BORDER,
                 height=1).pack(fill="x",
                                padx=20, pady=14)

    def _build_mode_selector(self):
        outer = tk.Frame(self, bg=BG_DARK)
        outer.pack(fill="x", padx=20)
        tk.Label(outer, text="SELECT MODE",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(
                 anchor="w", pady=(0, 8))
        row = tk.Frame(outer, bg=BG_DARK)
        row.pack(fill="x")

        modes = [
            ("Beginner",    "Step-by-step\nguidance"),
            ("Advanced",    "Full control\n& options"),
            ("Report Mode", "Audit &\ncompliance"),
        ]
        self.mode_btns = {}
        for name, desc in modes:
            btn = tk.Frame(row, bg=BG_CARD,
                           relief="flat",
                           highlightthickness=1,
                           highlightbackground=BORDER)
            btn.pack(side="left", expand=True,
                     fill="x", padx=4)
            tk.Label(btn, text=name,
                     bg=BG_CARD, fg=FG_PRIMARY,
                     font=("Courier", 10, "bold")
                     ).pack(pady=(10, 2))
            tk.Label(btn, text=desc,
                     bg=BG_CARD, fg=FG_MUTED,
                     font=("Courier", 8),
                     justify="center"
                     ).pack(pady=(0, 10))
            btn.bind("<Button-1>",
                     lambda e, n=name:
                     self._select_mode(n))
            for child in btn.winfo_children():
                child.bind("<Button-1>",
                           lambda e, n=name:
                           self._select_mode(n))
            self.mode_btns[name] = btn
        self._select_mode("Beginner")

    def _select_mode(self, name):
        self.mode.set(name)
        for n, btn in self.mode_btns.items():
            if n == name:
                btn.configure(
                    highlightbackground=FG_BLUE,
                    bg=BG_ACCENT)
                for c in btn.winfo_children():
                    c.configure(bg=BG_ACCENT,
                                fg=FG_BLUE)
            else:
                btn.configure(
                    highlightbackground=BORDER,
                    bg=BG_CARD)
                for c in btn.winfo_children():
                    c.configure(
                        bg=BG_CARD,
                        fg=FG_PRIMARY
                        if "bold" in str(c.cget("font"))
                        else FG_MUTED)

    def _build_module_grid(self):
        outer = tk.Frame(self, bg=BG_DARK)
        outer.pack(fill="x", padx=20, pady=(16, 0))
        tk.Label(outer, text="OPEN MODULE",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(
                 anchor="w", pady=(0, 8))

        modules = [
            ("Hash Cracker",
             "MD5 · SHA1 · SHA256 · NTLM",
             self._open_hash_cracker),
            ("Hybrid Attack",
             "Dict + rules + brute force",
             self._open_hybrid),
            ("Wordlist Generator",
             "AI-assisted smart lists",
             self._open_wordlist),
            ("AI Training",
             "Train Markov + N-gram models",
             self._open_ai_training),
            ("Rainbow Tables",
             "Lookup & manage tables",
             self._open_rainbow),
            ("Analytics",
             "Strength dashboard",
             self._open_analytics),
            ("Reports & Logs",
             "Export · compliance",
             self._open_reports),
            ("Rule Engine",
             "Hashcat-style rules",
             self._open_rules),
        ]

        grid = tk.Frame(outer, bg=BG_DARK)
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        for i, (name, hint, cmd) in enumerate(modules):
            card = tk.Frame(grid, bg=BG_CARD,
                            relief="flat",
                            highlightthickness=1,
                            highlightbackground=BORDER,
                            cursor="hand2")
            card.grid(row=i // 2, column=i % 2,
                      sticky="ew", padx=4, pady=4)

            inner = tk.Frame(card, bg=BG_CARD)
            inner.pack(fill="x", padx=12, pady=10)

            tk.Label(inner, text=name,
                     bg=BG_CARD, fg=FG_PRIMARY,
                     font=("Courier", 10, "bold")
                     ).pack(anchor="w")
            tk.Label(inner, text=hint,
                     bg=BG_CARD, fg=FG_MUTED,
                     font=("Courier", 8)
                     ).pack(anchor="w")

            card.bind("<Button-1>",
                      lambda e, c=cmd: c())
            card.bind(
                "<Enter>",
                lambda e, f=card:
                f.configure(
                    highlightbackground=FG_BLUE))
            card.bind(
                "<Leave>",
                lambda e, f=card:
                f.configure(
                    highlightbackground=BORDER))
            for w in (card.winfo_children()
                      + inner.winfo_children()):
                w.bind("<Button-1>",
                       lambda e, c=cmd: c())

    def _build_quick_start(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=20, pady=16)
        tk.Button(frame,
                  text="▶  Start Quick Crack",
                  bg=BTN_BLUE, fg="#e0f0ff",
                  font=("Courier", 12, "bold"),
                  relief="flat", bd=0,
                  activebackground="#1a6fbf",
                  activeforeground="#ffffff",
                  cursor="hand2",
                  command=self._open_hash_cracker
                  ).pack(fill="x", ipady=10)

    def _build_statusbar(self):
        bar = tk.Frame(self, bg=BG_CARD,
                       height=30)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Label(bar, text="●",
                 bg=BG_CARD, fg=FG_GREEN,
                 font=("Courier", 10)).pack(
                 side="left", padx=(12, 4))
        tk.Label(bar,
                 text="Ready · No session active",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 9)).pack(side="left")
        tk.Label(bar,
                 text="v2.0 · Authorized use only",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 9)).pack(
                 side="right", padx=12)

    def _open_project_info(self):
        """Opens the local project info HTML page in the default browser."""
        try:
            html_path = os.path.abspath(os.path.join("resources", "project_info.html"))
            if os.path.exists(html_path):
                webbrowser.open_new_tab(f"file:///{html_path}")
            else:
                from tkinter import messagebox
                messagebox.showerror("Error", "Project info file not found.")
        except Exception as e:
            print(f"Error opening project info: {e}")

    # ── Module openers ────────────────────────────────
    def _open_hash_cracker(self):
        from ui.hash_cracker_window import HashCrackerFrame
        self.nav.push_view(HashCrackerFrame)

    def _open_hybrid(self):
        from ui.hybrid_attack_window import HybridAttackFrame
        self.nav.push_view(HybridAttackFrame)

    def _open_wordlist(self):
        from ui.wordlist_generator_window import WordlistGeneratorFrame
        self.nav.push_view(WordlistGeneratorFrame)

    def _open_ai_training(self):
        from ui.ai_training_window import AITrainingFrame
        self.nav.push_view(AITrainingFrame)

    def _open_rainbow(self):
        from ui.rainbow_table_window import RainbowTableFrame
        self.nav.push_view(RainbowTableFrame)

    def _open_analytics(self):
        from ui.analytics_window import AnalyticsFrame
        self.nav.push_view(AnalyticsFrame)

    def _open_reports(self):
        from ui.reports_window import ReportsFrame
        self.nav.push_view(ReportsFrame)

    def _open_rules(self):
        from ui.rule_engine_window import RuleEngineFrame
        self.nav.push_view(RuleEngineFrame)
