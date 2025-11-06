from __future__ import annotations

from pathlib import Path
import os


"""
Configuration for ProjectSearchBar. Adds support for selecting between two UI
skins (ui1 and ui2). Default is ui2. You can override via env var:
  PROJECTSEARCHBAR_UI=ui1  -> use classic UI
  PROJECTSEARCHBAR_UI=ui2  -> use redesigned UI (default)
"""

# Base directories
BASE_DIR = Path(__file__).resolve().parent

# Allow overriding the data directory to support alternate locations (e.g., repo root)
_DATA_DIR_OVERRIDE = os.environ.get("PROJECTSEARCHBAR_DATA_DIR")
if _DATA_DIR_OVERRIDE:
    DATA_DIR = Path(_DATA_DIR_OVERRIDE).expanduser().resolve()
else:
    DATA_DIR = BASE_DIR / "data"

# UI root (UI2 only). Prefer the repo root UI (kept most up-to-date),
# falling back to the packaged UI if the external path is missing.
_PARENT = BASE_DIR.parent
_EXT_UI2 = _PARENT / "ui2" / "public"
if _EXT_UI2.exists():
    UI_PUBLIC = _EXT_UI2
    UI_PUBLIC_FALLBACK = BASE_DIR / "ui2" / "public"
else:
    UI_PUBLIC = BASE_DIR / "ui2" / "public"
    UI_PUBLIC_FALLBACK = None

# Ensure data folders exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / "vectors").mkdir(parents=True, exist_ok=True)

# External papers source (already downloaded)
# Default now points inside the project data folder.
# Override via env var PROJECTSEARCHBAR_PAPERS if desired.
PAPERS_SRC = Path(os.environ.get("PROJECTSEARCHBAR_PAPERS", str(DATA_DIR / "papers")))

# Local outputs
VECTORS_DIR = DATA_DIR / "vectors"
DB_PATH = DATA_DIR / "index.sqlite"

# Server settings
HOST = os.environ.get("PROJECTSEARCHBAR_HOST", "127.0.0.1")
PORT = int(os.environ.get("PROJECTSEARCHBAR_PORT", "8360") or 8360)
