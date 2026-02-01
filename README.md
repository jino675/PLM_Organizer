# PLM Organizer (v1.8.13)

**PLM Organizer** is a desktop automation tool designed to streamline the workflow of downloading and organizing PLM (Product Lifecycle Management) data. It automatically detects, unzips, and organizes downloads based on the context of the active PLM web page.

---

## ✨ Key Features

### 1. 📂 Context-Aware Filing
- Automatically detects which PLM project page you are viewing in Chrome/Edge.
- Downloads are organized into folders named after the project/part (e.g., `Downloads/Project_A_Part_123/`).
- **Smart Context Switching**: Recognizes when you leave the PLM site and pauses organization to prevent accidental filing.

### 2. ⚡ Robust Batch Processing
- **Queue System**: Handles multiple simultaneous downloads without files getting mixed up.
- **Twin-Thread Prevention**: preventing "File Not Found" errors caused by duplicate events.

### 3. 📦 Advanced Auto-Unzip
- **Zip-First Strategy**: Extracts files in the Downloads folder *before* moving them, ensuring data integrity.
- **Smart Fallback**:
    - **Priority 1**: Uses Windows `tar` (Faster, supports Long Paths > 260 chars).
    - **Priority 2**: Python `zipfile` (Legacy support).
- **Corrupt File Handling**: Moves the original ZIP even if extraction fails, so you never lose data.

### 4. 🛠️ Reliability
- **0-Byte Guard**: Waits for files to be fully written (handling Innorix/Network delays).
- **Process Protection**: Automatically kills zombie processes on shutdown.
- **Process Log**: `error_log.txt` captures startup crashes for easy debugging.

---

## 🚀 Getting Started

### Prerequisites
- Windows 10 or 11
- Python 3.9+ (if running from source)
- Chrome or Edge Browser
- **Extension**: PLM Organizer Context Extension installed in your browser.

### Running from Source
1.  Clone this repository.
2.  Double-click **`run.bat`**.
    - It will automatically create a virtual environment (`venv`).
    - It will install dependencies (`PyQt6`, `watchdog`, `pywin32`, etc.).
    - It will launch the GUI.

---

## 📦 Deployment (Building EXE)

To distribute this application to users who don't have Python installed:

1.  Run **`build.bat`** in the project root.
2.  Wait for the build to complete.
3.  The executable will be generated at **`dist/PLM_Organizer.exe`**.
4.  Share this single `.exe` file.

**Note**: Do **NOT** commit the `.exe` file to Git.

---

## 🛠️ Architecture Overview

- **`main.py`**: Application entry point. Handles crash logging (`sys.excepthook`) and silent mode.
- **`app/watcher.py`**: Monitors the Downloads folder using `watchdog`. Handles threading and file verification (size/lock checks).
- **`app/organizer.py`**: Core logic. Determines where to move files and how to unzip them (Tar vs Zipfile).
- **`app/bridge.py`**: Efficient O(1) polling of the active browser window title to determine Context.
- **`app/gui.py`**: PyQt6 interface for settings and status logs.

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **GUI won't open** | Check `error_log.txt` in the project folder. |
| **"WinError 2" / File Not Found** | Already fixed in v1.8.10. If seen, check permissions. |
| **Unzip Failed** | Check if the filename is too long. The app will automatically try `tar` to fix this. |
| **App says "Unknown Context"** | Ensure the Browser Extension is active and you are on a valid PLM page. |

---

## 📜 Version History
- **v1.8.13**: Switched to `tar` as primary unzip method (Long Path support).
- **v1.8.11**: Thread-safe duplicate prevention (Mutex).
- **v1.8.9**: "Unzip-First" strategy introduced.
- **v1.8.7**: Batch download race condition fix.

---
*Created by [Your Name/Team]*
