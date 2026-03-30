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


def runtime_work_dir() -> Path:
    """Fixed workspace for YazioExport.exe (token, days.json, products.json)."""
    return project_root() / "data" / "runtime" / "work"


def suggested_exporter_exe() -> Path | None:
    """First existing candidate path for the upstream YazioExport.exe (user may place it locally)."""
    root = project_root()
    candidates = [
        root / "exporter" / "YazioExport-windows" / "YazioExport.exe",
        root / "YazioExport.exe",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None
