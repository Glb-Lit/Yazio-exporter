from __future__ import annotations

import sys
from pathlib import Path

from datetime import date

from PySide6.QtCore import QSettings, QThread, Signal, Qt
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QBrush
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

try:
    from PySide6.QtSvgWidgets import QSvgWidget
except ImportError:  # pragma: no cover
    QSvgWidget = None  # type: ignore[misc, assignment]

from app.config import ExportSettings
from app.paths import suggested_exporter_exe
from app.services.export_service import ExportService


def _app_resource_path(*parts: str) -> Path:
    """Resolve paths under `app/` for dev and PyInstaller bundle (`_MEIPASS/app/...`)."""
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
        return base.joinpath("app", *parts)
    return Path(__file__).resolve().parent.parent.joinpath(*parts)


ICON_PATH = _app_resource_path("resources", "icon.svg")

_INPUT_ROW_FIXED_HEIGHT = 40


class GradientBackground(QWidget):
    """Soft green → yellow gradient behind the main card."""

    def paintEvent(self, event) -> None:  # noqa: ANN001
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, float(self.width()), float(self.height()))
        gradient.setColorAt(0.0, QColor("#e8f5e9"))
        gradient.setColorAt(0.45, QColor("#f1f8e9"))
        gradient.setColorAt(1.0, QColor("#fffde7"))
        painter.fillRect(self.rect(), QBrush(gradient))


