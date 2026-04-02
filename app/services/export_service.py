import shutil
import subprocess
from pathlib import Path
from typing import Callable

from app.config import ExportSettings
from app.paths import runtime_work_dir, tmp_files
from app.services.excel_service import build_excel_report
from app.services.parser_service import parse_reports

LogFn = Callable[[str], None]


class ExportService:
    def run(self, settings: ExportSettings, log: LogFn | None = None) -> Path:
        logger = log or (lambda _: None)

        if not settings.exporter_exe.exists():
            raise FileNotFoundError(f"Yazio exporter not found: {settings.exporter_exe}")

        cwd = runtime_work_dir()
        work_dir = runtime_work_dir()
        work_dir.mkdir(parents=True, exist_ok=True)

        token_file = work_dir / "token.txt"
        days_file = work_dir / "days.json"
        products_file = work_dir / "products.json"

        logger("Logging in to Yazio...")
        subprocess.run(
            [
                str(settings.exporter_exe),
                "login",
                settings.email,
                settings.password,
                "--out",
                str(token_file),
            ],
            check=True,
            cwd=str(cwd),
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        logger("Exporting diary data... (it may take some time)")
        subprocess.run(
            [
                str(settings.exporter_exe),
                "days",
                "--token",
                str(token_file),
                "--what",
                "all",
                "--from",
                settings.date_from,
                "--to",
                settings.date_to,
                "--out",
                str(days_file),
            ],
            check=True,
            cwd=str(cwd),
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        logger("Exporting product data...")
        subprocess.run(
            [
                str(settings.exporter_exe),
                "products",
                "--token",
                str(token_file),
                "--from",
                str(days_file),
                "-o",
                str(products_file),
            ],
            check=True,
            cwd=str(cwd),
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        logger("Building report tables...")
        nutrition_rows, meal_rows, daily_rows = parse_reports(days_file=days_file, products_file=products_file)

        logger("Generating Excel workbook...")
        build_excel_report(
            output_path=settings.output_xlsx,
            nutrition_rows=nutrition_rows,
            meal_rows=meal_rows,
            daily_rows=daily_rows,
        )

        logger(f"Done: {settings.output_xlsx}")
        shutil.rmtree(tmp_files(), ignore_errors=True)
        return settings.output_xlsx
