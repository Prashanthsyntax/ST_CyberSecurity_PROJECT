import tkinter as tk
from tkinter import filedialog, messagebox
import os
import datetime
import hashlib
import random
import json
import csv

from core.session_logger import load_sessions, clear_sessions

# ── Palette ───────────────────────────────────────────────────────────────────
BG_DARK    = "#1e1e2e"
BG_CARD    = "#2a2a3e"
BG_ACCENT  = "#1e3a4a"
BG_GREEN   = "#1a3a2a"
FG_PRIMARY = "#cbd5e1"
FG_MUTED   = "#64748b"
FG_BLUE    = "#7dd3fc"
FG_GREEN   = "#22c55e"
FG_TEAL    = "#2dd4bf"
FG_YELLOW  = "#fbbf24"
FG_RED     = "#f87171"
BORDER     = "#3a3a50"
BORDER_GRN = "#2d6a4f"
BTN_GREEN  = "#166534"

SEVERITY_COLORS = {
    "Critical": FG_RED,
    "High":     FG_YELLOW,
    "Medium":   FG_BLUE,
    "Low":      FG_GREEN,
}

TYPE_LABELS = {
    "Hash Crack":  "Hash Cracker",
    "Hybrid":      "Hybrid Attack",
    "Wordlist":    "Wordlist Generator",
    "AI Training": "AI Training",
    "Rainbow":     "Rainbow Tables",
    "Analytics":   "Analytics",
    "Rule Engine": "Rule Engine",
    "Reports":     "Reports",
}


