import tkinter as tk
from tkinter import ttk
import os
from PIL import Image, ImageTk, ImageFilter

# ── Colour palette (matches launcher) ─────────────────────────────────────────
BG_DARK    = "#1e1e2e"
BG_CARD    = "#2a2a3e"
BG_ACCENT  = "#1e3a4a"
BG_MODULE  = "#12121f"
FG_PRIMARY = "#cbd5e1"
FG_MUTED   = "#64748b"
FG_BLUE    = "#7dd3fc"
FG_GREEN   = "#22c55e"
FG_PURPLE  = "#a78bfa"
BORDER     = "#3a3a50"
BTN_BLUE   = "#185FA5"


# ── Data ───────────────────────────────────────────────────────────────────────
MODULES = [
    ("Window 1 — GUI Launcher",
     "Beginner friendly main interface with tool selection\nand mode switch (Beginner / Advanced)."),
    ("Window 2 — Hash Detection",
     "Automatically detects hash algorithms including\nMD5, SHA1, SHA256, SHA512 and NTLM."),
    ("Window 3 — Hybrid Attack Engine",
     "Combines rainbow tables, dictionary attacks,\nrule mutations, and brute force techniques."),
    ("Window 4 — AI Wordlist Generator",
     "Generates personalized password wordlists using\ntarget metadata like names and birthdays."),
    ("Window 5 — Rule Engine",
     "Applies transformations such as append, prepend,\nreverse, uppercase, lowercase and duplication."),
    ("Window 6 — Rainbow Table Manager",
     "Manages rainbow tables and provides statistics\non coverage and hash database size."),
    ("Window 7 — Analytics Dashboard",
     "Displays password strength metrics, crack statistics,\nand algorithm performance charts."),
    ("Window 8 — Reporting System",
     "Generates professional security audit reports\nwith logs and compliance documentation."),
]

PROJECT_DETAILS = [
    ("Project Name",      "CryptX: AI-Powered Password Vulnerability Analyzer"),
    ("Category",          "Cyber Security / Password Analysis Tool"),
    ("Technologies",      "Python, Tkinter GUI, Hash Algorithms, AI Wordlist Generation"),
    ("Start Date",        "01 January 2026"),
    ("Completion Date",   "31 May 2026"),
    ("Status",            "Completed"),
]

DEVELOPERS = [
    ("C Parasuraman",        "ST#IS#9059", "parasuramanm492@gmail.com"),
    ("S Sai Manikanta Rao",  "ST#IS#9060", "sainenisaimanikantarao@gmail.com"),
    ("P Prashanth",          "ST#IS#9061", "prashanthpendem2323@gmail.com"),
    ("Sai Nikhil",           "ST#IS#9062", "sainikhilyadav8@gmail.com"),
    ("V Rishika",            "ST#IS#9072", "rishikav0105@gmail.com"),
]

COMPANY_INFO = [
    ("Organization",       "Supraja Technologies"),
    ("Internship Domain",  "Cyber Security"),
    ("Email",              "contact@suprajatechnologies.com"),
]


# ── Helper widgets ─────────────────────────────────────────────────────────────
def _section_label(parent, text):
    """Blue section heading with bottom border."""
    tk.Label(
        parent, text=text,
        bg=BG_CARD, fg=FG_BLUE,
        font=("Courier", 13, "bold"),
        anchor="w"
    ).pack(fill="x", padx=16, pady=(16, 0))
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(6, 10))


def _card(parent):
    """Return a card frame with hover glow."""
    card = tk.Frame(
        parent, bg=BG_CARD,
        highlightthickness=1,
        highlightbackground=BORDER
    )
    card.pack(fill="x", padx=24, pady=8)

    def _on_enter(e):
        card.configure(highlightbackground=FG_BLUE)

    def _on_leave(e):
        card.configure(highlightbackground=BORDER)

    card.bind("<Enter>", _on_enter)
    card.bind("<Leave>", _on_leave)
    return card


