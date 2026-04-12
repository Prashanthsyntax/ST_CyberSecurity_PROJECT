import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import csv
import os
from datetime import datetime

from core.session_logger import (
    load_sessions,
    clear_sessions,
    log_session,
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

SESSION_TYPE_COLORS = {
    "Hash Crack":   FG_BLUE,
    "Hybrid":       FG_PURPLE,
    "Wordlist":     FG_GREEN,
    "Rule Engine":  FG_AMBER,
    "Rainbow":      FG_RED,
    "AI Training":  FG_PURPLE,
}


class ReportsFrame(tk.Frame):
    def __init__(self, parent, nav=None):
        super().__init__(parent, bg=BG_DARK)
        self.nav = nav

        self.sessions      = []
        self.preview_box   = None          # ← initialised early so guards work
        self.report_format = tk.StringVar(value="TXT")
        self.analyst_var   = tk.StringVar(value="")
        self.target_var    = tk.StringVar(value="")
        self.scope_var     = tk.StringVar(value="Authorized assessment")
        self.fmt_btns      = {}

        self._build_titlebar()
        self._build_summary_cards()
        self._build_main_area()
        self._build_preview()
        self._build_buttons()
        self._build_statusbar()

        self._load_sessions()

    # ── Title bar ────────────────────────────────────
    def _build_titlebar(self):
        bar = tk.Frame(self, bg=BG_CARD, height=36)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        for color in ["#ff5f57", "#febc2e", "#28c840"]:
            tk.Label(bar, bg=color, width=2).pack(
                side="left",
                padx=(8 if color == "#ff5f57" else 4, 0),
                pady=7)
        tk.Label(bar,
                 text="Window 8 — Reports & Logs  ·  Compliance-ready audit trail",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 10)).pack(side="left", padx=12)

    # ── Summary cards ─────────────────────────────────
    def _build_summary_cards(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(12, 0))

        self.summary_vars = {
            "Sessions":      tk.StringVar(value="0"),
            "Total cracked": tk.StringVar(value="0"),
            "Hash Crack":    tk.StringVar(value="0"),
            "Hybrid":        tk.StringVar(value="0"),
            "Wordlist":      tk.StringVar(value="0"),
            "Reports made":  tk.StringVar(value="0"),
        }
        colors = {
            "Sessions":      FG_BLUE,
            "Total cracked": FG_GREEN,
            "Hash Crack":    FG_BLUE,
            "Hybrid":        FG_PURPLE,
            "Wordlist":      FG_AMBER,
            "Reports made":  FG_PRIMARY,
        }
        for label, var in self.summary_vars.items():
            card = tk.Frame(frame, bg=BG_CARD,
                            highlightthickness=1,
                            highlightbackground=BORDER)
            card.pack(side="left", expand=True, fill="x", padx=3)
            tk.Label(card, textvariable=var, bg=BG_CARD,
                     fg=colors[label],
                     font=("Courier", 14, "bold")).pack(pady=(8, 2))
            tk.Label(card, text=label, bg=BG_CARD,
                     fg=FG_MUTED,
                     font=("Courier", 7)).pack(pady=(0, 8))

    # ── Main 2-column area ────────────────────────────
    def _build_main_area(self):
        outer = tk.Frame(self, bg=BG_DARK)
        outer.pack(fill="both", expand=True, padx=16, pady=(12, 0))
        outer.columnconfigure(0, weight=3)
        outer.columnconfigure(1, weight=2)

        self._build_session_log(outer)
        self._build_report_builder(outer)

    # ── Session log table ─────────────────────────────
    def _build_session_log(self, parent):
        frame = tk.Frame(parent, bg=BG_DARK)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tk.Label(frame,
                 text="SESSION LOG — all activity auto-logged",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w", pady=(0, 5))

        card = tk.Frame(frame, bg=BG_CARD,
                        highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Log.Treeview",
                        background=BG_CARD,
                        foreground=FG_PRIMARY,
                        fieldbackground=BG_CARD,
                        rowheight=26,
                        font=("Courier", 9))
        style.configure("Log.Treeview.Heading",
                        background=BG_DARK,
                        foreground=FG_MUTED,
                        font=("Courier", 8))
        style.map("Log.Treeview",
                  background=[("selected", BG_ACCENT)])

        cols = ("id", "timestamp", "type", "summary", "elapsed")
        self.log_tree = ttk.Treeview(card, columns=cols,
                                     show="headings",
                                     style="Log.Treeview",
                                     height=8) # Reduced from 10 to fit vertical budget

        for col, txt, w in [
            ("id",        "#",         35),
            ("timestamp", "Timestamp", 140),
            ("type",      "Type",       90),
            ("summary",   "Summary",   260),
            ("elapsed",   "Time",       60),
        ]:
            self.log_tree.heading(col, text=txt)
            self.log_tree.column(col, width=w, anchor="w")

        self.log_tree.tag_configure("hashcrack", foreground=FG_BLUE)
        self.log_tree.tag_configure("hybrid",    foreground=FG_PURPLE)
        self.log_tree.tag_configure("wordlist",  foreground=FG_GREEN)
        self.log_tree.tag_configure("rule",      foreground=FG_AMBER)
        self.log_tree.tag_configure("rainbow",   foreground=FG_RED)
        self.log_tree.tag_configure("other",     foreground=FG_MUTED)

        sb = ttk.Scrollbar(card, orient="vertical",
                           command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=sb.set)
        self.log_tree.pack(side="left", fill="both",
                           expand=True, padx=4, pady=4)
        sb.pack(side="right", fill="y", pady=4)

        self.log_tree.bind("<<TreeviewSelect>>", self._on_session_select)

        btn_row = tk.Frame(card, bg=BG_CARD)
        btn_row.pack(fill="x", padx=8, pady=(0, 6))

        tk.Button(btn_row, text="Add test session",
                  bg=BG_CARD, fg=FG_BLUE, relief="flat",
                  font=("Courier", 8), cursor="hand2",
                  command=self._add_test_session).pack(side="left")

        tk.Button(btn_row, text="Delete selected",
                  bg=BG_CARD, fg=FG_RED, relief="flat",
                  font=("Courier", 8), cursor="hand2",
                  command=self._delete_selected).pack(side="left", padx=8)

        tk.Button(btn_row, text="Refresh",
                  bg=BG_CARD, fg=FG_MUTED, relief="flat",
                  font=("Courier", 8), cursor="hand2",
                  command=self._load_sessions).pack(side="right")

    # ── Report builder ────────────────────────────────
    def _build_report_builder(self, parent):
        frame = tk.Frame(parent, bg=BG_DARK)
        frame.grid(row=0, column=1, sticky="nsew")

        tk.Label(frame, text="REPORT BUILDER",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w", pady=(0, 5))

        card = tk.Frame(frame, bg=BG_CARD,
                        highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill="both", expand=True)

        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(fill="x", padx=12, pady=10)

        fields = [
            ("Analyst name",  self.analyst_var, "Your name / team name"),
            ("Engagement",    self.target_var,  "Target / project name"),
            ("Scope / notes", self.scope_var,   "Authorized assessment"),
        ]
        for label, var, ph in fields:
            tk.Label(inner, text=label, bg=BG_CARD, fg=FG_MUTED,
                     font=("Courier", 8)).pack(anchor="w", pady=(0, 2))
            entry = tk.Entry(inner, textvariable=var,
                             bg=BG_EDITOR, fg=FG_PRIMARY,
                             insertbackground=FG_BLUE,
                             relief="flat",
                             highlightthickness=1,
                             highlightbackground=BORDER,
                             font=("Courier", 9))
            entry.pack(fill="x", ipady=5, pady=(0, 8))

            if not var.get():
                entry.insert(0, ph)
                entry.configure(fg=FG_MUTED)

                def _in(e, ent=entry, p=ph, v=var):
                    if ent.get() == p:
                        ent.delete(0, "end")
                        ent.configure(fg=FG_PRIMARY)

                def _out(e, ent=entry, p=ph):
                    if not ent.get().strip():
                        ent.insert(0, p)
                        ent.configure(fg=FG_MUTED)

                entry.bind("<FocusIn>",  _in)
                entry.bind("<FocusOut>", _out)

        tk.Label(inner, text="REPORT FORMAT",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w", pady=(0, 4))

        fmt_row = tk.Frame(inner, bg=BG_CARD)
        fmt_row.pack(fill="x", pady=(0, 8))

        for fmt in ["TXT", "CSV", "JSON", "HTML"]:
            btn = tk.Button(fmt_row, text=fmt,
                            bg=BG_DARK, fg=FG_MUTED,
                            relief="flat",
                            font=("Courier", 9),
                            highlightthickness=1,
                            highlightbackground=BORDER,
                            cursor="hand2",
                            padx=10, pady=4,
                            command=lambda f=fmt: self._select_format(f))
            btn.pack(side="left", padx=(0, 6))
            self.fmt_btns[fmt] = btn

        self._select_format("TXT")

        tk.Label(inner, text="INCLUDE IN REPORT",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w", pady=(0, 4))

        self.include_opts = {
            "Session log":      tk.BooleanVar(value=True),
            "Cracked passwords":tk.BooleanVar(value=True),
            "Strength analysis":tk.BooleanVar(value=True),
            "Timeline":         tk.BooleanVar(value=True),
            "Recommendations":  tk.BooleanVar(value=True),
        }
        for opt, var in self.include_opts.items():
            tk.Checkbutton(inner, text=opt, variable=var,
                           bg=BG_CARD, fg=FG_PRIMARY,
                           selectcolor=BG_ACCENT,
                           activebackground=BG_CARD,
                           activeforeground=FG_BLUE,
                           font=("Courier", 8)).pack(anchor="w")

    def _select_format(self, fmt):
        self.report_format.set(fmt)
        for f, btn in self.fmt_btns.items():
            if f == fmt:
                btn.configure(bg=BG_ACCENT, fg=FG_GREEN,
                              highlightbackground=FG_GREEN)
            else:
                btn.configure(bg=BG_DARK, fg=FG_MUTED,
                              highlightbackground=BORDER)
        if self.preview_box is not None:
            self._update_preview()

    # ── Report preview ────────────────────────────────
    def _build_preview(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(10, 0))

        tk.Label(frame, text="REPORT PREVIEW",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("Courier", 8)).pack(anchor="w", pady=(0, 4))

        pf = tk.Frame(frame, bg=BG_CARD,
                      highlightthickness=1,
                      highlightbackground=BORDER)
        pf.pack(fill="x")

        self.preview_box = tk.Text(pf,
                                   bg=BG_EDITOR, fg=FG_GREEN,
                                   font=("Courier", 9),
                                   relief="flat",
                                   state="disabled",
                                   height=5,
                                   padx=10, pady=8)
        self.preview_box.pack(fill="x", expand=False)

        self._update_preview()

        for var in [self.analyst_var, self.target_var, self.scope_var]:
            var.trace_add("write", lambda *a: self._update_preview())

    def _update_preview(self):
        if self.preview_box is None:
            return

        analyst = self.analyst_var.get().strip()
        target  = self.target_var.get().strip()
        scope   = self.scope_var.get().strip()
        fmt     = self.report_format.get()
        now     = datetime.now().strftime("%Y-%m-%d %H:%M")
        total   = len(self.sessions)
        cracked = sum(s["details"].get("cracked", 0) for s in self.sessions)

        if fmt == "TXT":
            preview = (
                f"{'='*56}\n"
                f"  PENETRATION TEST REPORT\n"
                f"{'='*56}\n"
                f"  Analyst:    {analyst or 'Not set'}\n"
                f"  Engagement: {target or 'Not set'}\n"
                f"  Scope:      {scope or 'Not set'}\n"
                f"  Date:       {now}\n"
                f"{'='*56}\n"
                f"  Sessions:   {total}\n"
                f"  Cracked:    {cracked}\n"
                f"  ...")
        elif fmt == "JSON":
            preview = (
                '{\n'
                f'  "analyst": "{analyst}",\n'
                f'  "engagement": "{target}",\n'
                f'  "date": "{now}",\n'
                f'  "total_sessions": {total},\n'
                f'  "total_cracked": {cracked},\n'
                '  "sessions": [...]\n'
                '}')
        elif fmt == "CSV":
            preview = (
                "id,timestamp,type,cracked,elapsed\n"
                + "\n".join(
                    f"{s['id']},"
                    f"{s['timestamp']},"
                    f"{s['type']},"
                    f"{s['details'].get('cracked', 0)},"
                    f"{s['details'].get('elapsed', '—')}"
                    for s in self.sessions[:3]))
        elif fmt == "HTML":
            preview = (
                "<!DOCTYPE html>\n"
                "<html><head>\n"
                f"  <title>Pentest Report — {target}</title>\n"
                "</head><body>\n"
                f"  <h1>{target or 'Report'}</h1>\n"
                f"  <p>Analyst: {analyst}</p>\n"
                f"  <p>Date: {now}</p>\n"
                f"  <p>Sessions: {total}</p>\n"
                "  ...")
        else:
            preview = ""

        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        self.preview_box.insert("end", preview)
        self.preview_box.configure(state="disabled")

    # ── Buttons ───────────────────────────────────────
    def _build_buttons(self):
        frame = tk.Frame(self, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(10, 6))

        self.gen_btn = tk.Button(
            frame, text="▶  Generate Report",
            bg=BTN_BLUE, fg="#e0f0ff",
            font=("Courier", 12, "bold"),
            relief="flat",
            highlightthickness=1,
            highlightbackground=BTN_BLUE,
            activebackground="#1a6fbf",
            activeforeground="#ffffff",
            cursor="hand2",
            command=self._generate_report)
        self.gen_btn.pack(side="left", expand=True,
                          fill="x", padx=(0, 6), ipady=10)

        tk.Button(frame, text="Export HTML",
                  bg=BG_DARK, fg=FG_PRIMARY,
                  font=("Courier", 11), relief="flat",
                  highlightthickness=1, highlightbackground=BORDER,
                  activebackground=BG_CARD, cursor="hand2",
                  command=self._export_html).pack(
                      side="left", expand=True, fill="x",
                      padx=3, ipady=10)

        tk.Button(frame, text="Import CSV Results",
                  bg=BG_DARK, fg=FG_PRIMARY,
                  font=("Courier", 11), relief="flat",
                  highlightthickness=1, highlightbackground=BORDER,
                  activebackground=BG_CARD, cursor="hand2",
                  command=self._import_csv).pack(
                      side="left", expand=True, fill="x",
                      padx=3, ipady=10)

        tk.Button(frame, text="Clear All Logs",
                  bg=BG_DARK, fg=FG_RED,
                  font=("Courier", 11), relief="flat",
                  highlightthickness=1, highlightbackground=BORDER,
                  activebackground=BG_CARD, cursor="hand2",
                  command=self._clear_logs).pack(
                      side="left", expand=True, fill="x",
                      padx=(3, 0), ipady=10)

    # ── Status bar ────────────────────────────────────
    def _build_statusbar(self):
        bar = tk.Frame(self, bg=BG_CARD, height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        tk.Label(bar, text="●", bg=BG_CARD, fg=FG_GREEN,
                 font=("Courier", 10)).pack(side="left", padx=(12, 4))

        self.status_var = tk.StringVar(
            value="Ready · Sessions auto-logged from all cracking windows")
        tk.Label(bar, textvariable=self.status_var,
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 9)).pack(side="left")

        tk.Label(bar, text="Compliance-ready · audit trail",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("Courier", 9)).pack(side="right", padx=12)

    def _set_status(self, msg):
        self.status_var.set(msg)

    # ── Load sessions ─────────────────────────────────
    def _load_sessions(self):
        self.sessions = load_sessions()
        self.log_tree.delete(*self.log_tree.get_children())

        total_cracked = 0
        type_counts   = {}

        for s in reversed(self.sessions):
            stype   = s.get("type", "—")
            details = s.get("details", {})
            cracked = details.get("cracked", 0)
            elapsed = details.get("elapsed", "—")
            summary = details.get("summary", f"{cracked} cracked")

            total_cracked += cracked
            type_counts[stype] = type_counts.get(stype, 0) + 1

            tag = {
                "Hash Crack":  "hashcrack",
                "Hybrid":      "hybrid",
                "Wordlist":    "wordlist",
                "Rule Engine": "rule",
                "Rainbow":     "rainbow",
            }.get(stype, "other")

            self.log_tree.insert("", "end",
                                 values=(s.get("id", ""),
                                         s.get("timestamp", ""),
                                         stype, summary,
                                         str(elapsed)),
                                 tags=(tag,))

        self.summary_vars["Sessions"].set(str(len(self.sessions)))
        self.summary_vars["Total cracked"].set(str(total_cracked))
        self.summary_vars["Hash Crack"].set(
            str(type_counts.get("Hash Crack", 0)))
        self.summary_vars["Hybrid"].set(
            str(type_counts.get("Hybrid", 0)))
        self.summary_vars["Wordlist"].set(
            str(type_counts.get("Wordlist", 0)))

        self._update_preview()
        self._set_status(
            f"{len(self.sessions)} sessions loaded · "
            f"{total_cracked} total cracked")

    # ── Session select ────────────────────────────────
    def _on_session_select(self, event):
        if self.log_tree.selection():
            self._set_status(
                "Session selected · will be included in report")

    # ── Add test session ──────────────────────────────
    def _add_test_session(self):
        log_session("Hash Crack", {
            "cracked":    3,
            "total":      3,
            "elapsed":    "0.08s",
            "summary":    "3/3 cracked · MD5",
            "algorithms": ["MD5"],
        })
        self._load_sessions()
        self._set_status("Test session added")

    # ── Delete selected ───────────────────────────────
    def _delete_selected(self):
        selected = self.log_tree.selection()
        if not selected:
            messagebox.showwarning("None selected",
                                   "Click a session row first.")
            return
        values = self.log_tree.item(selected[0], "values")
        sid = int(values[0]) if values else None

        if sid is not None:
            self.sessions = [s for s in self.sessions
                             if s.get("id") != sid]
            from core.session_logger import _save
            _save(self.sessions)

        self._load_sessions()

    # ── Generate report ───────────────────────────────
    def _generate_report(self):
        if not self.sessions:
            messagebox.showwarning(
                "No Sessions",
                "No sessions logged yet.\n"
                "Run a crack session first or click 'Add test session'.")
            return

        fmt     = self.report_format.get()
        ext_map = {"TXT": ".txt", "CSV": ".csv",
                   "JSON": ".json", "HTML": ".html"}
        ext  = ext_map.get(fmt, ".txt")
        path = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=[(f"{fmt} files", f"*{ext}")],
            initialfile=f"pentest_report{ext}")

        if not path:
            return

        analyst = self.analyst_var.get().strip()
        target  = self.target_var.get().strip()
        scope   = self.scope_var.get().strip()
        now     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if fmt == "TXT":
            self._write_txt(path, analyst, target, scope, now)
        elif fmt == "CSV":
            self._write_csv(path)
        elif fmt == "JSON":
            self._write_json(path, analyst, target, scope, now)
        elif fmt == "HTML":
            self._write_html(path, analyst, target, scope, now)

        count = int(self.summary_vars["Reports made"].get()) + 1
        self.summary_vars["Reports made"].set(str(count))

        messagebox.showinfo("Report Generated",
                            f"Report saved to:\n{path}")
        self._set_status(f"Report generated: {path}")

    # ── TXT report ────────────────────────────────────
    def _write_txt(self, path, analyst, target, scope, now):
        total   = len(self.sessions)
        cracked = sum(s["details"].get("cracked", 0)
                      for s in self.sessions)

        lines = [
            "=" * 60,
            "  PENETRATION TEST REPORT",
            "=" * 60,
            f"  Analyst:    {analyst or 'N/A'}",
            f"  Engagement: {target or 'N/A'}",
            f"  Scope:      {scope or 'N/A'}",
            f"  Date:       {now}",
            "  Tool:       CryptX v2.0",
            "=" * 60,
            "",
            "EXECUTIVE SUMMARY",
            "-" * 40,
            f"  Total sessions:    {total}",
            f"  Passwords cracked: {cracked}",
            f"  Crack rate:        "
            + (f"{round(cracked/total*100,1)}%" if total else "N/A"),
            "",
        ]

        if self.include_opts["Session log"].get():
            lines += ["SESSION LOG", "-" * 40]
            for s in self.sessions:
                d = s["details"]
                lines.append(
                    f"  [{s['timestamp']}]  "
                    f"{s['type']:<14}  {d.get('summary','')}")

        if self.include_opts["Cracked passwords"].get():
            lines += ["", "CRACKED PASSWORDS", "-" * 40]
            for s in self.sessions:
                for p in s["details"].get("passwords", [])[:10]:
                    lines.append(f"  {p}")

        if self.include_opts["Recommendations"].get():
            lines += [
                "", "RECOMMENDATIONS", "-" * 40,
                "  1. Enforce minimum password length of 12 characters.",
                "  2. Require uppercase, lowercase, numbers and symbols.",
                "  3. Implement account lockout after 5 attempts.",
                "  4. Use bcrypt or argon2 — never MD5 or SHA1.",
                "  5. Enable MFA for all accounts.",
                "  6. Deploy a password manager organisation-wide.",
            ]

        lines += [
            "", "=" * 60,
            f"  Report generated: {now}",
            "  Tool: CryptX v2.0",
            "=" * 60,
        ]

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    # ── CSV report ────────────────────────────────────
    def _write_csv(self, path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Timestamp", "Type",
                             "Cracked", "Total", "Elapsed", "Summary"])
            for s in self.sessions:
                d = s["details"]
                writer.writerow([
                    s.get("id", ""),
                    s.get("timestamp", ""),
                    s.get("type", ""),
                    d.get("cracked", 0),
                    d.get("total", 0),
                    d.get("elapsed", ""),
                    d.get("summary", ""),
                ])

    # ── JSON report ───────────────────────────────────
    def _write_json(self, path, analyst, target, scope, now):
        data = {
            "report": {
                "analyst":    analyst,
                "engagement": target,
                "scope":      scope,
                "generated":  now,
                "tool":       "CryptX v2.0",
            },
            "summary": {
                "total_sessions": len(self.sessions),
                "total_cracked":  sum(s["details"].get("cracked", 0)
                                      for s in self.sessions),
            },
            "sessions": self.sessions,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ── HTML report ───────────────────────────────────
    def _write_html(self, path, analyst, target, scope, now):
        total   = len(self.sessions)
        cracked = sum(s["details"].get("cracked", 0)
                      for s in self.sessions)
        rate    = round(cracked / total * 100, 1) if total else 0

        rows = ""
        for s in self.sessions:
            d = s["details"]
            rows += (
                f"<tr>"
                f"<td>{s.get('id','')}</td>"
                f"<td>{s.get('timestamp','')}</td>"
                f"<td>{s.get('type','')}</td>"
                f"<td>{d.get('summary','')}</td>"
                f"<td>{d.get('elapsed','')}</td>"
                f"</tr>\n")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Pentest Report — {target}</title>
<style>
  body{{font-family:monospace;background:#1e1e2e;color:#cbd5e1;padding:40px;}}
  h1{{color:#7dd3fc;}}
  h2{{color:#7dd3fc;border-bottom:1px solid #3a3a50;padding-bottom:6px;}}
  table{{width:100%;border-collapse:collapse;margin:16px 0;}}
  th{{background:#2a2a3e;color:#64748b;padding:8px 12px;text-align:left;font-size:12px;}}
  td{{padding:8px 12px;border-bottom:1px solid #3a3a50;font-size:12px;}}
  .stat{{display:inline-block;background:#2a2a3e;border:1px solid #3a3a50;
         border-radius:8px;padding:12px 24px;margin:8px;text-align:center;}}
  .stat-n{{font-size:28px;font-weight:bold;color:#7dd3fc;}}
  .stat-l{{font-size:11px;color:#64748b;}}
  .rec{{background:#1e3a2a;border-left:3px solid #22c55e;
        padding:8px 16px;margin:6px 0;border-radius:0 6px 6px 0;}}
</style>
</head>
<body>
<h1>Penetration Test Report</h1>
<p><strong>Analyst:</strong> {analyst or 'N/A'}</p>
<p><strong>Engagement:</strong> {target or 'N/A'}</p>
<p><strong>Scope:</strong> {scope or 'N/A'}</p>
<p><strong>Date:</strong> {now}</p>
<p><strong>Tool:</strong> CryptX v2.0</p>

<h2>Executive Summary</h2>
<div>
  <div class="stat">
    <div class="stat-n">{total}</div>
    <div class="stat-l">Sessions</div>
  </div>
  <div class="stat">
    <div class="stat-n" style="color:#22c55e">{cracked}</div>
    <div class="stat-l">Cracked</div>
  </div>
  <div class="stat">
    <div class="stat-n" style="color:#fbbf24">{rate}%</div>
    <div class="stat-l">Crack rate</div>
  </div>
</div>

<h2>Session Log</h2>
<table>
<tr><th>#</th><th>Timestamp</th><th>Type</th><th>Summary</th><th>Time</th></tr>
{rows}
</table>

<h2>Recommendations</h2>
<div class="rec">1. Enforce minimum password length of 12 characters.</div>
<div class="rec">2. Require uppercase, lowercase, numbers and symbols.</div>
<div class="rec">3. Implement account lockout after 5 failed attempts.</div>
<div class="rec">4. Use bcrypt or argon2 — never MD5 or SHA1 for passwords.</div>
<div class="rec">5. Enable MFA for all privileged accounts.</div>
<div class="rec">6. Deploy a password manager organisation-wide.</div>

<p style="color:#64748b;margin-top:40px;font-size:11px;">
Report generated: {now}<br>
Tool: CryptX v2.0<br>
For authorized use only.
</p>
</body>
</html>"""

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

    # ── Export HTML shortcut ──────────────────────────
    def _export_html(self):
        self._select_format("HTML")
        self._generate_report()

    # ── Import CSV results ────────────────────────────
    def _import_csv(self):
        path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                rows    = list(csv.DictReader(f))
                total   = len(rows)
                cracked = sum(1 for r in rows
                              if r.get("status", "") == "Cracked")

            log_session("Hash Crack", {
                "cracked": cracked,
                "total":   total,
                "elapsed": "imported",
                "summary": f"{cracked}/{total} cracked (imported)",
            })
            self._load_sessions()
            self._set_status(f"Imported: {cracked}/{total} cracked")
        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    # ── Clear logs ────────────────────────────────────
    def _clear_logs(self):
        if not messagebox.askyesno("Clear All Logs",
                                   "Delete all session logs?\n"
                                   "This cannot be undone."):
            return
        clear_sessions()
        self.sessions = []
        self.log_tree.delete(*self.log_tree.get_children())
        for v in self.summary_vars.values():
            v.set("0")
        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        self.preview_box.configure(state="disabled")
        self._set_status("All logs cleared")