# ══════════════════════════════════════════════════════════════════════════════
class ReportsFrame(tk.Frame):
    """Report Mode — fully dynamic, reads from data/session_log.json"""

    def __init__(self, parent, nav):
        super().__init__(parent, bg=BG_DARK)
        self.nav = nav
        self._sessions   = load_sessions()
        self._active_tab = tk.StringVar(value="overview")

        self._build_header()
        self._build_tab_bar()
        self._build_content_area()
        self._build_statusbar()
        self._switch_tab("overview")

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=BG_DARK)
        hdr.pack(fill="x", padx=20, pady=(18, 0))

        left = tk.Frame(hdr, bg=BG_DARK)
        left.pack(side="left", fill="both", expand=True)

        total   = len(self._sessions)
        cracked = sum(s["details"].get("cracked", 0) for s in self._sessions)

        tk.Label(left, text="REPORT MODE  —  Audit & Compliance",
                 bg=BG_DARK, fg=FG_GREEN,
                 font=("Courier", 15, "bold")).pack(anchor="w")
        tk.Label(left,
                 text=f"Live data  ·  {total} sessions logged  ·  "
                      f"{cracked} hashes cracked  ·  source: data/session_log.json",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w", pady=(3, 0))

        right = tk.Frame(hdr, bg=BG_DARK)
        right.pack(side="right", anchor="n")
        for label, cmd in [("[ REFRESH ]",    self._refresh),
                            ("[ EXPORT ALL ]", self._export_all),
                            ("[ CLEAR LOG ]",  self._clear_log)]:
            tk.Button(right, text=label,
                      bg=BG_DARK, fg=FG_GREEN,
                      font=("Courier", 9, "bold"),
                      relief="flat",
                      highlightthickness=1,
                      highlightbackground=FG_GREEN,
                      cursor="hand2",
                      padx=10, pady=5,
                      activebackground=BG_GREEN,
                      activeforeground="#ffffff",
                      command=cmd).pack(side="left", padx=(6, 0))

        tk.Frame(self, bg=BORDER_GRN, height=1).pack(fill="x", padx=20, pady=12)

    # ── Tab bar ───────────────────────────────────────────────────────────────
    def _build_tab_bar(self):
        self._tab_frame = tk.Frame(self, bg=BG_DARK)
        self._tab_frame.pack(fill="x", padx=20)

        self._tab_btns = {}
        for key, label in [
            ("overview",   "Session Overview"),
            ("evidence",   "Evidence Log"),
            ("risk",       "Risk Scoring"),
            ("compliance", "Compliance"),
            ("report_gen", "Generate Report"),
            ("audit",      "Audit Trail"),
        ]:
            btn = tk.Label(self._tab_frame,
                           text=label,
                           bg=BG_DARK, fg=FG_MUTED,
                           font=("Courier", 9),
                           cursor="hand2",
                           padx=12, pady=7)
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda e, k=key: self._switch_tab(k))
            self._tab_btns[key] = btn

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(4, 0))

    def _switch_tab(self, key):
        self._active_tab.set(key)
        for k, btn in self._tab_btns.items():
            if k == key:
                btn.configure(fg=FG_GREEN, font=("Courier", 9, "bold"), bg=BG_GREEN)
            else:
                btn.configure(fg=FG_MUTED, font=("Courier", 9), bg=BG_DARK)
        for w in self._content.winfo_children():
            w.destroy()
        {
            "overview":   self._panel_overview,
            "evidence":   self._panel_evidence,
            "risk":       self._panel_risk,
            "compliance": self._panel_compliance,
            "report_gen": self._panel_report_gen,
            "audit":      self._panel_audit,
        }[key](self._content)

    # ── Scrollable content ────────────────────────────────────────────────────
    def _build_content_area(self):
        outer = tk.Frame(self, bg=BG_DARK)
        outer.pack(fill="both", expand=True, padx=20, pady=10)

        self._canvas = tk.Canvas(outer, bg=BG_DARK, highlightthickness=0)
        vsb = tk.Scrollbar(outer, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._content = tk.Frame(self._canvas, bg=BG_DARK)
        win_id = self._canvas.create_window((0, 0), window=self._content, anchor="nw")

        self._content.bind("<Configure>",
                           lambda e: self._canvas.configure(
                               scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
                          lambda e: self._canvas.itemconfig(win_id, width=e.width))

        # ── FIX: safe scroll handler that checks canvas still exists ──────────
        def _on_mousewheel(event):
            try:
                if self._canvas.winfo_exists():
                    self._canvas.yview_scroll(-1 * (event.delta // 120), "units")
            except tk.TclError:
                pass

        self._canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # ── Unbind when this ReportsFrame is destroyed ────────────────────────
        self.bind("<Destroy>", lambda e: self._canvas.unbind_all("<MouseWheel>"))

    # ── Status bar ────────────────────────────────────────────────────────────
    def _build_statusbar(self):
        bar = tk.Frame(self, bg=BG_CARD, height=30)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Label(bar, text="●", bg=BG_CARD, fg=FG_GREEN,
                 font=("Courier", 10)).pack(side="left", padx=(12, 4))
        self._status_var = tk.StringVar(
            value=f"Report Mode active  ·  {len(self._sessions)} sessions  ·  data/session_log.json")
        tk.Label(bar, textvariable=self._status_var,
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 9)).pack(side="left")
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        tk.Label(bar, text=f"Generated: {now}",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 9)).pack(side="right", padx=12)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 1 — SESSION OVERVIEW
    # ══════════════════════════════════════════════════════════════════════════
    def _panel_overview(self, parent):
        self._section_label(parent, "SESSION OVERVIEW  —  LIVE DATA")
        sessions = self._sessions

        if not sessions:
            tk.Label(parent,
                     text="  No sessions logged yet.\n  Run any module and come back.",
                     bg=BG_DARK, fg=FG_MUTED,
                     font=("Courier", 11)).pack(pady=60)
            return

        total_sessions = len(sessions)
        total_cracked  = sum(s["details"].get("cracked", 0) for s in sessions)
        total_hashes   = sum(s["details"].get("total",   0) for s in sessions)
        crack_rate     = (total_cracked / total_hashes * 100) if total_hashes else 0

        # ── Summary cards ─────────────────────────────────────────────────────
        top = tk.Frame(parent, bg=BG_DARK)
        top.pack(fill="x", pady=(0, 12))
        for label, val, color in [
            ("Total Sessions", str(total_sessions),      FG_BLUE),
            ("Hashes Cracked", str(total_cracked),       FG_GREEN),
            ("Total Tested",   str(total_hashes),        FG_PRIMARY),
            ("Crack Rate",     f"{crack_rate:.1f}%",     FG_YELLOW),
        ]:
            card = tk.Frame(top, bg=BG_CARD,
                            highlightthickness=1, highlightbackground=color)
            card.pack(side="left", expand=True, fill="x", padx=4)
            tk.Label(card, text=val,   bg=BG_CARD, fg=color,
                     font=("Courier", 22, "bold")).pack(pady=(12, 0))
            tk.Label(card, text=label, bg=BG_CARD, fg=FG_MUTED,
                     font=("Courier", 7)).pack(pady=(0, 12))

        # ── Module breakdown ──────────────────────────────────────────────────
        type_counts = {}
        for s in sessions:
            t = s.get("type", "Unknown")
            type_counts[t] = type_counts.get(t, 0) + 1

        self._section_label(parent, "MODULE USAGE BREAKDOWN", pady=(8, 8))
        for stype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            pct   = int(count / total_sessions * 100)
            label = TYPE_LABELS.get(stype, stype)
            row   = tk.Frame(parent, bg=BG_CARD,
                             highlightthickness=1, highlightbackground=BORDER)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"  {label:<22}", bg=BG_CARD, fg=FG_PRIMARY,
                     font=("Courier", 9)).pack(side="left", pady=8)
            tk.Label(row, text=f"{count} session(s)", bg=BG_CARD, fg=FG_MUTED,
                     font=("Courier", 8), width=14).pack(side="left")
            bar_f = tk.Frame(row, bg=BG_DARK, height=8, width=300)
            bar_f.pack(side="left", padx=10)
            bar_f.pack_propagate(False)
            tk.Frame(bar_f, bg=FG_BLUE, height=8,
                     width=max(1, int(3 * pct))).place(x=0, y=0)
            tk.Label(row, text=f"{pct}%", bg=BG_CARD, fg=FG_BLUE,
                     font=("Courier", 8)).pack(side="left")

        # ── Recent sessions table ─────────────────────────────────────────────
        self._section_label(parent, "RECENT SESSIONS  (latest 20)", pady=(16, 8))
        tbl = tk.Frame(parent, bg=BG_CARD,
                       highlightthickness=1, highlightbackground=BORDER_GRN)
        tbl.pack(fill="x")

        hrow = tk.Frame(tbl, bg=BG_GREEN)
        hrow.pack(fill="x")
        for h, w in [("ID", 5), ("Timestamp", 20), ("Type", 14),
                     ("Summary", 42), ("Result", 10)]:
            tk.Label(hrow, text=h, bg=BG_GREEN, fg=FG_GREEN,
                     font=("Courier", 8, "bold"),
                     width=w, anchor="w").pack(side="left", padx=6, pady=5)

        for i, s in enumerate(reversed(sessions[-20:])):
            row_bg  = BG_CARD if i % 2 == 0 else "#252535"
            cracked = s["details"].get("cracked", "—")
            total   = s["details"].get("total",   "—")
            summary = s["details"].get("summary", "—").replace("\u00c2\u00b7", "·")
            row     = tk.Frame(tbl, bg=row_bg)
            row.pack(fill="x")
            for val, w in [(str(s["id"]), 5), (s["timestamp"], 20),
                           (s.get("type", "?"), 14),
                           (summary[:40], 42),
                           (f"{cracked}/{total}", 10)]:
                tk.Label(row, text=val, bg=row_bg, fg=FG_PRIMARY,
                         font=("Courier", 8),
                         width=w, anchor="w").pack(side="left", padx=6, pady=4)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 2 — EVIDENCE LOG
    # ══════════════════════════════════════════════════════════════════════════
    def _panel_evidence(self, parent):
        self._section_label(parent, "EVIDENCE LOG  —  ALL MODULE ACTIVITY")
        sessions = self._sessions

        if not sessions:
            tk.Label(parent, text="  No evidence logged yet.",
                     bg=BG_DARK, fg=FG_MUTED,
                     font=("Courier", 11)).pack(pady=60)
            return

        tb = tk.Frame(parent, bg=BG_DARK)
        tb.pack(fill="x", pady=(0, 10))
        tk.Button(tb, text="[ EXPORT EVIDENCE CSV ]",
                  bg=BG_CARD, fg=FG_TEAL,
                  font=("Courier", 8, "bold"),
                  relief="flat",
                  highlightthickness=1, highlightbackground=FG_TEAL,
                  cursor="hand2", padx=8, pady=4,
                  activebackground=BG_ACCENT,
                  command=self._export_evidence_csv).pack(side="left")

        cols = [("ID", 5), ("Timestamp", 20), ("Module", 14),
                ("Details", 44), ("Result", 9)]
        tbl = tk.Frame(parent, bg=BG_CARD,
                       highlightthickness=1, highlightbackground=BORDER_GRN)
        tbl.pack(fill="x")

        hrow = tk.Frame(tbl, bg=BG_GREEN)
        hrow.pack(fill="x")
        for label, w in cols:
            tk.Label(hrow, text=label, bg=BG_GREEN, fg=FG_GREEN,
                     font=("Courier", 8, "bold"),
                     width=w, anchor="w").pack(side="left", padx=6, pady=5)

        for i, s in enumerate(reversed(sessions)):
            row_bg  = BG_CARD if i % 2 == 0 else "#252535"
            cracked = s["details"].get("cracked", "—")
            total   = s["details"].get("total",   "—")
            elapsed = s["details"].get("elapsed", "")
            summary = s["details"].get("summary", "").replace("\u00c2\u00b7", "·")
            detail  = f"{summary}  {elapsed}".strip()
            result  = f"{cracked}/{total}"
            color   = FG_GREEN if cracked == total and cracked != "—" else FG_PRIMARY

            row = tk.Frame(tbl, bg=row_bg)
            row.pack(fill="x")
            for val, w in [(str(s["id"]), 5), (s["timestamp"], 20),
                           (s.get("type", "?"), 14),
                           (detail[:43], 44), (result, 9)]:
                tk.Label(row, text=val, bg=row_bg, fg=color,
                         font=("Courier", 8),
                         width=w, anchor="w").pack(side="left", padx=6, pady=4)

        # Chain of custody
        self._section_label(parent, "CHAIN OF CUSTODY  (last 6)", pady=(16, 8))
        for s in sessions[-6:]:
            summary = s["details"].get("summary", "").replace("\u00c2\u00b7", "·")
            tk.Label(parent,
                     text=f"  {s['timestamp']}  ·  {s.get('type','?'):<14}  ·  {summary}",
                     bg=BG_DARK, fg=FG_MUTED,
                     font=("Courier", 8), anchor="w").pack(fill="x")

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 3 — RISK SCORING
    # ══════════════════════════════════════════════════════════════════════════
    def _panel_risk(self, parent):
        self._section_label(parent, "RISK SCORING  —  CALCULATED FROM REAL DATA")
        sessions = self._sessions

        if not sessions:
            tk.Label(parent, text="  No data to score yet.",
                     bg=BG_DARK, fg=FG_MUTED,
                     font=("Courier", 11)).pack(pady=60)
            return

        total_hashes  = sum(s["details"].get("total",   0) for s in sessions)
        total_cracked = sum(s["details"].get("cracked", 0) for s in sessions)
        crack_rate    = (total_cracked / total_hashes * 100) if total_hashes else 0
        risk_score    = round(crack_rate / 10, 1)

        if   crack_rate >= 80: severity, color = "CRITICAL", FG_RED
        elif crack_rate >= 50: severity, color = "HIGH",     FG_YELLOW
        elif crack_rate >= 25: severity, color = "MEDIUM",   FG_BLUE
        else:                  severity, color = "LOW",       FG_GREEN

        # Summary cards
        top = tk.Frame(parent, bg=BG_DARK)
        top.pack(fill="x", pady=(0, 12))
        for label, val, c in [
            ("Risk Score",     f"{risk_score}/10",    color),
            ("Crack Rate",     f"{crack_rate:.1f}%",  color),
            ("Hashes Cracked", str(total_cracked),    FG_RED),
            ("Total Tested",   str(total_hashes),     FG_PRIMARY),
        ]:
            card = tk.Frame(top, bg=BG_CARD,
                            highlightthickness=1, highlightbackground=c)
            card.pack(side="left", expand=True, fill="x", padx=4)
            tk.Label(card, text=val,   bg=BG_CARD, fg=c,
                     font=("Courier", 20, "bold")).pack(pady=(12, 0))
            tk.Label(card, text=label, bg=BG_CARD, fg=FG_MUTED,
                     font=("Courier", 7)).pack(pady=(0, 12))

        # Banner
        banner = tk.Frame(parent, bg=BG_CARD,
                          highlightthickness=2, highlightbackground=color)
        banner.pack(fill="x", pady=(0, 12))
        tk.Label(banner,
                 text=f"  OVERALL RISK: {severity}  ·  "
                      f"{total_cracked}/{total_hashes} hashes crackable  ·  "
                      f"Score: {risk_score}/10",
                 bg=BG_CARD, fg=color,
                 font=("Courier", 10, "bold")).pack(anchor="w", pady=10)

        # Per-session breakdown
        self._section_label(parent, "PER-SESSION BREAKDOWN", pady=(8, 8))
        tbl = tk.Frame(parent, bg=BG_CARD,
                       highlightthickness=1, highlightbackground=BORDER_GRN)
        tbl.pack(fill="x")

        hrow = tk.Frame(tbl, bg=BG_GREEN)
        hrow.pack(fill="x")
        for h, w in [("ID", 5), ("Type", 14), ("Cracked", 9),
                     ("Total", 7), ("Rate", 8), ("Risk", 10), ("Elapsed", 10)]:
            tk.Label(hrow, text=h, bg=BG_GREEN, fg=FG_GREEN,
                     font=("Courier", 8, "bold"),
                     width=w, anchor="w").pack(side="left", padx=6, pady=5)

        for i, s in enumerate(reversed(sessions)):
            c = s["details"].get("cracked", 0)
            t = s["details"].get("total",   0)
            e = s["details"].get("elapsed", "—")
            r = (c / t * 100) if t else 0

            if   r >= 80: rl, rc = "CRITICAL", FG_RED
            elif r >= 50: rl, rc = "HIGH",     FG_YELLOW
            elif r >= 25: rl, rc = "MEDIUM",   FG_BLUE
            else:         rl, rc = "LOW",       FG_GREEN

            row_bg = BG_CARD if i % 2 == 0 else "#252535"
            row    = tk.Frame(tbl, bg=row_bg)
            row.pack(fill="x")
            for val, w, fg in [
                (str(s["id"]),        5,  FG_MUTED),
                (s.get("type","?"),  14,  FG_PRIMARY),
                (str(c),              9,  FG_RED),
                (str(t),             7,  FG_PRIMARY),
                (f"{r:.0f}%",         8,  rc),
                (rl,                 10,  rc),
                (str(e),             10,  FG_MUTED),
            ]:
                tk.Label(row, text=val, bg=row_bg, fg=fg,
                         font=("Courier", 8),
                         width=w, anchor="w").pack(side="left", padx=6, pady=4)

        # Recommendations
        self._section_label(parent, "RECOMMENDATIONS", pady=(16, 8))
        if   crack_rate >= 80:
            recs = [("Critical", "Immediately migrate to bcrypt / Argon2id"),
                    ("Critical", "Enforce account lockout after 5 attempts"),
                    ("High",     "Force password reset for all users")]
        elif crack_rate >= 50:
            recs = [("High",   "Strengthen password complexity requirements"),
                    ("High",   "Integrate breach-list (HaveIBeenPwned API)"),
                    ("Medium", "Enforce 12+ character minimum")]
        elif crack_rate >= 25:
            recs = [("Medium", "Increase minimum password length to 14+"),
                    ("Medium", "Enable MFA across all accounts"),
                    ("Low",    "Schedule regular password audits")]
        else:
            recs = [("Low", "Password posture looks strong — maintain policies"),
                    ("Low", "Continue regular audits")]

        for sev, rec in recs:
            c   = SEVERITY_COLORS.get(sev, FG_PRIMARY)
            row = tk.Frame(parent, bg=BG_CARD,
                           highlightthickness=1, highlightbackground=BORDER)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"  {sev:<8}", bg=BG_CARD, fg=c,
                     font=("Courier", 8, "bold"), width=10).pack(side="left", pady=6)
            tk.Label(row, text=rec, bg=BG_CARD, fg=FG_PRIMARY,
                     font=("Courier", 8)).pack(side="left", padx=8)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 4 — COMPLIANCE
    # ══════════════════════════════════════════════════════════════════════════
    def _panel_compliance(self, parent):
        self._section_label(parent, "COMPLIANCE  —  DERIVED FROM REAL CRACK RATE")
        sessions   = self._sessions
        total_h    = sum(s["details"].get("total",   0) for s in sessions)
        cracked_h  = sum(s["details"].get("cracked", 0) for s in sessions)
        crack_rate = (cracked_h / total_h * 100) if total_h else 0

        for fw, desc, threshold in [
            ("NIST 800-63B",  "Min length · breach-list · no complexity rules", 20),
            ("OWASP Top 10",  "A07: Identification & Authentication Failures",   30),
            ("ISO 27001 A.9", "Access control · credential management",          40),
            ("PCI-DSS 8.3",   "Strong passwords for cardholder data systems",    10),
        ]:
            passing = crack_rate < threshold
            color   = FG_GREEN if passing else FG_RED
            card    = self._card(parent)
            row     = tk.Frame(card, bg=BG_CARD)
            row.pack(fill="x", padx=14, pady=10)

            left = tk.Frame(row, bg=BG_CARD)
            left.pack(side="left", fill="both", expand=True)
            tk.Label(left, text=fw, bg=BG_CARD, fg=FG_PRIMARY,
                     font=("Courier", 10, "bold")).pack(anchor="w")
            tk.Label(left, text=desc, bg=BG_CARD, fg=FG_MUTED,
                     font=("Courier", 8)).pack(anchor="w")
            tk.Label(left,
                     text=f"Threshold: crack rate < {threshold}%  ·  "
                          f"Your rate: {crack_rate:.1f}%  ·  "
                          f"Based on {total_h} hashes",
                     bg=BG_CARD, fg=FG_MUTED,
                     font=("Courier", 7)).pack(anchor="w")

            tk.Label(row, text="PASS ✔" if passing else "FAIL ✘",
                     bg=BG_CARD, fg=color,
                     font=("Courier", 14, "bold")).pack(side="right")

        # Violations
        self._section_label(parent, "DETECTED VIOLATIONS", pady=(16, 8))
        violations = []
        if crack_rate >= 80:
            violations.append(("Critical", "Overall",      f"{crack_rate:.0f}% crack rate — critical risk"))
        if crack_rate >= 50:
            violations.append(("High",     "NIST 800-63B", "Crack rate exceeds 50% threshold"))
        if crack_rate >= 30:
            violations.append(("High",     "PCI-DSS 8.3",  "Weak passwords detected"))
        if crack_rate >= 10:
            violations.append(("Medium",   "ISO 27001",    "Password strength below standard"))
        if total_h < 10:
            violations.append(("Low",      "Audit",        "Small sample — increase testing scope"))
        if not violations:
            violations.append(("Low", "None", "No critical violations detected"))

        for sev, ref, desc in violations:
            color = SEVERITY_COLORS.get(sev, FG_PRIMARY)
            row   = tk.Frame(parent, bg=BG_CARD,
                             highlightthickness=1, highlightbackground=BORDER)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"  {sev:<8}", bg=BG_CARD, fg=color,
                     font=("Courier", 8, "bold"), width=10).pack(side="left", pady=6)
            tk.Label(row, text=ref,  bg=BG_CARD, fg=FG_TEAL,
                     font=("Courier", 8), width=16).pack(side="left")
            tk.Label(row, text=desc, bg=BG_CARD, fg=FG_PRIMARY,
                     font=("Courier", 8)).pack(side="left", padx=8)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 5 — REPORT GENERATOR
    # ══════════════════════════════════════════════════════════════════════════
    def _panel_report_gen(self, parent):
        self._section_label(parent, "REPORT GENERATOR  —  EXPORTS REAL SESSION DATA")

        form = self._card(parent)
        self._entries = {}
        for label, default in [
            ("Engagement Title", "Password Security Assessment"),
            ("Client Name",      ""),
            ("Assessor",         "Analyst-1"),
            ("Classification",   "CONFIDENTIAL"),
            ("Scope",            "All CryptX modules"),
        ]:
            row = tk.Frame(form, bg=BG_CARD)
            row.pack(fill="x", padx=14, pady=4)
            tk.Label(row, text=f"{label}:", bg=BG_CARD, fg=FG_MUTED,
                     font=("Courier", 8), width=18, anchor="w").pack(side="left")
            var = tk.StringVar(value=default)
            tk.Entry(row, textvariable=var,
                     bg="#1a1a2e", fg=FG_PRIMARY,
                     insertbackground=FG_GREEN,
                     relief="flat",
                     highlightthickness=1, highlightbackground=BORDER,
                     font=("Courier", 9)
                     ).pack(side="left", fill="x", expand=True, ipady=4)
            self._entries[label] = var

        # Live data summary
        sessions   = self._sessions
        total_h    = sum(s["details"].get("total",   0) for s in sessions)
        cracked_h  = sum(s["details"].get("cracked", 0) for s in sessions)
        crack_rate = (cracked_h / total_h * 100) if total_h else 0
        types      = list({s.get("type","?") for s in sessions})

        self._section_label(parent, "REPORT WILL CONTAIN", pady=(12, 8))
        preview = tk.Text(parent, bg="#12121e", fg=FG_GREEN,
                          font=("Courier", 9),
                          relief="flat",
                          highlightthickness=1, highlightbackground=BORDER_GRN,
                          height=8)
        preview.pack(fill="x")
        for line in [
            f"  Total sessions logged : {len(sessions)}",
            f"  Modules used          : {', '.join(types) or 'None'}",
            f"  Total hashes tested   : {total_h}",
            f"  Total cracked         : {cracked_h}",
            f"  Overall crack rate    : {crack_rate:.1f}%",
            f"  Date range            : "
            f"{sessions[0]['timestamp'] if sessions else 'N/A'}"
            f"  →  {sessions[-1]['timestamp'] if sessions else 'N/A'}",
            f"  Risk level            : "
            f"{'CRITICAL' if crack_rate>=80 else 'HIGH' if crack_rate>=50 else 'MEDIUM' if crack_rate>=25 else 'LOW'}",
        ]:
            preview.insert("end", line + "\n")
        preview.configure(state="disabled")

        fmt_row = tk.Frame(parent, bg=BG_DARK)
        fmt_row.pack(fill="x", pady=(12, 0))
        for fmt, color in [("HTML", FG_BLUE), ("TXT", FG_GREEN)]:
            tk.Button(fmt_row, text=f"▶  Generate {fmt} Report",
                      bg=BG_CARD, fg=color,
                      font=("Courier", 10, "bold"),
                      relief="flat",
                      highlightthickness=1, highlightbackground=color,
                      cursor="hand2", padx=14, pady=8,
                      activebackground=BG_ACCENT,
                      command=lambda f=fmt: self._generate_report(f)
                      ).pack(side="left", expand=True, fill="x", padx=4)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 6 — AUDIT TRAIL
    # ══════════════════════════════════════════════════════════════════════════
    def _panel_audit(self, parent):
        self._section_label(parent, "AUDIT TRAIL  —  COMPLETE SESSION LOG")

        ctrl = tk.Frame(parent, bg=BG_DARK)
        ctrl.pack(fill="x", pady=(0, 10))
        for label, color, cmd in [
            ("[ EXPORT LOG ]",        FG_GREEN, self._export_log),
            ("[ CLEAR ALL SESSIONS ]", FG_RED,  self._clear_log),
        ]:
            tk.Button(ctrl, text=label,
                      bg=BG_CARD, fg=color,
                      font=("Courier", 8, "bold"),
                      relief="flat",
                      highlightthickness=1, highlightbackground=color,
                      cursor="hand2", padx=8, pady=3,
                      activebackground=BG_GREEN if color == FG_GREEN else "#2d0000",
                      command=cmd).pack(side="left", padx=(0, 6))

        log_frame = tk.Frame(parent, bg=BG_CARD,
                             highlightthickness=1, highlightbackground=BORDER_GRN)
        log_frame.pack(fill="both", expand=True)

        log_text = tk.Text(log_frame, bg="#0f0f1a", fg=FG_GREEN,
                           font=("Courier", 8),
                           relief="flat", highlightthickness=0,
                           height=22, wrap="none")
        log_text.pack(fill="both", expand=True, padx=2, pady=2)

        log_text.tag_configure("id",      foreground=FG_BLUE)
        log_text.tag_configure("ts",      foreground=FG_MUTED)
        log_text.tag_configure("type",    foreground=FG_TEAL)
        log_text.tag_configure("detail",  foreground=FG_PRIMARY)
        log_text.tag_configure("result",  foreground=FG_GREEN)

        if not self._sessions:
            log_text.insert("end", "  No sessions logged yet.\n", "ts")
        else:
            for s in self._sessions:
                summary = s["details"].get("summary", "").replace("\u00c2\u00b7", "·")
                cracked = s["details"].get("cracked", "?")
                total   = s["details"].get("total",   "?")
                log_text.insert("end", f"[{s['id']:>4}]  ", "id")
                log_text.insert("end", f"{s['timestamp']}  ", "ts")
                log_text.insert("end", f"{s.get('type','?'):<14}", "type")
                log_text.insert("end", f"{summary[:38]:<40}", "detail")
                log_text.insert("end", f"cracked:{cracked}/{total}\n", "result")

        log_text.configure(state="disabled")

        integ = tk.Frame(parent, bg=BG_GREEN,
                         highlightthickness=1, highlightbackground=BORDER_GRN)
        integ.pack(fill="x", pady=(8, 0))
        last_ts = self._sessions[-1]["timestamp"] if self._sessions else "N/A"
        tk.Label(integ,
                 text=f"  ✔  {len(self._sessions)} sessions in log  ·  "
                      f"Source: data/session_log.json  ·  Last entry: {last_ts}",
                 bg=BG_GREEN, fg=FG_GREEN,
                 font=("Courier", 8)).pack(anchor="w", pady=6)

    # ══════════════════════════════════════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════════════════════════════════════
    def _section_label(self, parent, text, pady=(0, 8)):
        tk.Label(parent, text=text,
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w", pady=pady)

    def _card(self, parent):
        card = tk.Frame(parent, bg=BG_CARD,
                        relief="flat",
                        highlightthickness=1,
                        highlightbackground=BORDER_GRN)
        card.pack(fill="x", pady=(0, 8))
        return card

    # ══════════════════════════════════════════════════════════════════════════
    #  ACTIONS
    # ══════════════════════════════════════════════════════════════════════════
    def _refresh(self):
        self._sessions = load_sessions()
        for w in self.winfo_children():
            w.destroy()
        self._build_header()
        self._build_tab_bar()
        self._build_content_area()
        self._build_statusbar()
        self._switch_tab(self._active_tab.get())

    def _clear_log(self):
        if messagebox.askyesno("Clear Log",
                               "Delete ALL session data permanently?\n"
                               "This cannot be undone."):
            clear_sessions()
            self._sessions = []
            self._refresh()

    def _export_all(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile="CryptX_SessionLog.json"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._sessions, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Exported", f"Session log saved to:\n{path}")

    def _export_evidence_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="CryptX_Evidence.csv"
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Timestamp", "Type",
                             "Cracked", "Total", "Elapsed", "Summary"])
            for s in self._sessions:
                d = s["details"]
                writer.writerow([
                    s["id"], s["timestamp"], s.get("type", ""),
                    d.get("cracked", ""), d.get("total", ""),
                    d.get("elapsed", ""),
                    d.get("summary", "").replace("\u00c2\u00b7", "·")
                ])
        messagebox.showinfo("Exported", f"Evidence CSV saved to:\n{path}")

    def _export_log(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text log", "*.txt")],
            initialfile="CryptX_AuditLog.txt"
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("CRYPTX AUDIT TRAIL\n" + "=" * 60 + "\n\n")
            for s in self._sessions:
                summary = s["details"].get("summary", "").replace("\u00c2\u00b7", "·")
                f.write(f"[{s['id']:>4}]  {s['timestamp']}  "
                        f"{s.get('type','?'):<14}  {summary}\n")
        messagebox.showinfo("Exported", f"Audit log saved to:\n{path}")

    def _generate_report(self, fmt):
        sessions   = self._sessions
        total_h    = sum(s["details"].get("total",   0) for s in sessions)
        cracked_h  = sum(s["details"].get("cracked", 0) for s in sessions)
        crack_rate = (cracked_h / total_h * 100) if total_h else 0
        client     = self._entries.get("Client Name",      type("o",(),{"get":lambda s:""})()).get()
        assessor   = self._entries.get("Assessor",         type("o",(),{"get":lambda s:"Analyst-1"})()).get()
        title      = self._entries.get("Engagement Title", type("o",(),{"get":lambda s:"Assessment"})()).get()
        now        = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        if   crack_rate >= 80: risk, rc = "CRITICAL", "#f87171"
        elif crack_rate >= 50: risk, rc = "HIGH",     "#fbbf24"
        elif crack_rate >= 25: risk, rc = "MEDIUM",   "#7dd3fc"
        else:                  risk, rc = "LOW",       "#22c55e"

        ext  = ".html" if fmt == "HTML" else ".txt"
        path = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=[(f"{fmt} file", f"*{ext}")],
            initialfile=f"CryptX_Report{ext}"
        )
        if not path:
            return

        if fmt == "HTML":
            rows = ""
            for s in sessions:
                d  = s["details"]
                c  = d.get("cracked", 0)
                t  = d.get("total",   0)
                r  = (c / t * 100) if t else 0
                cl = "critical" if r>=80 else "high" if r>=50 else "medium" if r>=25 else "low"
                sm = d.get("summary","").replace("\u00c2\u00b7","·")
                rows += (f"<tr><td>{s['id']}</td><td>{s['timestamp']}</td>"
                         f"<td>{s.get('type','?')}</td><td>{sm}</td>"
                         f"<td class='{cl}'>{c}/{t} ({r:.0f}%)</td></tr>\n")

            content = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>CryptX Report</title>
