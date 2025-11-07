# ProjectSearchBar — Prototype README
Author: Brandon Gallegos

> Local-first academic search with LaTeX-aware queries, dual ranking (TF-IDF cosine + BM25), and agentic AI for cited answers.

---

## What this is
- A prototype for the UNM/CNM App Contest.
- Runs on localhost. Data stays on your machine.
- Works in a browser or as a desktop window (pywebview).

## Features
- Mixed text + LaTeX queries (ASCII and Unicode math supported).
- Dual ranking: TF-IDF cosine and BM25 with visible score bars.
- Metadata enrichment from arXiv when online; graceful offline mode.
- Per-paper AI chat with exact quotes and `[paperId]` citations.
- Single “Research Agent” to read Top-N papers and report `FOUND/NOT_FOUND` with quoted evidence.
- Debug tokenization endpoint to see how your query is parsed.

---

## System requirements
- Python 3.9+ (3.10+ recommended)
- SQLite (bundled with Python)
- Optional: `pywebview` for desktop window (`pip install pywebview`)

---

## Install and run

### Option A — Quick start (zip + launchers)
1) Download the project zip and extract it.
2) Launch:
   - **Windows:** double-click `Run-ProjectSearchBar-Windows.vbs`  
     or run `launch_windows.bat` in a console.  
     To build a standalone exe:  
     ```powershell
     ./build_windows_exe.ps1
     .\dist\ProjectSearchBar.exe
     ```
   - **Linux:** double-click `ProjectSearchBar.desktop`  
     If blocked: right-click → Properties → Permissions → “Allow executing file as a program”.
   - **Linux/macOS (console):**
     ```bash
     ./ProjectSearchBar/launch.sh
     ```

### Option B — Manual venv
- **Linux/macOS**
  ```bash
  cd /path/to/ProjectSearchBar
  python3 -m venv .venv && . .venv/bin/activate
  pip install -r requirements.txt
  python3 launch.py
