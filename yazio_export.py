
"""Backward-compatible entry point for the new desktop app."""

from app.main import main


if __name__ == "__main__":
    raise SystemExit(main())
