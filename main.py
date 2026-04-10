from ui.nav_manager import NavigationManager
from ui.launcher import LauncherFrame

if __name__ == "__main__":
    app = NavigationManager()
    app.show_view(LauncherFrame)
    app.mainloop()