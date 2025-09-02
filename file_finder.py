import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import Menu, ttk
import subprocess
import platform
import pyperclip
import threading

SETTINGS_FILE = "settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {"search_folders": []}

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

def count_total_files(folders):
    total = 0
    for folder in folders:
        for _, _, files in os.walk(folder):
            total += len(files)
    return total

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
        self.root.geometry("700x650")

        self.settings = load_settings()
        self.results = []
        self.cancel_search = False
        self.search_thread = None

        self.create_widgets()

    def create_widgets(self):
        # Search input
        tk.Label(self.root, text="Search (type filename then click Search):").pack(anchor='w', padx=2, pady=(10, 0))
        search_frame = tk.Frame(self.root)
        search_frame.pack(padx=5, pady=5, fill='x')

        self.pattern_entry = tk.Entry(search_frame, width=50)
        self.pattern_entry.pack(side=tk.LEFT, padx=(0, 5))

        self.search_button = tk.Button(search_frame, text="🔍 Search", command=self.perform_search)
        self.search_button.pack(side=tk.LEFT)

        self.cancel_button = tk.Button(search_frame, text="❌ Cancel", command=self.cancel_search_action)
        self.cancel_button.pack(side=tk.LEFT)
        self.cancel_button.pack_forget()  # hidden by default

        # Progress bar
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=500, mode="determinate")
        self.progress.pack(pady=5)

        # Folder list
        tk.Label(self.root, text="Search Folders:").pack(anchor='w', padx=10)
        self.folder_listbox = tk.Listbox(self.root, height=5)
        self.folder_listbox.pack(fill='x', padx=10)

        for folder in self.settings["search_folders"]:
            self.folder_listbox.insert(tk.END, folder)

        # Folder buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5)
        tk.Button(button_frame, text="➕ Add Folder", command=self.add_folder).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="❌ Remove Selected", command=self.remove_folder).pack(side=tk.LEFT)

        # Results
        self.result_listbox = tk.Listbox(self.root)
        self.result_listbox.pack(fill='both', expand=True, padx=10, pady=5)
        self.result_listbox.bind("<Double-Button-1>", self.on_double_click)
        self.result_listbox.bind("<Button-3>", self.show_context_menu)

        # Context menu
        self.context_menu = Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="📋 Copy Path", command=self.copy_path)
        self.context_menu.add_command(label="📂 Open File Location", command=self.open_file_location)

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
            messagebox.showerror("Error", "Please enter text to search.")
            return

        self.pattern_entry.config(state="disabled")
        self.search_button.config(state="disabled")
        self.cancel_button.pack(side=tk.LEFT)

        self.result_listbox.delete(0, tk.END)
        self.result_listbox.insert(tk.END, "🔄 Searching...")

        self.progress["value"] = 0
        self.cancel_search = False

        # Start threaded search
        self.search_thread = threading.Thread(target=self._do_search, args=(text,))
        self.search_thread.start()

    def _do_search(self, text):
        folders = self.settings["search_folders"]
        total_files = count_total_files(folders)
        matches = []
        processed = 0

        for folder in folders:
            for root, _, files in os.walk(folder):
                for file in files:
                    if self.cancel_search:
                        self._update_ui_on_finish([], canceled=True)
                        return
                    processed += 1
                    if text.lower() in file.lower():
                        matches.append(os.path.join(root, file))
                    self.root.after(0, self._update_progress, processed, total_files)

        self._update_ui_on_finish(matches)

    def _update_progress(self, done, total):
        self.progress["maximum"] = total
        self.progress["value"] = done

    def _update_ui_on_finish(self, results, canceled=False):
        def update():
            self.result_listbox.delete(0, tk.END)
            if canceled:
                self.result_listbox.insert(tk.END, "❌ Search canceled.")
            elif results:
                for path in results:
                    self.result_listbox.insert(tk.END, path)
                self.results = results
            else:
                self.result_listbox.insert(tk.END, "No files found.")

            self.pattern_entry.config(state="normal")
            self.search_button.config(state="normal")
            self.cancel_button.pack_forget()
        self.root.after(0, update)

    def cancel_search_action(self):
        self.cancel_search = True

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
    root = tk.Tk()
    app = FileFinderApp(root)
    root.mainloop()
