from pathlib import Path
from typing import Protocol


class OCRPort(Protocol):
    def extract_text(self, path: Path) -> str: ...

