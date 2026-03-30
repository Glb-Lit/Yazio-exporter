from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExportSettings:
    exporter_exe: Path
    email: str
    password: str
    date_from: str
    date_to: str
    output_xlsx: Path
