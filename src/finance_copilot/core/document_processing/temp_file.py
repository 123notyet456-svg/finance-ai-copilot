from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator


@contextmanager
def temporary_file_path(filename: str) -> Iterator[Path]:
    safe_name = Path(filename).name
    if not safe_name:
        raise ValueError("filename 不能为空")
    with TemporaryDirectory(prefix="finance-copilot-") as directory:
        yield Path(directory) / safe_name

