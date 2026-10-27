from pathlib import Path
from typing import Collection

from finance_copilot.core.exceptions import FileValidationError


DEFAULT_ALLOWED_SUFFIXES = frozenset({".txt", ".md", ".markdown", ".pdf", ".docx"})


def validate_file(
    path: str | Path,
    *,
    allowed_suffixes: Collection[str] = DEFAULT_ALLOWED_SUFFIXES,
    max_size_bytes: int = 10 * 1024 * 1024,
) -> Path:
    file_path = Path(path)
    if not file_path.is_file():
        raise FileValidationError(f"文件不存在或不是普通文件：{file_path}")
    allowed = {suffix.lower() for suffix in allowed_suffixes}
    if file_path.suffix.lower() not in allowed:
        raise FileValidationError(f"不支持的文件类型：{file_path.suffix}")
    size = file_path.stat().st_size
    if size == 0:
        raise FileValidationError("文件不能为空")
    if size > max_size_bytes:
        raise FileValidationError(f"文件超过大小限制：{size} > {max_size_bytes}")
    return file_path
