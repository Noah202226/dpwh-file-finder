# 🔍 Document File Finder - DPWH

A simple **Python GUI tool** to search for files across multiple folders by:
- Partial filename  
- Extension (e.g. `.pdf`, `.docx`)  
- Pattern (e.g. `*.pdf`)  

Built with **Tkinter** for GUI, and supports:
- 📂 Add / remove default search folders (saved in `settings.json`)  
- 🚀 Live progress bar while searching  
- ❌ Cancel ongoing search  
- 📋 Copy file path  
- 📂 Open file or open file location directly  
- ⚡ Standalone executable build  

---

## 📥 Installation

1. Clone or download the source code:

```bash
git clone https://github.com/YOUR-REPO/document-file-finder.git
cd document-file-finder

pip install pyperclip

pip install pyinstaller
pyinstaller --onefile --windowed file_finder.py
