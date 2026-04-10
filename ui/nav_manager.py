import tkinter as tk
from tkinter import ttk

# Common colors and styles (to be synced across modules)
BG_DARK    = "#1e1e2e"
BG_CARD    = "#2a2a3e"
FG_PRIMARY = "#cbd5e1"
FG_MUTED   = "#64748b"
FG_BLUE    = "#7dd3fc"
BORDER     = "#3a3a50"

class NavigationManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CryptX v2.0")
        self.geometry("900x750")
        self.minsize(800, 700)
        self.configure(bg=BG_DARK)

        # History stack (list of frames)
        self.history = []
        self.current_frame = None

        self._init_ui()

    def _init_ui(self):
        # ── Navbar (Header) ──────
        self.navbar = tk.Frame(self, bg=BG_CARD, height=44)
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
        self.back_btn.pack_forget()  # Hide initially

        # App Title in Navbar
        self.title_label = tk.Label(
            self.navbar,
            text="CRYPTX: AI-Powered Password Vulnerability Analyzer v2.0",
            bg=BG_CARD,
            fg=FG_MUTED,
            font=("Courier", 10)
        )
        self.title_label.pack(side="left", padx=20)

        # Main Container for views
        self.container = tk.Frame(self, bg=BG_DARK)
        self.container.pack(fill="both", expand=True)

    def show_view(self, view_class, *args, **kwargs):
        """Clears the current view and shows a new one. History is NOT pushed."""
        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = view_class(self.container, self, *args, **kwargs)
        self.current_frame.pack(fill="both", expand=True)

        # Update back button visibility
        if self.history:
             self.back_btn.pack(side="left", fill="y")
        else:
             self.back_btn.pack_forget()

    def push_view(self, view_class, *args, **kwargs):
        """Pushes current view to history stack and shows new view."""
        # Note: In Tkinter, we might want to store the class and its state,
        # but for simplicity, we destroy the old frame and just store the class for navigation back.
        # If we need state preservation, we could hide instead of destroy.
        
        # Here we only store the "Home" view for now as we transition.
        # Later, we can make it more generic.
        if self.current_frame:
            # We don't store the actual frame object usually because of resource management,
            # but we can store the class type if we want to re-instantiate it.
            # For this simple app, we just need a way to go back to Home.
            pass

        self.history.append(view_class)
        self.show_view(view_class, *args, **kwargs)

    def pop_view(self):
        """Returns to the previous screen in history."""
        if not self.history:
            return

        self.history.pop()  # Remove current
        if not self.history:
            # Go back to launcher (Home)
            from ui.launcher import LauncherFrame
            self.show_view(LauncherFrame)
        else:
            prev_view = self.history[-1]
            # Since we destroy frames to save resources, we re-instantiate.
            self.show_view(prev_view)