<style>
body{{font-family:'Courier New',monospace;background:#1e1e2e;color:#cbd5e1;padding:40px}}
h1{{color:#22c55e}}h2{{color:#7dd3fc;border-bottom:1px solid #3a3a50;padding-bottom:6px}}
.critical{{color:#f87171}}.high{{color:#fbbf24}}.medium{{color:#7dd3fc}}.low{{color:#22c55e}}
table{{width:100%;border-collapse:collapse;margin:16px 0}}
th{{background:#1a3a2a;color:#22c55e;padding:8px;text-align:left}}
td{{padding:6px 8px;border-bottom:1px solid #3a3a50}}
.banner{{background:#2a2a3e;border:2px solid {rc};padding:16px;margin:16px 0;color:{rc};font-weight:bold}}
</style></head><body>
<h1>CRYPTX SECURITY ASSESSMENT REPORT</h1>
<p><strong>Title:</strong> {title} &nbsp;|&nbsp;
   <strong>Client:</strong> {client} &nbsp;|&nbsp;
   <strong>Assessor:</strong> {assessor} &nbsp;|&nbsp;
   <strong>Generated:</strong> {now}</p>
<div class="banner">OVERALL RISK: {risk} &nbsp;·&nbsp;
{cracked_h}/{total_h} hashes crackable &nbsp;·&nbsp; Crack Rate: {crack_rate:.1f}%</div>
<h2>Session Data ({len(sessions)} sessions)</h2>
<table><tr><th>#</th><th>Timestamp</th><th>Module</th><th>Summary</th><th>Result</th></tr>
{rows}</table>
<h2>Risk Summary</h2>
<ul>
<li>Total sessions: {len(sessions)}</li>
<li>Total hashes tested: {total_h}</li>
<li>Total cracked: {cracked_h}</li>
<li>Crack rate: {crack_rate:.1f}%</li>
<li>Risk level: <span class="{risk.lower()}">{risk}</span></li>
</ul>
</body></html>"""
        else:
            lines = [
                "CRYPTX SECURITY ASSESSMENT REPORT",
                "=" * 60,
                f"Title    : {title}",
                f"Client   : {client}",
                f"Assessor : {assessor}",
                f"Generated: {now}",
                "",
                f"OVERALL RISK : {risk}",
                f"Crack Rate   : {crack_rate:.1f}%",
                f"Cracked      : {cracked_h}/{total_h}",
                "",
                "SESSIONS",
                "-" * 60,
            ]
            for s in sessions:
                sm = s["details"].get("summary","").replace("\u00c2\u00b7","·")
                lines.append(f"[{s['id']:>3}] {s['timestamp']}  "
                             f"{s.get('type','?'):<14}  {sm}")
            content = "\n".join(lines)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        messagebox.showinfo("Report Generated", f"Saved to:\n{path}")


# ══════════════════════════════════════════════════════════════════════════════
#  STANDALONE TEST  —  python ui/reports_mode.py
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    class _FakeNav:
        def push_view(self, cls): print(f"[nav] push_view({cls.__name__})")
        def pop_view(self):       print("[nav] pop_view()")

    root = tk.Tk()
    root.title("CryptX — Report Mode (standalone test)")
    root.geometry("1100x750")
    root.configure(bg="#1e1e2e")
    ReportsFrame(root, _FakeNav()).pack(fill="both", expand=True)
    root.mainloop()