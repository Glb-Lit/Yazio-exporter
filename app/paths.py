"""Project root and runtime paths (dev vs PyInstaller bundle)."""

from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    """Directory used for `data/runtime` and other app-local files.

    - Dev: repository root (parent of the `app` package).
    - Frozen (PyInstaller): directory containing the executable.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent

def tmp_files() -> Path:
    return project_root() / "data_tmp"

def runtime_work_dir() -> Path:
    """Fixed workspace for YazioExport.exe (token, days.json, products.json)."""
    return project_root() / "data_tmp" / "runtime" / "work"


import sys
from pathlib import Path


def suggested_exporter_exe() -> Path | None:
    """Find YazioExport.exe in dev and in PyInstaller bundle."""

    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
        candidates = [
            base / "helper" / "YazioExport.exe",
        ]
    else:
        root = project_root()
        candidates = [
            root / "helper" / "YazioExport.exe",
            root / "YazioExport.exe",
        ]

    for path in candidates:
        if path.is_file():
            return path

    return None