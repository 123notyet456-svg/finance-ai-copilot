from pathlib import Path

from finance_copilot.core.document_processing.file_validator import validate_file


def load_markdown(path: str | Path, encoding: str = "utf-8") -> str:
    file_path = validate_file(path, allowed_suffixes={".md", ".markdown"})
    return file_path.read_text(encoding=encoding)

