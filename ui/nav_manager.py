import tkinter as tk
from tkinter import ttk

# Common colors and styles (to be synced across modules)
BG_DARK    = "#1e1e2e"
BG_CARD    = "#2a2a3e"
FG_PRIMARY = "#cbd5e1"
FG_MUTED   = "#64748b"
FG_BLUE    = "#7dd3fc"
BG_ACCENT  = "#1e3a4a"
BORDER     = "#3a3a50"

class NavigationManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw() # Hide immediately to prevent launch flicker
        
        self.title("CryptX v2.0")
        
        self.width = 1100
        self.height = 750 
        self.minsize(950, 500)
        self.configure(bg=BG_DARK)

        # History stack (list of frames)
        self.history = []
        self.current_frame = None
        
        # View cache to make switching near-instant
        self.views = {}

        self._init_ui()

    def _center_window(self):
        """Dynamic centering: snaps window height to content requirements."""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        req_height = self.winfo_reqheight()
        req_width  = self.winfo_reqwidth()

        self.height = min(req_height + 4, screen_height - 80)
        self.width  = max(1100, min(req_width, screen_width - 40))
        
        x = (screen_width // 2) - (self.width // 2)
        y = (screen_height // 2) - (self.height // 2)
        
        y = max(20, y) 
        self.geometry(f"{self.width}x{self.height}+{x}+{y}")

    def _init_ui(self):
        # ── Navbar (Header) ──────
        self.navbar = tk.Frame(self, bg=BG_CARD, height=36)
        self.navbar.pack(fill="x")
        self.navbar.pack_propagate(False)

        # Back button (Hidden on Home)
        self.back_btn = tk.Button(
            self.navbar,
            text="← BACK",
            bg=BG_CARD,
            fg=FG_BLUE,
            font=("Courier", 10, "bold"),
            relief="flat",
            command=self.pop_view,
            cursor="hand2",
            padx=15
        )
        self.back_btn.pack(side="left", fill="y")
        self.back_btn.pack_forget()

        # App Title in Navbar
        self.title_label = tk.Label(
            self.navbar,
            text="CRYPTX: AI-Powered Password Vulnerability Analyzer v2.0",
            bg=BG_CARD,
            fg=FG_MUTED,
            font=("Courier", 10)
        )
        self.title_label.pack(side="left", padx=20)

        # ── Main Container (Standard Frame) ──────
        self.main_area = tk.Frame(self, bg=BG_DARK)
        self.main_area.pack(fill="both", expand=True, padx=0, pady=0)

    def show_view(self, view_class, *args, **kwargs):
        """High-performance view switcher with caching and smart state transitions."""
        target_name = view_class.__name__
        is_home = (target_name == "LauncherFrame")
        
        # 1. Determine if we need to hide the window
        # We only withdraw if we are changing between 'zoomed' and 'normal' states
        current_state = self.state()
        target_state = "normal" if is_home else "zoomed"
        needs_masking = (current_state != target_state) or (current_state == "withdrawn")

        if needs_masking and current_state != "withdrawn":
            self.withdraw()
            self.update_idletasks()

        # 2. Swap the frame (Optimized with caching)
        if self.current_frame:
            # We don't destroy cached views, just unmap them
            self.current_frame.pack_forget()

        if target_name in self.views:
            self.current_frame = self.views[target_name]
        else:
            # Create and cache
            self.current_frame = view_class(self.main_area, self, *args, **kwargs)
            self.views[target_name] = self.current_frame

        self.current_frame.pack(fill="both", expand=True)

        # 3. Update navigation state
        if self.history:
             self.back_btn.pack(side="left", fill="y")
        else:
             self.back_btn.pack_forget()

        # 4. Handle State & Geometry
        if is_home:
            if self.state() == "zoomed":
                self.state("normal")
            self._center_window()
        else:
            if self.state() != "zoomed":
                self.state("zoomed")

        # 5. Show window (Instant if no state change, otherwise fast reveal)
        if needs_masking:
            # Reduced delay to 50ms for snappy feel
            self.after(50, lambda: (
                self.deiconify(),
                self.lift(),
                self.focus_force(),
                self.update_idletasks()
            ))
        else:
            self.update_idletasks()
            self.lift()
            self.focus_force()

    def push_view(self, view_class, *args, **kwargs):
        """Pushes current view to history stack and shows new view."""
        self.history.append(view_class)
        self.show_view(view_class, *args, **kwargs)

    def pop_view(self):
        """Returns to the previous screen in history."""
        if not self.history:
            return

        self.history.pop()
        if not self.history:
            from ui.launcher import LauncherFrame
            self.show_view(LauncherFrame)
        else:
            prev_view = self.history[-1]
            self.show_view(prev_view)
