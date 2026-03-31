# Yazio Desktop Exporter (MVP)

Windows desktop app that runs the [Yazio Exporter](https://github.com/funmelon64/Yazio-Exporter) pipeline and produces a single Excel workbook.

## What You Get

- Desktop UI on PySide6 (no manual terminal steps)
- Export by date range with your Yazio credentials
- One `.xlsx` output with sheets:
  - `nutrition_log`
  - `meal_summary`
  - `daily_summary`
- Basic formatting in Excel:
  - auto column widths
  - header row freeze
  - filters enabled

## Quick Start (Developer Run)

1. Install Python 3.11+ on Windows.
2. Build/download `YazioExport.exe` from [Yazio Exporter](https://github.com/funmelon64/Yazio-Exporter).
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start the desktop app:

```bash
python -m app.main
```

5. Put `YazioExport.exe` in `exporter/YazioExport-windows/` next to the project (or next to the built `.exe`), then in the app enter your Yazio email/password and where to save the `.xlsx` file. The app will export from the beginning of the current year up to today.

## Security and Data Handling

- Credentials are entered in UI and not stored in repository files.
- Intermediate files from the upstream exporter (`token.txt`, `days.json`, `products.json`) are written to a fixed workspace under `data/runtime/work/` (relative to the app / project root). The Yazio exporter expects stable paths; they are not deleted automatically after export (you can remove them manually). They are ignored by git via `.gitignore`.
- Do not log or commit token contents; the app only reports progress messages, not file payloads.

## Windows Release Build (GitHub Actions)

Workflow: `.github/workflows/release-windows.yml`

- Runs on `windows-latest`
- Builds standalone app with PyInstaller
- Uploads build artifact for every run
- Publishes release asset automatically on tag push (`v*`)

## Known Issues

- Export reliability depends on upstream `YazioExport.exe` behavior and API compatibility.
- Some product names can still contain encoding artifacts from source data.
- Nutrient totals are calculated from per-gram values in exported product data and may differ slightly from Yazio app UI totals.
- Large date ranges may take noticeable time due to upstream exporter calls.

## Project Structure

- `app/main.py` - desktop app entrypoint
- `app/paths.py` - project root and `data/runtime/work` (dev vs frozen exe)
- `app/ui/main_window.py` - PySide6 UI
- `app/services/export_service.py` - orchestration of external exporter + report generation
- `app/services/parser_service.py` - JSON parsing and summary aggregation
- `app/services/excel_service.py` - single workbook generation
- `data/runtime/work/` - local workspace for exporter output (gitignored except `.gitkeep`)

## License

MIT

## Disclaimer

## 🙌 Credits
Thanks to the awesome open-source project Yazio Exporter for enabling data access.

## ⚠️ Disclaimer

This tool is not officially supported, affiliated with, or endorsed by Yazio.  
It uses the [Yazio Exporter](https://github.com/funmelon64/Yazio-Exporter), an unofficial open-source utility, to access user data.  
Yazio does not provide public documentation for this export functionality, and the structure of exported data may change without notice.

Use at your own risk.