class ExportWorker(QThread):
    log_signal = Signal(str)
    done_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, settings: ExportSettings, service: ExportService) -> None:
        super().__init__()
        self._settings = settings
        self._service = service

    def run(self) -> None:
        try:
            result = self._service.run(self._settings, self.log_signal.emit)
            self.done_signal.emit(str(result))
        except Exception as error:  # noqa: BLE001
            self.error_signal.emit(str(error))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Yazio export to Excel")
        if ICON_PATH.is_file():
            self.setWindowIcon(QIcon(str(ICON_PATH)))
        # Fixed window size so layout always looks the same.
        self.setFixedSize(460, 520)

        self._settings = QSettings("yazio-csv-exporter", "desktop")
        self.worker: ExportWorker | None = None
        self.service = ExportService()

        if ICON_PATH.is_file():
            self.setWindowIcon(QIcon(str(ICON_PATH)))

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.setClearButtonEnabled(True)
        self._apply_input_row_height(self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Password")
        self.password_input.setClearButtonEnabled(True)
        self._apply_input_row_height(self.password_input)

        default_out = Path.home() / "Documents" / "Yazio_nutrition_report.xlsx"
        self.output_path_input = QLineEdit(str(default_out.resolve()))
        self._apply_input_row_height(self.output_path_input)

        self.status_label = QLabel("Ready.")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #4a5f4a; font-size: 12px;")

        self.run_button = QPushButton("Create Excel report")
        self.run_button.setObjectName("primaryButton")
        self.run_button.setCursor(Qt.PointingHandCursor)
        self.run_button.clicked.connect(self._start_export)

        self._load_saved_settings()

        card = QFrame()
        card.setObjectName("card")
        card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(14)
        card_layout.setContentsMargins(28, 24, 28, 24)

        header_row = QHBoxLayout()
        header_row.setSpacing(14)

        if QSvgWidget is not None and ICON_PATH.is_file():
            icon_widget = QSvgWidget(str(ICON_PATH))
            icon_widget.setFixedSize(56, 56)
            header_row.addWidget(icon_widget, alignment=Qt.AlignTop)
        else:
            fallback = QLabel("🥗")
            fallback.setStyleSheet("font-size: 36px;")
            header_row.addWidget(fallback, alignment=Qt.AlignTop)

        titles = QVBoxLayout()
        title = QLabel("Export to Excel")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #1b3d1b;")
        subtitle = QLabel("Sign in with your Yazio account. Nothing is uploaded to the web — the report is built on your PC.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 12px; color: #4a5f4a;")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header_row.addLayout(titles, stretch=1)
        card_layout.addLayout(header_row)

        form = QFormLayout()
        form.setSpacing(12)
        form.setContentsMargins(0, 0, 0, 0)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form.setFormAlignment(Qt.AlignTop)
        form.addRow(self._styled_label("Email"), self.email_input)
        form.addRow(self._styled_label("Password"), self.password_input)
        form.addRow(self._styled_label("Save report to"), self._browse_row(self.output_path_input, self._pick_output))
        card_layout.addLayout(form)
        card_layout.addWidget(self.run_button)
        card_layout.addWidget(self.status_label)

        disclaimer = QLabel("Unofficial helper — not affiliated with Yazio.")
        disclaimer.setStyleSheet("font-size: 10px; color: #7a8f7a;")
        disclaimer.setWordWrap(True)
        card_layout.addWidget(disclaimer)

        root = GradientBackground()
        root_layout = QVBoxLayout(root)
        # Slightly smaller margins and no stretch so there is less empty
        # space under the white card.
        root_layout.setContentsMargins(20, 16, 20, 16)
        root_layout.addWidget(card, alignment=Qt.AlignCenter)

        self.setCentralWidget(root)
        self.setStyleSheet(
            """
            QFrame#card {
                background-color: rgba(255, 255, 255, 0.94);
                border-radius: 18px;
                border: 1px solid rgba(255, 255, 255, 0.9);
            }
            QLineEdit {
                padding: 10px 12px;
                border-radius: 10px;
                border: 1px solid #c5d9c0;
                background: #ffffff;
                color: #1b2e1b;
                font-size: 13px;
                selection-background-color: #7cb342;
                selection-color: #ffffff;
            }
            QLineEdit::placeholder {
                color: #6d806d;
            }
            QLineEdit:focus {
                border: 1px solid #7cb342;
            }
            QPushButton#browseButton {
                color: #1b2e1b;
                background-color: #e3efe0;
                border: 1px solid #7d9a75;
                font-weight: 500;
                min-width: 88px;
            }
            QPushButton#browseButton:hover {
                background-color: #d4e6cf;
                border: 1px solid #5c7a54;
            }
            QPushButton#browseButton:pressed {
                background-color: #c5dac0;
            }
            QPushButton#primaryButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #7cb342, stop:1 #9ccc65);
                color: #ffffff;
                font-weight: 600;
                font-size: 14px;
                padding: 14px 20px;
                border-radius: 12px;
                border: none;
            }
            QPushButton#primaryButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #689f38, stop:1 #8bc34a);
            }
            QPushButton#primaryButton:disabled {
                background: #b0c9a8;
                color: #f5f5f5;
            }
            QPushButton {
                padding: 8px 14px;
                border-radius: 8px;
                border: 1px solid #a5c09a;
                background: rgba(255, 255, 255, 0.85);
                font-size: 12px;
            }
            """
        )

    def _apply_input_row_height(self, widget: QWidget) -> None:
        widget.setFixedHeight(_INPUT_ROW_FIXED_HEIGHT)

    def _styled_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setFixedHeight(_INPUT_ROW_FIXED_HEIGHT)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label.setStyleSheet("font-size: 12px; color: #2e4a2e; font-weight: 500;")
        return label

    def _browse_row(self, line_edit: QLineEdit, callback) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.addWidget(line_edit)
        button = QPushButton("Browse…")
        button.setObjectName("browseButton")
        button.setFixedHeight(_INPUT_ROW_FIXED_HEIGHT)
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(callback)
        row.addWidget(button)
        return container

    def _load_saved_settings(self) -> None:
        s = self._settings
        out = s.value("output_path")
        if out:
            self.output_path_input.setText(str(out))

    def _pick_output(self) -> None:
        selected, _ = QFileDialog.getSaveFileName(
            self,
            "Save Excel report as",
            self.output_path_input.text() or str(Path.home() / "Documents" / "Yazio_nutrition_report.xlsx"),
            "Excel Workbook (*.xlsx)",
        )
        if selected:
            if not selected.lower().endswith(".xlsx"):
                selected += ".xlsx"
            self.output_path_input.setText(selected)

    def _append_log(self, message: str) -> None:
        self.status_label.setText(message)

    def _start_export(self) -> None:
        output_text = self.output_path_input.text().strip()
        exporter_path = suggested_exporter_exe()
        if exporter_path is None:
            QMessageBox.information(
                self,
                "YazioExport.exe not found",
                "Place YazioExport.exe next to this app or under:\n"
                "  helper\\YazioExport.exe\n\n"
                "Build or download it from the Yazio Exporter project, then try again.",
            )
            return

        today = date.today()
        date_from = f"2012-01-01"
        date_to = today.isoformat()
        settings = ExportSettings(
            exporter_exe=exporter_path,
            email=self.email_input.text().strip(),
            password=self.password_input.text(),
            date_from=date_from,
            date_to=date_to,
            output_xlsx=Path(output_text),
        )
        if not settings.email or not settings.password:
            QMessageBox.warning(self, "Missing login", "Please enter your email and password.")
            return
        if not output_text:
            QMessageBox.warning(self, "Where to save?", "Choose where to save the Excel file.")
            return

        self._settings.setValue("output_path", output_text)

        self.run_button.setEnabled(False)
        self._append_log("Starting…")

        self.worker = ExportWorker(settings=settings, service=self.service)
        self.worker.log_signal.connect(self._append_log)
        self.worker.done_signal.connect(self._on_done)
        self.worker.error_signal.connect(self._on_error)
        self.worker.finished.connect(lambda: self.run_button.setEnabled(True))
        self.worker.start()

    def _on_done(self, output_path: str) -> None:
        self._append_log("Done.")
        QMessageBox.information(
            self,
            "Report ready",
            f"Your Excel file was saved here:\n{output_path}",
        )

    def _on_error(self, error: str) -> None:
        self._append_log("Something went wrong.")
        QMessageBox.critical(self, "Export failed", error)