def _table(parent, headers, rows, special_col=None, special_vals=None):
    """Simple grid-based table using Labels."""
    tbl = tk.Frame(parent, bg=BG_CARD)
    tbl.pack(fill="x", padx=16, pady=(0, 14))

    col_count = len(headers)
    for c in range(col_count):
        tbl.columnconfigure(c, weight=1)

    # Header row
    for c, h in enumerate(headers):
        tk.Label(
            tbl, text=h,
            bg="#0f172a", fg=FG_BLUE,
            font=("Courier", 10, "bold"),
            relief="flat", anchor="w",
            padx=10, pady=8,
            highlightthickness=1,
            highlightbackground=BORDER
        ).grid(row=0, column=c, sticky="nsew", padx=1, pady=1)

    # Data rows
    for r, row in enumerate(rows, start=1):
        for c, val in enumerate(row):
            is_special = (
                special_col is not None
                and c == special_col
                and special_vals is not None
                and val in special_vals
            )
            color = FG_GREEN if is_special else FG_PRIMARY
            bold  = "bold" if is_special else "normal"
            tk.Label(
                tbl, text=val,
                bg=BG_MODULE, fg=color,
                font=("Courier", 10, bold),
                relief="flat", anchor="w",
                padx=10, pady=7,
                highlightthickness=1,
                highlightbackground=BORDER
            ).grid(row=r, column=c, sticky="nsew", padx=1, pady=1)


