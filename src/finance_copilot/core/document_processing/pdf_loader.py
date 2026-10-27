"""文本型 PDF 的轻量解析入口；扫描件 OCR 明确不在本轮范围。"""

from pathlib import Path

from finance_copilot.core.document_processing.file_validator import validate_file
from finance_copilot.core.exceptions import DocumentProcessingError


def load_pdf_text(path: str | Path) -> str:
    file_path = validate_file(path, allowed_suffixes={".pdf"})
    try:
        import fitz  # type: ignore[import-not-found]
    except ImportError as exc:
        raise DocumentProcessingError(
            "当前环境未安装 PyMuPDF；PDF 文本解析为可替换占位能力。"
        ) from exc

    try:
        with fitz.open(file_path) as document:
            text = "\n".join(page.get_text() for page in document).strip()
    except Exception as exc:
        raise DocumentProcessingError(f"PDF 解析失败：{file_path.name}") from exc
    if not text:
        raise DocumentProcessingError("PDF 未提取到文本；扫描件 OCR 未实现。")
    return text

