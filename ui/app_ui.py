import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
from core.cracker import crack_passwords

def build_ui(root):
    root.title("Hash Cracker")
    root.resizable(False, False)
    root.configure(padx=16, pady=16)

    tk.Label(root, text="Hash file:").grid(row=0, column=0, sticky="w")
    hash_entry = tk.Entry(root, width=52)
    hash_entry.grid(row=0, column=1, padx=6, pady=4)
    tk.Button(root, text="Browse",
              command=lambda: select_file(hash_entry)).grid(row=0, column=2)

    tk.Label(root, text="Wordlist:").grid(row=1, column=0, sticky="w")
    wl_entry = tk.Entry(root, width=52)
    wl_entry.grid(row=1, column=1, padx=6, pady=4)
    tk.Button(root, text="Browse",
              command=lambda: select_file(wl_entry)).grid(row=1, column=2)

    output = scrolledtext.ScrolledText(root, width=80, height=22,
                                       font=("Courier", 10))
    output.grid(row=2, column=0, columnspan=3, pady=10)

    btn_frame = tk.Frame(root)
    btn_frame.grid(row=3, column=0, columnspan=3)

    tk.Button(btn_frame, text="Start Cracking", width=20,
              command=lambda: start_cracking(hash_entry, wl_entry, output)
              ).pack(side="left", padx=6)

    tk.Button(btn_frame, text="Clear Output", width=14,
              command=lambda: output.delete("1.0", tk.END)
              ).pack(side="left", padx=6)

def select_file(entry_widget):
    path = filedialog.askopenfilename()
    if path:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, path)

def start_cracking(hash_entry, wl_entry, output_text):
    hf = hash_entry.get().strip()
    wf = wl_entry.get().strip()
    if not hf or not wf:
        messagebox.showwarning("Input Error", "Please select both hash and wordlist files.")
        return
    t = threading.Thread(target=crack_passwords, args=(hf, wf, output_text), daemon=True)
    t.start()

def open_cracker_window(parent):
    """Opens the hash cracker as a child window from the launcher."""
    win = tk.Toplevel(parent)
    win.withdraw()
    win.title("Hash Cracker")
    win.configure(padx=16, pady=16)
    build_ui(win)