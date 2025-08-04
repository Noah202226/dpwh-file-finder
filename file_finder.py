import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import Menu
from threading import Timer
import subprocess
import platform
import pyperclip

SETTINGS_FILE = "settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {"search_folders": []}

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

def search_files_by_contains(text, folders):
    matches = []
    text = text.lower()
    for folder in folders:
        for root, dirs, files in os.walk(folder):
            for file in files:
                if text in file.lower():
                    matches.append(os.path.join(root, file))
    return matches

def open_file(path):
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
    except Exception as e:
        messagebox.showerror("Error", f"Could not open file:\n{e}")

def open_folder(path):
    folder = os.path.dirname(path)
    if platform.system() == "Windows":
        subprocess.run(['explorer', '/select,', os.path.normpath(path)])
    elif platform.system() == "Darwin":
        subprocess.call(["open", "-R", path])
    else:
        subprocess.call(["xdg-open", folder])

class FileFinderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🔍 Document File Finder - DPWH")
        self.root.geometry("700x600")

        self.settings = load_settings()
        self.search_timer = None
        self.results = []

        self.create_widgets()

    def create_widgets(self):
        # Search input
        tk.Label(self.root, text="Search (auto match filenames):").pack(anchor='w', padx=2, pady=(10, 0))
        self.pattern_entry = tk.Entry(self.root, width=60)
        self.pattern_entry.pack(padx=5, pady=5)
        self.pattern_entry.bind("<KeyRelease>", self.on_text_change)

        # Folder list display
        tk.Label(self.root, text="Search Folders:").pack(anchor='w', padx=10)
        self.folder_listbox = tk.Listbox(self.root, height=5)
        self.folder_listbox.pack(fill='x', padx=10)

        for folder in self.settings["search_folders"]:
            self.folder_listbox.insert(tk.END, folder)

        # Add/remove folder buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5)

        tk.Button(button_frame, text="➕ Add Folder", command=self.add_folder).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="❌ Remove Selected", command=self.remove_folder).pack(side=tk.LEFT)

        # Result list
        self.result_listbox = tk.Listbox(self.root)
        self.result_listbox.pack(fill='both', expand=True, padx=10, pady=5)
        self.result_listbox.bind("<Double-Button-1>", self.on_double_click)
        self.result_listbox.bind("<Button-3>", self.show_context_menu)

        # Context menu
        self.context_menu = Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="📋 Copy Path", command=self.copy_path)
        self.context_menu.add_command(label="📂 Open File Location", command=self.open_file_location)

    def on_text_change(self, event):
        if self.search_timer:
            self.search_timer.cancel()
        self.search_timer = Timer(0.5, lambda: self.root.after(0, self.perform_search))
        self.search_timer.start()

    def add_folder(self):
        folder = filedialog.askdirectory()
        if folder and folder not in self.settings["search_folders"]:
            self.settings["search_folders"].append(folder)
            self.folder_listbox.insert(tk.END, folder)
            save_settings(self.settings)

    def remove_folder(self):
        selected = self.folder_listbox.curselection()
        if selected:
            index = selected[0]
            folder = self.folder_listbox.get(index)
            self.folder_listbox.delete(index)
            self.settings["search_folders"].remove(folder)
            save_settings(self.settings)

    def perform_search(self):
        text = self.pattern_entry.get().strip()
        if not text:
            return

        self.pattern_entry.config(state="disabled")  # disable typing
        self.result_listbox.delete(0, tk.END)
        self.result_listbox.insert(tk.END, "🔄 Searching...")

        # Perform search in background (avoid freezing UI)
        self.root.after(200, lambda: self._do_search(text))

    def _do_search(self, text):
        self.results = search_files_by_contains(text, self.settings["search_folders"])
        self.result_listbox.delete(0, tk.END)

        if self.results:
            for path in self.results:
                self.result_listbox.insert(tk.END, path)
        else:
            self.result_listbox.insert(tk.END, "No files found.")

        self.pattern_entry.config(state="normal")  # re-enable typing

    def on_double_click(self, event):
        selection = self.result_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.results):
                open_file(self.results[index])

    def show_context_menu(self, event):
        widget = event.widget
        index = widget.nearest(event.y)
        if index < len(self.results):
            widget.selection_clear(0, tk.END)
            widget.selection_set(index)
            self.context_menu.tk_popup(event.x_root, event.y_root)
            self.context_menu.selection_index = index

    def copy_path(self):
        selection = self.result_listbox.curselection()
        if selection:
            path = self.results[selection[0]]
            pyperclip.copy(path)

    def open_file_location(self):
        selection = self.result_listbox.curselection()
        if selection:
            path = self.results[selection[0]]
            open_folder(path)

if __name__ == "__main__":
    try:
        import pyperclip
    except ImportError:
        messagebox.showerror("Missing Dependency", "Please install 'pyperclip' with:\n\npip install pyperclip")
        raise

    root = tk.Tk()
    app = FileFinderApp(root)
    root.mainloop()
