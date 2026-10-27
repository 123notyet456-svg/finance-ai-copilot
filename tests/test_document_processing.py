from pathlib import Path

import pytest

from finance_copilot.core.document_processing import load_markdown, load_text, sha256_file
from finance_copilot.core.document_processing.file_validator import validate_file
from finance_copilot.core.document_processing.temp_file import temporary_file_path
from finance_copilot.core.exceptions import FileValidationError


def test_text_markdown_hash_and_temp_path(tmp_path: Path) -> None:
    text_path = tmp_path / "sample.txt"
    text_path.write_text("合成样本", encoding="utf-8")
    markdown_path = tmp_path / "sample.md"
    markdown_path.write_text("# 合成样本", encoding="utf-8")

    assert load_text(text_path) == "合成样本"
    assert load_markdown(markdown_path).startswith("#")
    assert len(sha256_file(text_path)) == 64
    assert validate_file(text_path) == text_path

    with temporary_file_path("safe.txt") as temp_path:
        assert temp_path.name == "safe.txt"
        assert temp_path.parent.exists()
    assert not temp_path.parent.exists()


def test_file_validator_rejects_unsupported_file(tmp_path: Path) -> None:
    path = tmp_path / "sample.exe"
    path.write_bytes(b"not executable")
    with pytest.raises(FileValidationError):
        validate_file(path)