# ── Main Frame ─────────────────────────────────────────────────────────────────
class ProjectInfoFrame(tk.Frame):
    """
    Drop-in replacement for the HTML project_info page.
    Usage with nav manager:
        self.nav.push_view(ProjectInfoFrame)
    Usage standalone:
        root = tk.Tk(); ProjectInfoFrame(root, nav=None).pack(fill="both", expand=True)
    """

    def __init__(self, parent, nav=None):
        super().__init__(parent, bg=BG_DARK)
        self.nav = nav
        self._build()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build(self):
        self._build_topbar()

        # Scrollable canvas
        canvas = tk.Canvas(self, bg=BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.inner = tk.Frame(canvas, bg=BG_DARK)
        self._win_id = canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>",
                        lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(self._win_id, width=e.width))

        # Mouse-wheel scrolling
        def _on_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_wheel)

        # Sections
        self._build_title_section()
        self._build_overview_section()
        self._build_modules_section()
        self._build_details_section()
        self._build_developers_section()
        self._build_company_section()
        self._build_status_bar()
        self._build_footer()

    # ── Top navigation bar ────────────────────────────────────────────────────
    def _build_topbar(self):
        bar = tk.Frame(self, bg=BG_CARD, height=50)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        # Logo
        try:
            logo_path = os.path.join("resources", "logo.png")
            if os.path.exists(logo_path):
                img = Image.open(logo_path).resize((36, 36), Image.LANCZOS)
                self._topbar_logo = ImageTk.PhotoImage(img)
                tk.Label(bar, image=self._topbar_logo,
                         bg=BG_CARD).pack(side="left", padx=(14, 6), pady=7)
        except Exception:
            pass

        tk.Label(bar, text="CRYPTX SECURITY",
                 bg=BG_CARD, fg=FG_BLUE,
                 font=("Courier", 13, "bold")).pack(side="left", pady=7)

        # Back button (only shown when nav is available)
        if self.nav:
            tk.Button(
                bar, text="◀  BACK",
                bg=BG_CARD, fg=FG_BLUE,
                font=("Courier", 10, "bold"),
                relief="flat", bd=0,
                activebackground=BG_ACCENT,
                activeforeground="#ffffff",
                cursor="hand2",
                padx=14, pady=6,
                command=self.nav.pop_view
            ).pack(side="right", padx=10, pady=7)

    # ── Title ─────────────────────────────────────────────────────────────────
    def _build_title_section(self):
        frm = tk.Frame(self.inner, bg=BG_DARK)
        frm.pack(fill="x", pady=(30, 10), padx=24)

        # Right logo (supraja)
        try:
            right_logo_path = os.path.join("resources", "supraja.png")
            if os.path.exists(right_logo_path):
                img = Image.open(right_logo_path).resize((80, 40), Image.LANCZOS)
                self._right_logo = ImageTk.PhotoImage(img)
                tk.Label(frm, image=self._right_logo,
                         bg=BG_DARK).pack(side="right", padx=(0, 10))
        except Exception:
            pass

        tk.Label(
            frm, text="CRYPTX",
            bg=BG_DARK, fg=FG_BLUE,
            font=("Courier", 36, "bold"),
            anchor="center"
        ).pack(fill="x")

        tk.Label(
            frm, text="AI Powered Password Vulnerability Analyzer",
            bg=BG_DARK, fg=FG_MUTED,
            font=("Courier", 11),
            anchor="center"
        ).pack(fill="x", pady=(4, 0))

        tk.Frame(self.inner, bg=BORDER, height=1).pack(fill="x", padx=24, pady=18)

    # ── Overview ──────────────────────────────────────────────────────────────
    def _build_overview_section(self):
        card = _card(self.inner)
        _section_label(card, "Project Overview")

        overview_text = (
            "CryptX is an advanced cybersecurity toolkit designed to analyze password vulnerabilities "
            "and help organizations evaluate the strength of authentication systems.\n\n"
            "The system integrates multiple password cracking techniques such as dictionary attacks, "
            "brute force attacks, rule-based mutations, rainbow tables, and AI-assisted wordlist "
            "generation to simulate real-world attack scenarios.\n\n"
            "By combining intelligent analytics with automated attack strategies, CryptX helps "
            "security teams identify weak passwords, improve password policies, and strengthen "
            "organizational security against cyber threats."
        )

        tk.Label(
            card, text=overview_text,
            bg=BG_CARD, fg=FG_MUTED,
            font=("Courier", 10),
            justify="left", wraplength=900,
            anchor="w"
        ).pack(fill="x", padx=16, pady=(0, 18))

    # ── System Modules ────────────────────────────────────────────────────────
    def _build_modules_section(self):
        card = _card(self.inner)
        _section_label(card, "System Modules")

        grid = tk.Frame(card, bg=BG_CARD)
        grid.pack(fill="x", padx=12, pady=(0, 14))
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        for i, (title, desc) in enumerate(MODULES):
            mod = tk.Frame(
                grid, bg=BG_MODULE,
                highlightthickness=1,
                highlightbackground=BORDER
            )
            mod.grid(row=i // 2, column=i % 2,
                     sticky="nsew", padx=5, pady=5)

            tk.Label(mod, text=title,
                     bg=BG_MODULE, fg=FG_PURPLE,
                     font=("Courier", 10, "bold"),
                     anchor="w"
                     ).pack(fill="x", padx=12, pady=(10, 4))
            tk.Label(mod, text=desc,
                     bg=BG_MODULE, fg=FG_MUTED,
                     font=("Courier", 9),
                     justify="left", anchor="w"
                     ).pack(fill="x", padx=12, pady=(0, 10))

            def _enter(e, w=mod):
                w.configure(highlightbackground=FG_PURPLE)

            def _leave(e, w=mod):
                w.configure(highlightbackground=BORDER)

            mod.bind("<Enter>", _enter)
            mod.bind("<Leave>", _leave)

    # ── Project Details ───────────────────────────────────────────────────────
    def _build_details_section(self):
        card = _card(self.inner)
        _section_label(card, "Project Details")
        _table(
            card,
            headers=["Field", "Value"],
            rows=PROJECT_DETAILS,
            special_col=1,
            special_vals={"Completed"}
        )

    # ── Developer Team ────────────────────────────────────────────────────────
    def _build_developers_section(self):
        card = _card(self.inner)
        _section_label(card, "Developer Team")
        _table(
            card,
            headers=["Name", "Employee ID", "Email"],
            rows=DEVELOPERS
        )

    # ── Company Information ───────────────────────────────────────────────────
    def _build_company_section(self):
        card = _card(self.inner)
        _section_label(card, "Company Information")
        _table(
            card,
            headers=["Field", "Value"],
            rows=COMPANY_INFO
        )

    # ── Status bar ────────────────────────────────────────────────────────────
    def _build_status_bar(self):
        frm = tk.Frame(self.inner, bg=BG_DARK)
        frm.pack(fill="x", padx=24, pady=(16, 4))

        tk.Label(frm, text="●",
                 bg=BG_DARK, fg=FG_GREEN,
                 font=("Courier", 12)).pack(side="left", padx=(0, 8))
        tk.Label(frm,
                 text="SYSTEM OPERATIONAL — PROJECT COMPLETED",
                 bg=BG_DARK, fg=FG_GREEN,
                 font=("Courier", 10, "bold")).pack(side="left")

    # ── Footer ────────────────────────────────────────────────────────────────
    def _build_footer(self):
        tk.Frame(self.inner, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(10, 0))
        tk.Label(
            self.inner,
            text="© 2026 CRYPTX SECURITY  ·  SUPRAJA TECHNOLOGIES",
            bg=BG_DARK, fg=FG_MUTED,
            font=("Courier", 9)
        ).pack(pady=20)


# ── Standalone test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    root.title("CryptX — Project Info")
    root.geometry("1000x700")
    root.configure(bg=BG_DARK)
    ProjectInfoFrame(root, nav=None).pack(fill="both", expand=True)
    root.mainloop()